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

import hashlib
import json
import os
from datetime import UTC, datetime
from typing import Literal

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

mcp = FastMCP("WellnessCompanionServer")

DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "mock_secure_db.json")
)

ALLOWED_MED_STATUS = {"taken", "missed", "pending"}
ALLOWED_METRIC_KEYS = {"mood_score", "medication_compliance", "medication_updates"}


class TelemetryRejected(ValueError):
    """Raised when a metrics payload contains anything beyond enum/numeric fields."""


class WellnessMetrics(BaseModel):
    """Structured metrics schema for MCP tool calls and deterministic graph writes."""

    mood_score: int = Field(ge=1, le=10)
    medication_compliance: bool
    medication_updates: dict[str, Literal["taken", "missed", "pending"]] = Field(
        default_factory=dict
    )


def subject_hash(patient_id: str) -> str:
    return hashlib.sha256(patient_id.encode()).hexdigest()[:12]


def validate_metrics(metrics: dict) -> dict:
    if not isinstance(metrics, dict):
        raise TelemetryRejected("metrics must be a dict")

    extra_keys = set(metrics) - ALLOWED_METRIC_KEYS
    if extra_keys:
        raise TelemetryRejected(f"unexpected fields not allowed in telemetry: {sorted(extra_keys)}")

    mood = metrics.get("mood_score", 5)
    if not isinstance(mood, int) or isinstance(mood, bool) or not (1 <= mood <= 10):
        raise TelemetryRejected(f"mood_score must be an int 1-10, got {mood!r}")

    compliance = metrics.get("medication_compliance", True)
    if not isinstance(compliance, bool):
        raise TelemetryRejected(f"medication_compliance must be a bool, got {compliance!r}")

    updates = metrics.get("medication_updates") or {}
    if not isinstance(updates, dict):
        raise TelemetryRejected("medication_updates must be a dict")
    clean_updates = {}
    for med_id, status in updates.items():
        if not isinstance(med_id, str) or not isinstance(status, str):
            raise TelemetryRejected("medication_updates keys/values must be strings")
        if status not in ALLOWED_MED_STATUS:
            raise TelemetryRejected(
                f"medication_updates status must be one of {sorted(ALLOWED_MED_STATUS)}, got {status!r}"
            )
        clean_updates[med_id.lower().strip()] = status

    return {
        "mood_score": mood,
        "medication_compliance": compliance,
        "medication_updates": clean_updates,
    }


def load_db() -> dict:
    if os.path.exists(DB_PATH):
        try:
            with open(DB_PATH) as f:
                return json.load(f)
        except Exception:
            pass
    return {"patients": {}}


def save_db(data: dict) -> None:
    with open(DB_PATH, "w") as f:
        json.dump(data, f, indent=2)


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def apply_wellness_metrics(patient_id: str, metrics: dict) -> str:
    """Deterministic write path shared by MCP tool and graph persist node."""
    db = load_db()
    patient_id = patient_id.lower().strip()
    patients = db.get("patients", {})
    if patient_id not in patients:
        return f"Error: Patient ID '{patient_id}' not found in database."

    try:
        clean = validate_metrics(metrics)
    except TelemetryRejected as exc:
        return f"Error: telemetry rejected ({exc}). Only enum/numeric fields may reach the metrics sink."

    mood = clean["mood_score"]
    compliance = clean["medication_compliance"]
    medication_updates = clean["medication_updates"]
    patient = patients[patient_id]

    incoming_entry = {
        "mood_score": mood,
        "medication_compliance": compliance,
        "medication_updates": medication_updates,
    }
    if patient.get("_last_logged_metrics") == incoming_entry:
        return f"Skipped duplicate telemetry write for {patient.get('name')} (idempotent no-op)."
    patient["_last_logged_metrics"] = incoming_entry

    telemetry = db.setdefault("telemetry", {})
    subject = telemetry.setdefault(
        subject_hash(patient_id), {"mood_history": [], "compliance_history": []}
    )
    subject["mood_history"].append(mood)
    subject["compliance_history"].append(compliance)

    if "mood_history" not in patient:
        patient["mood_history"] = []
    patient["mood_history"].append(mood)

    if "compliance_history" not in patient:
        patient["compliance_history"] = []
    patient["compliance_history"].append(compliance)

    meds = patient.get("medications", {})
    if medication_updates:
        for med_id, status in medication_updates.items():
            med_id_clean = med_id.lower().strip()
            if med_id_clean in meds:
                meds[med_id_clean]["status"] = status
    elif compliance:
        # Full compliance with no per-med breakdown: mark every scheduled med taken.
        for med_info in meds.values():
            med_info["status"] = "taken"

    updated_labels = [
        f"{meds[med_id.lower().strip()].get('name', med_id)} -> {status}"
        for med_id, status in medication_updates.items()
        if med_id.lower().strip() in meds
    ]
    if not updated_labels and compliance and meds and not medication_updates:
        updated_labels = [
            f"{med_info.get('name', med_id)} -> taken" for med_id, med_info in meds.items()
        ]

    activity_log = patient.setdefault("activity_log", [])
    activity_log.insert(
        0,
        {
            "created_at": utc_now(),
            "kind": "update",
            "summary": (
                f"Logged mood {mood}/10; medication compliance "
                f"{'confirmed' if compliance else 'needs review'}."
            ),
            "detail": "; ".join(updated_labels) if updated_labels else "No per-medication status changes.",
        },
    )
    del activity_log[50:]

    save_db(db)
    return (
        f"Logged anonymized metrics for {patient.get('name')}: mood={mood}/10, "
        f"compliance={'confirmed' if compliance else 'needs review'}, "
        f"medication_updates={'; '.join(updated_labels)}"
    )


@mcp.tool()
def get_medication_schedule(patient_id: str) -> str:
    """Pull the daily medication schedule for the elderly patient.

    Args:
        patient_id: The ID of the patient (e.g., 'arthur', 'beatrice', 'charles').
    """
    db = load_db()
    patient_id = patient_id.lower().strip()
    patients = db.get("patients", {})
    if patient_id not in patients:
        return f"Error: Patient ID '{patient_id}' not found in database."

    patient = patients[patient_id]
    meds = patient.get("medications", {})

    schedule_lines = [f"Daily Medication Schedule for {patient.get('name')}:"]
    for med_id, med_info in meds.items():
        schedule_lines.append(
            f"- id={med_id} | {med_info.get('time')}: {med_info.get('name')} "
            f"(status: {med_info.get('status', 'pending')})"
        )
    schedule_lines.extend(
        [
            "Use the exact id= values as keys in medication_updates.",
            "Interpret the patient's words freely (nicknames, partial names, 'my morning pill') "
            "but always map them to those ids in your structured output.",
            "If the patient mentions taking or missing specific medications, medication_updates "
            "must include every affected id — never describe changes only in companion_response.",
        ]
    )

    return "\n".join(schedule_lines)


@mcp.tool()
def log_wellness_metrics(patient_id: str, metrics: WellnessMetrics) -> str:
    """Log anonymized wellness metrics to the secure local database file for a specific patient.

    Args:
        patient_id: The ID of the patient.
        metrics: Structured metrics. Must NOT contain PII or chat text.
    """
    return apply_wellness_metrics(patient_id, metrics.model_dump())


if __name__ == "__main__":
    mcp.run()
