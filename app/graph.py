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

from .tools import anonymizer_toolset, companion_toolset


# --- Graph State Schema ---
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


# --- Node Output Schemas ---
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
    """Output schema for AnonymizerNode confirming telemetry fields."""

    mood_score: int = Field(description="Anonymized mood score of the patient.")
    medication_compliance: bool = Field(
        description="Anonymized medication compliance flag."
    )
    medication_updates: dict[str, str] = Field(
        description="Anonymized medication updates mapping.",
        default_factory=dict
    )


# --- Node Logic ---


@node
def log_input_node(ctx: Context, node_input: types.Content) -> Event:
    """Pre-processing node: logs the user prompt to conversational history state."""
    patient_id = ctx.session.user_id if (ctx.session and ctx.session.user_id) else "arthur"
    
    # Extract text content from standard GenAI Content type
    user_text = ""
    if node_input and node_input.parts:
        parts_text = [p.text for p in node_input.parts if p.text]
        user_text = " ".join(parts_text)

    history = ctx.state.get("conversational_history", [])
    
    # Prepend system profile message on the first turn
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
        history.append(f"System: You are conversing with patient {patient_name} (ID: {patient_id}). Always call get_medication_schedule with patient_id='{patient_id}' and log_wellness_metrics with patient_id='{patient_id}'.")

    history.append(f"User: {user_text}")

    # State Transition: Save user message in conversational_history and set patient_id
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
5. Populate the `medication_updates` dictionary with updates for any medications discussed (keys are medication IDs like 'cardiovascular', 'multivitamin', etc.).
6. Output the structured companion response, overall compliance, mood score, and medication updates.

Security constraint: You have NO access to database logging tools. You must rely on the next node for telemetry logging.
""",
    tools=[companion_toolset],
    output_schema=CompanionOutput,
    output_key="companion_data",
)

anonymizer_node = LlmAgent(
    name="AnonymizerNode",
    model=Gemini(
        model="gemini-3.5-flash",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction="""You are a telemetry anonymization agent.
You will receive the structured wellness data from the CompanionNode.
Your tasks:
1. Parse the mood score, overall medication compliance, and medication updates fields.
2. Completely strip out any PII, text chat logs, or conversational content.
3. Call the `log_wellness_metrics` tool to store the anonymized metrics. You MUST retrieve the patient_id from the state/history and pass it: log_wellness_metrics(patient_id=patient_id, metrics={"mood_score": mood_score, "medication_compliance": compliance, "medication_updates": medication_updates}).
4. Output the structured anonymized metrics.
""",
    tools=[anonymizer_toolset],
    output_schema=AnonymizedMetrics,
    output_key="anonymized_data",
)


@node
def escalation_node(ctx: Context, node_input: AnonymizedMetrics) -> Event:
    """Evaluates system state and performs conditional routing to trigger alerts if needed.

    State Transitions:
    - If medication compliance is true, consecutive_missed_cycles is reset to 0.
    - If medication compliance is false, consecutive_missed_cycles is incremented by 1.
    - If consecutive_missed_cycles >= 2 or mood score < 3, escalation_triggered is set to True.
    - conversational_history is updated to append the companion's response.
    """
    companion_data = ctx.state.get("companion_data", {})
    companion_resp = companion_data.get("companion_response", "All checked in!")

    # Update conversational history
    history = ctx.state.get("conversational_history", [])
    history.append(f"Companion: {companion_resp}")

    # Calculate consecutive missed cycles
    compliance = node_input.medication_compliance
    current_missed = ctx.state.get("consecutive_missed_cycles", 0)
    new_missed = 0 if compliance else current_missed + 1

    mood = node_input.mood_score

    # Trigger criteria: compliance missed 2+ times OR mood score below 3 (out of 10)
    escalate = (new_missed >= 2) or (mood < 3)

    state_delta = {
        "conversational_history": history,
        "current_mood_score": mood,
        "medication_compliance_flag": compliance,
        "consecutive_missed_cycles": new_missed,
        "escalation_triggered": escalate,
    }

    if escalate:
        # Route to alert node
        return Event(
            output="CRITICAL ALERT: Wellness companion has triggered an escalation. Please check on the patient immediately.",
            actions=EventActions(
                route="escalate",
                state_delta=state_delta,
            ),
        )
    else:
        # Route to normal end
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


# --- Graph Workflow Assembly ---
wellness_graph = Workflow(
    name="wellness_companion_workflow",
    state_schema=WellnessState,
    edges=[
        Edge(from_node=START, to_node=log_input_node),
        Edge(from_node=log_input_node, to_node=companion_node),
        Edge(from_node=companion_node, to_node=anonymizer_node),
        Edge(from_node=anonymizer_node, to_node=escalation_node),
        # Conditional edges for state-driven routing
        Edge(from_node=escalation_node, to_node=alert_node, route="escalate"),
        Edge(from_node=escalation_node, to_node=normal_end_node, route="normal"),
    ],
)
