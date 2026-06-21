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

from google.adk.agents import LlmAgent
from google.adk.agents.context import Context
from google.adk.events.event import Event, EventActions
from google.adk.models import Gemini
from google.adk.workflow import START, Edge, Workflow, node
from google.genai import types
from pydantic import BaseModel, Field

from .mcp_server import apply_wellness_metrics
from .tools import companion_toolset


class WellnessState(BaseModel):
    """Central state tracking variables for the wellness companion."""

    patient_id: str = "arthur"
    conversational_history: list[str] = Field(default_factory=list)
    current_mood_score: int = 5
    medication_compliance_flag: bool = True
    consecutive_missed_cycles: int = 0
    escalation_triggered: bool = False
    companion_data: dict = Field(default_factory=dict)
    anonymized_data: dict = Field(default_factory=dict)


class CompanionOutput(BaseModel):
    """Output schema for CompanionNode containing LLM evaluation."""

    companion_response: str = Field(
        description="The empathetic verbal response or check-in prompt for the patient."
    )
    medication_compliance: bool = Field(
        description="Calculated overall medication compliance from the patient check-in."
    )
    mood_score: int = Field(
        description="Patient mood score on a scale of 1 (depressed) to 10 (happy)."
    )
    medication_updates: dict[str, str] = Field(
        description="Updates for the statuses of the patient's individual medications based on the conversation. Keys must be medication IDs like 'cardiovascular', 'multivitamin', 'sleep_aid', 'insulin', 'blood_pressure', 'digestive_enzyme', or 'vitamin_d'. Values must be 'taken', 'missed', or 'pending'. If a medication was not mentioned, do not include it or set it to 'pending'.",
        default_factory=dict
    )


class AnonymizedMetrics(BaseModel):
    """Structured telemetry fields passed to escalation after allowlist persistence."""

    mood_score: int = Field(description="Anonymized mood score of the patient.")
    medication_compliance: bool = Field(
        description="Anonymized medication compliance flag."
    )
    medication_updates: dict[str, str] = Field(
        description="Anonymized medication updates mapping.",
        default_factory=dict
    )


@node
def log_input_node(ctx: Context, node_input: types.Content) -> Event:
    """Pre-processing node: logs the user prompt to conversational history state."""
    patient_id = ctx.session.user_id if (ctx.session and ctx.session.user_id) else "arthur"

    user_text = ""
    if node_input and node_input.parts:
        parts_text = [p.text for p in node_input.parts if p.text]
        user_text = " ".join(parts_text)

    history = ctx.state.get("conversational_history", [])

    if not history:
        import json
        import os
        db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "mock_secure_db.json"))
        patient_name = "Arthur Pendelton"
        if os.path.exists(db_path):
            try:
                with open(db_path) as f:
                    db = json.load(f)
                    patient_name = db.get("patients", {}).get(patient_id, {}).get("name", "Arthur Pendelton")
            except Exception:
                pass
        history.append(
            f"System: You are conversing with patient {patient_name} (ID: {patient_id}). "
            f"Always call get_medication_schedule with patient_id='{patient_id}'."
        )

    history.append(f"User: {user_text}")

    return Event(
        output=user_text,
        actions=EventActions(
            state_delta={
                "conversational_history": history,
                "patient_id": patient_id
            },
        ),
    )


companion_node = LlmAgent(
    name="CompanionNode",
    model=Gemini(
        model="gemini-3.5-flash",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction="""You are an empathetic, ambient, privacy-first wellness companion for elderly care.
Your primary tasks:
1. Converse empathetically with the patient.
2. Read the patient_id from the conversation history/state (e.g. 'arthur', 'beatrice', or 'charles').
3. Call the `get_medication_schedule` tool with that patient_id to retrieve the active medication routine.
4. Determine overall medication compliance, mood score, and individual medication status updates ('taken', 'missed', or 'pending') based on the patient's check-in.
5. Populate `medication_updates` with the status of each medication the patient mentioned. Keys must be medication IDs from the schedule (e.g. `digestive_enzyme`, `vitamin_d`, `insulin`). Values must be `taken`, `missed`, or `pending`. When the patient confirms all medications were taken, list every scheduled med ID as `taken`. When only some were taken or missed, include only those discussed — do not mark unmentioned meds from overall compliance alone.
6. Output the structured companion response, overall compliance, mood score, and medication updates.

Security constraint: You have NO access to database logging tools. Telemetry is persisted by a separate deterministic privacy guard node.
""",
    tools=[companion_toolset],
    output_schema=CompanionOutput,
    output_key="companion_data",
)


@node
def persist_metrics_node(ctx: Context, node_input: CompanionOutput) -> Event:
    """Deterministic privacy guard: allowlist-validated metrics write to patient JSON."""
    patient_id = ctx.state.get("patient_id", "arthur")
    metrics = {
        "mood_score": node_input.mood_score,
        "medication_compliance": node_input.medication_compliance,
        "medication_updates": dict(node_input.medication_updates or {}),
    }
    result_msg = apply_wellness_metrics(patient_id, metrics)
    anonymized = AnonymizedMetrics(**metrics)
    return Event(
        output=anonymized,
        actions=EventActions(state_delta={"anonymized_data": metrics}),
    )


@node
def escalation_node(ctx: Context, node_input: AnonymizedMetrics) -> Event:
    """Evaluates system state and performs conditional routing to trigger alerts if needed."""
    companion_data = ctx.state.get("companion_data", {})
    companion_resp = companion_data.get("companion_response", "All checked in!")

    history = ctx.state.get("conversational_history", [])
    history.append(f"Companion: {companion_resp}")

    compliance = node_input.medication_compliance
    current_missed = ctx.state.get("consecutive_missed_cycles", 0)
    new_missed = 0 if compliance else current_missed + 1

    mood = node_input.mood_score
    patient_id = ctx.state.get("patient_id", "unknown")
    medication_updates = node_input.medication_updates or {}

    escalate = (new_missed >= 2) or (mood < 3)
    alert_reasons = []
    if new_missed >= 2:
        alert_reasons.append(f"{new_missed} consecutive medication non-compliance cycles")
    if mood < 3:
        alert_reasons.append(f"critical mood score {mood}/10")

    state_delta = {
        "conversational_history": history,
        "current_mood_score": mood,
        "medication_compliance_flag": compliance,
        "consecutive_missed_cycles": new_missed,
        "escalation_triggered": escalate,
    }

    if escalate:
        updates_text = (
            ", ".join(f"{med_id}: {status}" for med_id, status in medication_updates.items())
            if medication_updates
            else "no individual medication updates supplied"
        )
        return Event(
            output=(
                "CRITICAL ALERT: Wellness companion triggered escalation for "
                f"patient_id={patient_id}. Reason: {'; '.join(alert_reasons)}. "
                f"Latest compliance={'confirmed' if compliance else 'needs review'}; "
                f"medication updates: {updates_text}. Please check on the patient immediately."
            ),
            actions=EventActions(
                route="escalate",
                state_delta=state_delta,
            ),
        )

    return Event(
        output=companion_resp,
        actions=EventActions(
            route="normal",
            state_delta=state_delta,
        ),
    )


@node
def alert_node(node_input: str) -> str:
    """Leaf node for critical escalation alert output."""
    return f"🚨 [ALERT] {node_input}"


@node
def normal_end_node(node_input: str) -> str:
    """Leaf node for normal companion conversation output."""
    return node_input


wellness_graph = Workflow(
    name="wellness_companion_workflow",
    state_schema=WellnessState,
    edges=[
        Edge(from_node=START, to_node=log_input_node),
        Edge(from_node=log_input_node, to_node=companion_node),
        Edge(from_node=companion_node, to_node=persist_metrics_node),
        Edge(from_node=persist_metrics_node, to_node=escalation_node),
        Edge(from_node=escalation_node, to_node=alert_node, route="escalate"),
        Edge(from_node=escalation_node, to_node=normal_end_node, route="normal"),
    ],
)
