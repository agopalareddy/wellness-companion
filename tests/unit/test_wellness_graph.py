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

from app.graph import AnonymizedMetrics, escalation_node


class MockContext:
    """Mock context to simulate the state of the graph runner during node execution."""

    def __init__(self, state_dict):
        self.state = state_dict


def test_escalation_node_normal() -> None:
    # Set up normal state: no missed cycles
    state = {
        "consecutive_missed_cycles": 0,
        "conversational_history": [],
        "companion_data": {"companion_response": "Hello, how are you?"},
    }
    ctx = MockContext(state)

    # Input: mood score 8 (fine), compliance True
    metrics = AnonymizedMetrics(mood_score=8, medication_compliance=True)

    # Call the underlying function of the FunctionNode using _func
    event = escalation_node._func(ctx, metrics)

    # Asserts that routing is set to normal, counters stay at 0, and no escalation triggers
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
    # Set up state: 1 missed cycle already recorded
    state = {
        "consecutive_missed_cycles": 1,
        "conversational_history": [],
        "companion_data": {"companion_response": "Please take your pills."},
    }
    ctx = MockContext(state)

    # Input: mood score 7, compliance False (which will make 2 consecutive missed cycles)
    metrics = AnonymizedMetrics(mood_score=7, medication_compliance=False)

    # Call the underlying function of the FunctionNode using _func
    event = escalation_node._func(ctx, metrics)

    # Asserts that consecutive missed cycles increments to 2 and triggers an alert
    assert event.actions.route == "escalate"
    assert event.actions.state_delta["consecutive_missed_cycles"] == 2
    assert event.actions.state_delta["escalation_triggered"] is True
    assert "CRITICAL ALERT" in event.output


def test_escalation_node_low_mood() -> None:
    # Set up state: no missed cycles
    state = {
        "consecutive_missed_cycles": 0,
        "conversational_history": [],
        "companion_data": {"companion_response": "I'm sorry to hear that."},
    }
    ctx = MockContext(state)

    # Input: mood score 2 (under critical threshold < 3), compliance True
    metrics = AnonymizedMetrics(mood_score=2, medication_compliance=True)

    # Call the underlying function of the FunctionNode using _func
    event = escalation_node._func(ctx, metrics)

    # Asserts that low mood triggers an immediate escalation
    assert event.actions.route == "escalate"
    assert event.actions.state_delta["escalation_triggered"] is True
    assert event.actions.state_delta["current_mood_score"] == 2
    assert "CRITICAL ALERT" in event.output
