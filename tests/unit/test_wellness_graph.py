# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import os
import tempfile

from app.graph import (
    AnonymizedMetrics,
    CompanionOutput,
    escalation_node,
    persist_metrics_node,
)
from app.mcp_server import (
    TelemetryRejected,
    apply_wellness_metrics,
    subject_hash,
    validate_metrics,
)


class MockContext:
    """Mock context to simulate the state of the graph runner during node execution."""

    def __init__(self, state_dict):
        self.state = state_dict


def test_escalation_node_normal() -> None:
    state = {
        "consecutive_missed_cycles": 0,
        "conversational_history": [],
        "companion_data": {"companion_response": "Hello, how are you?"},
    }
    ctx = MockContext(state)
    metrics = AnonymizedMetrics(mood_score=8, medication_compliance=True)
    event = escalation_node._func(ctx, metrics)

    assert event.actions.route == "normal"
    assert event.actions.state_delta["consecutive_missed_cycles"] == 0
    assert event.actions.state_delta["current_mood_score"] == 8
    assert event.actions.state_delta["medication_compliance_flag"] is True
    assert event.actions.state_delta["escalation_triggered"] is False
    assert (
        "Companion: Hello, how are you?"
        in event.actions.state_delta["conversational_history"]
    )


def test_escalation_node_missed_medication() -> None:
    state = {
        "consecutive_missed_cycles": 1,
        "conversational_history": [],
        "companion_data": {"companion_response": "Please take your pills."},
    }
    ctx = MockContext(state)
    metrics = AnonymizedMetrics(mood_score=7, medication_compliance=False)
    event = escalation_node._func(ctx, metrics)

    assert event.actions.route == "escalate"
    assert event.actions.state_delta["consecutive_missed_cycles"] == 2
    assert event.actions.state_delta["escalation_triggered"] is True
    assert "CRITICAL ALERT" in event.output


def test_escalation_node_low_mood() -> None:
    state = {
        "consecutive_missed_cycles": 0,
        "conversational_history": [],
        "companion_data": {"companion_response": "I'm sorry to hear that."},
    }
    ctx = MockContext(state)
    metrics = AnonymizedMetrics(mood_score=2, medication_compliance=True)
    event = escalation_node._func(ctx, metrics)

    assert event.actions.route == "escalate"
    assert event.actions.state_delta["escalation_triggered"] is True
    assert event.actions.state_delta["current_mood_score"] == 2
    assert "CRITICAL ALERT" in event.output


def test_validate_metrics_accepts_clean_payload() -> None:
    clean = validate_metrics(
        {
            "mood_score": 7,
            "medication_compliance": False,
            "medication_updates": {"Cardiovascular": "missed"},
        }
    )
    assert clean == {
        "mood_score": 7,
        "medication_compliance": False,
        "medication_updates": {"cardiovascular": "missed"},
    }


def test_validate_metrics_rejects_pii_field() -> None:
    try:
        validate_metrics(
            {
                "mood_score": 5,
                "medication_compliance": True,
                "patient_name": "Arthur Pendelton",
            }
        )
        raise AssertionError("expected TelemetryRejected")
    except TelemetryRejected:
        pass


def test_validate_metrics_rejects_free_text_med_status() -> None:
    try:
        validate_metrics(
            {
                "mood_score": 5,
                "medication_compliance": True,
                "medication_updates": {"cardiovascular": "patient said he felt fine"},
            }
        )
        raise AssertionError("expected TelemetryRejected")
    except TelemetryRejected:
        pass


def test_subject_hash_is_stable_and_not_reversible_lookalike() -> None:
    h1 = subject_hash("arthur")
    h2 = subject_hash("arthur")
    h3 = subject_hash("beatrice")
    assert h1 == h2
    assert h1 != h3
    assert "arthur" not in h1


def test_persist_metrics_node_writes_patient_json(monkeypatch) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = os.path.join(tmpdir, "mock_secure_db.json")
        seed = {
            "patients": {
                "beatrice": {
                    "name": "Beatrice Vance",
                    "medications": {
                        "insulin": {
                            "name": "Insulin injection",
                            "time": "Morning",
                            "status": "pending",
                        }
                    },
                    "mood_history": [7],
                    "compliance_history": [True],
                }
            }
        }
        with open(db_file, "w") as f:
            json.dump(seed, f)

        import app.mcp_server as mcp_server

        monkeypatch.setattr(mcp_server, "DB_PATH", db_file)

        ctx = MockContext({"patient_id": "beatrice"})
        companion = CompanionOutput(
            companion_response="Great job today!",
            medication_compliance=True,
            mood_score=8,
            medication_updates={"insulin": "taken"},
        )
        event = persist_metrics_node._func(ctx, companion)

        assert isinstance(event.output, AnonymizedMetrics)
        assert event.output.mood_score == 8

        with open(db_file) as f:
            db = json.load(f)
        patient = db["patients"]["beatrice"]
        assert patient["mood_history"][-1] == 8
        assert patient["medications"]["insulin"]["status"] == "taken"
        assert any("Logged mood 8/10" in item["summary"] for item in patient["activity_log"])


def test_apply_wellness_metrics_idempotent(monkeypatch) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = os.path.join(tmpdir, "mock_secure_db.json")
        seed = {
            "patients": {
                "arthur": {
                    "name": "Arthur",
                    "medications": {},
                    "mood_history": [],
                    "compliance_history": [],
                }
            }
        }
        with open(db_file, "w") as f:
            json.dump(seed, f)

        import app.mcp_server as mcp_server

        monkeypatch.setattr(mcp_server, "DB_PATH", db_file)

        metrics = {"mood_score": 6, "medication_compliance": True, "medication_updates": {}}
        first = apply_wellness_metrics("arthur", metrics)
        second = apply_wellness_metrics("arthur", metrics)
        assert "Logged anonymized metrics" in first
        assert "Skipped duplicate" in second

        with open(db_file) as f:
            db = json.load(f)
        assert len(db["patients"]["arthur"]["mood_history"]) == 1


def test_apply_wellness_metrics_partial_updates_only(monkeypatch) -> None:
    """Empty or partial medication_updates must not blanket-mark every medication."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = os.path.join(tmpdir, "mock_secure_db.json")
        seed = {
            "patients": {
                "charles": {
                    "name": "Charles Darwin",
                    "medications": {
                        "digestive_enzyme": {
                            "name": "Digestive Enzyme Capsule",
                            "time": "Morning",
                            "status": "pending",
                        },
                        "vitamin_d": {
                            "name": "Vitamin D3 Supplement",
                            "time": "Noon",
                            "status": "pending",
                        },
                    },
                    "mood_history": [],
                    "compliance_history": [],
                }
            }
        }
        with open(db_file, "w") as f:
            json.dump(seed, f)

        import app.mcp_server as mcp_server

        monkeypatch.setattr(mcp_server, "DB_PATH", db_file)

        apply_wellness_metrics(
            "charles",
            {
                "mood_score": 5,
                "medication_compliance": False,
                "medication_updates": {},
            },
        )
        with open(db_file) as f:
            empty_updates_db = json.load(f)
        meds = empty_updates_db["patients"]["charles"]["medications"]
        assert meds["digestive_enzyme"]["status"] == "pending"
        assert meds["vitamin_d"]["status"] == "pending"

        apply_wellness_metrics(
            "charles",
            {
                "mood_score": 7,
                "medication_compliance": True,
                "medication_updates": {},
            },
        )
        with open(db_file) as f:
            full_compliance_db = json.load(f)
        meds = full_compliance_db["patients"]["charles"]["medications"]
        assert meds["digestive_enzyme"]["status"] == "taken"
        assert meds["vitamin_d"]["status"] == "taken"

        apply_wellness_metrics(
            "charles",
            {
                "mood_score": 5,
                "medication_compliance": False,
                "medication_updates": {
                    "digestive_enzyme": "missed",
                    "vitamin_d": "taken",
                },
            },
        )
        with open(db_file) as f:
            partial_db = json.load(f)
        meds = partial_db["patients"]["charles"]["medications"]
        assert meds["digestive_enzyme"]["status"] == "missed"
        assert meds["vitamin_d"]["status"] == "taken"
