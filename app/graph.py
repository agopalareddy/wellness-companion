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

import contextvars
import os
from typing import Literal

import google.auth
from google import genai
from google.adk.agents import LlmAgent
from google.adk.agents.context import Context
from google.adk.events.event import Event, EventActions
from google.adk.models import Gemini
from google.adk.workflow import START, Edge, Workflow, node
from google.genai import types
from pydantic import BaseModel, Field

from .mcp_server import apply_wellness_metrics, load_db

_EXTRACTOR_MODEL = "gemini-2.5-flash"
_EXTRACTOR_INSTRUCTION = """You extract medication compliance from elderly patient check-in messages.

The input contains the patient check-in and medication schedule with id= keys.
Map the patient's natural language to those exact ids (e.g. "enzyme capsule" → digestive_enzyme).

When the patient mentions specific meds, medication_updates MUST list every affected id with taken, missed, or pending.
Never return an empty medication_updates when specific meds were discussed.

Example:
Patient check-in: I missed my enzyme capsule but took my supplement.
→ {"digestive_enzyme": "missed", "vitamin_d": "taken"}, medication_compliance: false
"""


class WellnessState(BaseModel):
    """Central state tracking variables for the wellness companion."""

    patient_id: str = "arthur"
    conversational_history: list[str] = Field(default_factory=list)
    current_mood_score: int = 5
    medication_compliance_flag: bool = True
    consecutive_missed_cycles: int = 0
    escalation_triggered: bool = False
    medication_extraction: dict = Field(default_factory=dict)
    check_in_context: str = ""
    companion_data: dict = Field(default_factory=dict)
    anonymized_data: dict = Field(default_factory=dict)


class MedicationExtraction(BaseModel):
    """Structured medication status extracted from the patient check-in."""

    medication_updates: dict[str, Literal["taken", "missed", "pending"]] = Field(
        description=(
            "Per-medication status mapped from the patient's words to exact schedule ids "
            "(e.g. digestive_enzyme, vitamin_d). Include every med the patient mentioned. "
            "Leave empty only when the patient did not discuss any medication."
        ),
        default_factory=dict,
    )
    medication_compliance: bool = Field(
        description=(
            "False when any scheduled medication was missed; true when all were taken "
            "or the patient did not mention medications."
        )
    )


class CompanionOutput(BaseModel):
    """Output schema for CompanionNode — mood and empathetic reply only."""

    companion_response: str = Field(
        description="The empathetic verbal response or check-in prompt for the patient."
    )
    mood_score: int = Field(
        description="Patient mood score on a scale of 1 (depressed) to 10 (happy)."
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


def _format_check_in_context(patient_id: str, user_text: str) -> str:
    """Build the full check-in payload downstream LLM nodes can read."""
    lines = [f"Patient check-in: {user_text}", "", "Medication schedule (use id= keys in medication_updates):"]
    try:
        patient_record = load_db().get("patients", {}).get(patient_id.lower(), {})
        meds = patient_record.get("medications", {})
        for med_id, med_info in meds.items():
            lines.append(
                f"- id={med_id} | {med_info.get('name')} | {med_info.get('time')} | "
                f"status={med_info.get('status', 'pending')}"
            )
        if not meds:
            lines.append("- (no medications on file)")
    except Exception:
        lines.append("- (schedule unavailable)")
    return "\n".join(lines)


# ponytail: contextvar lets middleware inject per-request API key w/o env var races.
_user_api_key: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "user_api_key", default=None
)

_MOCK_LLM = os.getenv("MOCK_LLM", "").lower() == "true"


class UserKeyGemini(Gemini):
    """Gemini model that reads API key from request-scoped contextvar.

    When a user provides their own AI Studio key via the UI, it flows through
    X-Google-API-Key header → middleware → _user_api_key contextvar → here.
    Falls back to parent behavior (ADC/Vertex AI) when no user key is set.
    """

    @property  # NOT cached_property — must re-read contextvar for each request
    def api_client(self) -> genai.Client:  # type: ignore[override]
        key = _user_api_key.get()
        if key:
            base_url, api_version = self._base_url_and_api_version
            http_kwargs = {
                "headers": self._tracking_headers(),
                "retry_options": self.retry_options,
                "base_url": base_url,
            }
            if api_version:
                http_kwargs["api_version"] = api_version
            return genai.Client(
                api_key=key,
                http_options=types.HttpOptions(**http_kwargs),
            )
        return super().api_client  # parent's cached_property → ADC/Vertex AI


def _genai_client() -> genai.Client:
    key = _user_api_key.get()
    if key:
        return genai.Client(api_key=key)
    _, project_id = google.auth.default()
    return genai.Client(
        vertexai=True,
        project=project_id,
        location=os.environ.get("GOOGLE_CLOUD_LOCATION", "global"),
    )


def _extract_medications_with_llm(check_in_context: str) -> MedicationExtraction:
    """LLM extraction via response_schema (gemini-3.5-flash omits dict fields too often)."""
    if _MOCK_LLM:
        return MedicationExtraction(
            medication_updates={"vitamin_d": "taken"},
            medication_compliance=True,
        )
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=MedicationExtraction,
        temperature=0,
        system_instruction=_EXTRACTOR_INSTRUCTION,
    )
    client = _genai_client()
    extraction = MedicationExtraction(medication_compliance=True)
    for attempt in range(2):
        suffix = ""
        if attempt:
            suffix = (
                "\n\nYour prior response omitted medication_updates. "
                "Return every affected schedule id with taken or missed."
            )
        response = client.models.generate_content(
            model=_EXTRACTOR_MODEL,
            contents=check_in_context + suffix,
            config=config,
        )
        extraction = MedicationExtraction.model_validate_json(response.text or "{}")
        if extraction.medication_updates:
            return extraction
        if extraction.medication_compliance:
            return extraction
    return extraction


@node
def extract_medications_node(ctx: Context, node_input: str) -> Event:
    """Focused LLM call: map patient wording to schedule ids."""
    check_in_context = (node_input or "").strip() or ctx.state.get("check_in_context", "")
    extraction = _extract_medications_with_llm(check_in_context)
    payload = extraction.model_dump()
    return Event(
        output=extraction,
        actions=EventActions(state_delta={"medication_extraction": payload}),
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
        history.append(
            f"System: You are conversing with patient ID {patient_id}. "
            "Medication schedule lines below use id= keys for structured extraction."
        )

    check_in_context = _format_check_in_context(patient_id, user_text)
    history.append(f"User: {user_text}")

    return Event(
        output=check_in_context,
        actions=EventActions(
            state_delta={
                "conversational_history": history,
                "patient_id": patient_id,
                "check_in_context": check_in_context,
            },
        ),
    )


medication_extractor_node = extract_medications_node


if _MOCK_LLM:
    # ponytail: deterministic mock avoids real LLM calls in tests. Gate real
    # LLM behind REAL_LLM_TEST=true for cost control.
    @node
    def _mock_companion_node(ctx: Context, node_input) -> Event:
        text = "Mock companion response — all vitals stable, mood appears balanced."
        return Event(
            content=types.Content(role="model", parts=[types.Part.from_text(text=text)]),
            output=CompanionOutput(companion_response=text, mood_score=7),
            actions=EventActions(state_delta={
                "companion_data": {"companion_response": text, "mood_score": 7}
            }),
        )
    companion_node = _mock_companion_node
else:
    companion_node = LlmAgent(
        name="CompanionNode",
        model=UserKeyGemini(
            model="gemini-3.5-flash",
            retry_options=types.HttpRetryOptions(attempts=3),
        ),
        instruction="""You are an empathetic, privacy-first wellness companion for elderly care.

Check-in context:
{check_in_context}

Medication extraction (already recorded for the chart):
{medication_extraction}

Write a warm companion_response that acknowledges what the patient said, including specific medications when they discussed them.
Assess mood_score from 1 (very low) to 10 (excellent) based on tone and words.

Security: You have NO database logging tools. Telemetry is persisted by a separate node.
""",
        output_schema=CompanionOutput,
        output_key="companion_data",
    )


def _coerce_extraction(raw: object) -> dict:
    if hasattr(raw, "model_dump"):
        return raw.model_dump()
    if isinstance(raw, dict):
        return raw
    return {}


@node
def persist_metrics_node(ctx: Context, node_input: CompanionOutput) -> Event:
    """Deterministic privacy guard: allowlist-validated metrics write to patient JSON."""
    patient_id = ctx.state.get("patient_id", "arthur")
    extraction = _coerce_extraction(ctx.state.get("medication_extraction"))
    medication_updates = dict(extraction.get("medication_updates") or {})
    medication_compliance = extraction.get("medication_compliance", True)

    metrics = {
        "mood_score": node_input.mood_score,
        "medication_compliance": medication_compliance,
        "medication_updates": medication_updates,
    }
    apply_wellness_metrics(patient_id, metrics)
    anonymized = AnonymizedMetrics(**metrics)
    companion_data = {
        **node_input.model_dump(),
        "medication_compliance": medication_compliance,
        "medication_updates": medication_updates,
    }
    return Event(
        output=anonymized,
        actions=EventActions(
            state_delta={
                "anonymized_data": metrics,
                "companion_data": companion_data,
            }
        ),
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
        Edge(from_node=log_input_node, to_node=medication_extractor_node),
        Edge(from_node=medication_extractor_node, to_node=companion_node),
        Edge(from_node=companion_node, to_node=persist_metrics_node),
        Edge(from_node=persist_metrics_node, to_node=escalation_node),
        Edge(from_node=escalation_node, to_node=alert_node, route="escalate"),
        Edge(from_node=escalation_node, to_node=normal_end_node, route="normal"),
    ],
)
