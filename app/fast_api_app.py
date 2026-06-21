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
import os
import re
from datetime import UTC, datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

import google.auth
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from google.adk.cli.fast_api import get_fast_api_app
from google.cloud import logging as google_cloud_logging
from pydantic import BaseModel, Field

from app.app_utils.telemetry import setup_telemetry
from app.app_utils.typing import Feedback
from app.aura_ui import AURA_ABOUT_HTML, AURA_INDEX_HTML, AURA_PROVIDER_HTML

setup_telemetry()

PROVIDER_PASSCODE = os.getenv("PROVIDER_PASSCODE", "")
EXPOSE_DEMO_PASSCODES = os.getenv("EXPOSE_DEMO_PASSCODES", "false").lower() == "true"

if os.getenv("INTEGRATION_TEST") == "TRUE":
    import logging as python_logging
    logger = python_logging.getLogger(__name__)
    VERTEX_OK = False
else:
    try:
        _, project_id = google.auth.default()
        logging_client = google_cloud_logging.Client()
        logger = logging_client.logger(__name__)
        VERTEX_OK = True
    except Exception:
        import logging as python_logging
        logger = python_logging.getLogger(__name__)
        VERTEX_OK = False

allow_origins = (
    os.getenv("ALLOW_ORIGINS", "").split(",") if os.getenv("ALLOW_ORIGINS") else None
)

logs_bucket_name = os.environ.get("LOGS_BUCKET_NAME")

AGENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if os.getenv("INTEGRATION_TEST") == "TRUE":
    session_service_uri = None
else:
    _sessions_dir = os.path.join(os.path.dirname(__file__), ".adk")
    os.makedirs(_sessions_dir, exist_ok=True)
    session_service_uri = f"sqlite:///{os.path.join(_sessions_dir, 'sessions.db')}"

artifact_service_uri = f"gs://{logs_bucket_name}" if logs_bucket_name else None

otel_to_cloud = False if os.getenv("INTEGRATION_TEST") == "TRUE" else True

app: FastAPI = get_fast_api_app(
    agents_dir=AGENT_DIR,
    web=True,
    artifact_service_uri=artifact_service_uri,
    allow_origins=allow_origins,
    session_service_uri=session_service_uri,
    otel_to_cloud=otel_to_cloud,
)
app.title = "wellness-companion"
app.description = "API for interacting with the Agent wellness-companion"

APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "mock_secure_db.json"
SEED_DB_PATH = APP_DIR / "seed_db.json"
ACTIVITY_PATH = APP_DIR / "aura_activity.json"


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def load_json(path: Path, default: dict) -> dict:
    import json

    if not path.exists():
        return default
    try:
        with path.open() as f:
            return json.load(f)
    except Exception:
        return default


def save_json(path: Path, data: dict) -> None:
    import json

    with path.open("w") as f:
        json.dump(data, f, indent=2)


def load_db() -> dict:
    return load_json(DB_PATH, {"patients": {}})


def save_db(data: dict) -> None:
    save_json(DB_PATH, data)


def resolve_patient_passcode(patient_id: str, stored: str | None = None) -> str | None:
    env_code = os.getenv(f"PASSCODE_{patient_id.upper()}")
    if env_code:
        return env_code
    return stored or None


def apply_passcodes_from_env(db: dict) -> dict:
    for patient_id, pdata in db.get("patients", {}).items():
        code = resolve_patient_passcode(patient_id, pdata.get("passcode"))
        if code:
            pdata["passcode"] = code
        else:
            pdata.pop("passcode", None)
    return db


def slugify_patient_id(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "_", value.lower().strip())
    return cleaned.strip("_") or "patient"


def public_patient(patient_id: str) -> dict:
    patients = load_db().get("patients", {})
    patient_id_clean = patient_id.lower().strip()
    if patient_id_clean not in patients:
        return {"error": f"Patient '{patient_id}' not found"}
    patient = dict(patients[patient_id_clean])
    patient.pop("passcode", None)
    patient.pop("_last_logged_metrics", None)
    patient["patient_id"] = patient_id_clean
    return patient


def load_activity() -> dict:
    return load_json(ACTIVITY_PATH, {"patients": {}})


def append_activity(patient_id: str, kind: str, summary: str, detail: str = "") -> dict:
    patient_id_clean = patient_id.lower().strip()
    activity = load_activity()
    items = activity.setdefault("patients", {}).setdefault(patient_id_clean, [])
    entry = {
        "created_at": utc_now(),
        "kind": kind,
        "summary": summary,
        "detail": detail,
    }
    items.insert(0, entry)
    del items[100:]
    save_json(ACTIVITY_PATH, activity)
    return entry


def consecutive_missed_cycles(compliance_history: list) -> int:
    streak = 0
    for value in reversed(compliance_history):
        if value is False:
            streak += 1
        else:
            break
    return streak


def patient_has_alert(patient_id: str, patient: dict) -> bool:
    moods = patient.get("mood_history") or []
    if moods and moods[-1] < 3:
        return True
    if consecutive_missed_cycles(patient.get("compliance_history") or []) >= 2:
        return True
    items = load_activity().get("patients", {}).get(patient_id, [])
    for item in items[:5]:
        if item.get("kind") == "alert":
            return True
    for item in (patient.get("activity_log") or [])[:5]:
        if item.get("kind") == "alert":
            return True
    return False


def require_provider(x_provider_passcode: str | None = Header(default=None)) -> None:
    if not PROVIDER_PASSCODE or x_provider_passcode != PROVIDER_PASSCODE:
        raise HTTPException(status_code=403, detail="Provider passcode required")


def clear_patient_activity(patient_id: str) -> None:
    activity = load_activity()
    patients = activity.get("patients", {})
    patients.pop(patient_id.lower().strip(), None)
    save_json(ACTIVITY_PATH, activity)


@app.post("/feedback")
def collect_feedback(feedback: Feedback) -> dict[str, str]:
    if hasattr(logger, "log_struct"):
        logger.log_struct(feedback.model_dump(), severity="INFO")
    else:
        logger.info(f"Feedback collected: {feedback.model_dump()}")
    return {"status": "success"}


class VerifyPasscodeRequest(BaseModel):
    passcode: str


class ActivityRequest(BaseModel):
    kind: str
    summary: str
    detail: str = ""


class ProviderVerifyRequest(BaseModel):
    passcode: str


class MedicationEntry(BaseModel):
    name: str
    time: str
    status: str = "pending"


class PatientCreate(BaseModel):
    id: str
    name: str
    address: str = ""
    phone: str = ""
    passcode: str
    is_demo: bool = True
    medications: dict[str, MedicationEntry] = Field(default_factory=dict)


class PatientUpdate(BaseModel):
    name: str | None = None
    address: str | None = None
    phone: str | None = None
    passcode: str | None = None
    is_demo: bool | None = None
    medications: dict[str, MedicationEntry] | None = None


class PatientTypeToggle(BaseModel):
    is_demo: bool


app.router.routes = [
    route for route in app.router.routes if getattr(route, "path", None) != "/"
]


@app.get("/", response_class=HTMLResponse)
def aura_index() -> str:
    return AURA_INDEX_HTML


@app.get("/provider", include_in_schema=False)
def provider_trailing_slash() -> RedirectResponse:
    return RedirectResponse(url="provider/", status_code=308)


@app.get("/provider/", response_class=HTMLResponse)
def aura_provider() -> str:
    return AURA_PROVIDER_HTML


@app.get("/about", include_in_schema=False)
def about_trailing_slash() -> RedirectResponse:
    return RedirectResponse(url="about/", status_code=308)


@app.get("/about/", response_class=HTMLResponse)
def aura_about() -> str:
    return AURA_ABOUT_HTML


@app.get("/api/health")
def health() -> dict:
    return {"vertex_ok": VERTEX_OK}


@app.get("/api/patients")
def list_patients() -> dict:
    patients = load_db().get("patients", {})
    return {
        "patients": [
            {
                "id": patient_id,
                "name": pdata.get("name", patient_id.title()),
                "is_demo": pdata.get("is_demo", True),
            }
            for patient_id, pdata in patients.items()
        ]
    }


@app.get("/api/demo-passcodes")
def list_demo_passcodes() -> dict:
    patients = load_db().get("patients", {})
    profiles = []
    for patient_id, pdata in patients.items():
        if not pdata.get("is_demo", True):
            continue
        profile = {"id": patient_id, "name": pdata.get("name", patient_id.title())}
        if EXPOSE_DEMO_PASSCODES:
            profile["passcode"] = resolve_patient_passcode(patient_id, pdata.get("passcode")) or ""
        profiles.append(profile)
    notice = (
        "Passcodes are configured via environment variables on the server."
        if not EXPOSE_DEMO_PASSCODES
        else "Demo profiles only. Do not use these passcodes in production."
    )
    return {"notice": notice, "profiles": profiles, "exposed": EXPOSE_DEMO_PASSCODES}


@app.get("/api/patient/{patient_id}")
def get_patient_data(patient_id: str) -> dict:
    return public_patient(patient_id)


@app.get("/api/patient/{patient_id}/activity")
def get_patient_activity(patient_id: str) -> dict:
    patient_id_clean = patient_id.lower().strip()
    items = load_activity().get("patients", {}).get(patient_id_clean, [])
    patient_log = public_patient(patient_id_clean).get("activity_log", [])
    merged = [*items, *patient_log]
    merged.sort(key=lambda item: item.get("created_at", ""), reverse=True)
    return {"items": merged[:100]}


@app.post("/api/patient/{patient_id}/activity")
def create_patient_activity(patient_id: str, req: ActivityRequest) -> dict:
    kind = req.kind if req.kind in {"message", "update", "alert", "error"} else "update"
    return append_activity(patient_id, kind, req.summary, req.detail)


@app.post("/api/patient/{patient_id}/verify")
def verify_patient_passcode(patient_id: str, req: VerifyPasscodeRequest) -> dict:
    if not DB_PATH.exists():
        return {"success": False, "error": "Database not found"}
    try:
        patients = load_db().get("patients", {})
        patient_id_clean = patient_id.lower().strip()
        if patient_id_clean in patients:
            expected = resolve_patient_passcode(
                patient_id_clean, patients[patient_id_clean].get("passcode")
            )
            if expected and req.passcode == expected:
                append_activity(
                    patient_id_clean,
                    "update",
                    "Demo profile unlocked through security gate.",
                )
                return {"success": True}
            return {"success": False, "error": "Incorrect passcode"}
        return {"success": False, "error": f"Patient '{patient_id}' not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/provider/verify")
def verify_provider_passcode(req: ProviderVerifyRequest) -> dict:
    if req.passcode == PROVIDER_PASSCODE:
        return {"success": True}
    return {"success": False, "error": "Incorrect provider passcode"}


@app.get("/api/provider/summary")
def provider_summary() -> dict:
    patients = load_db().get("patients", {})
    rows = []
    for patient_id, pdata in patients.items():
        moods = pdata.get("mood_history") or []
        compliance = pdata.get("compliance_history") or []
        meds = pdata.get("medications") or {}
        pending_count = sum(1 for med in meds.values() if med.get("status") == "pending")
        rows.append(
            {
                "id": patient_id,
                "name": pdata.get("name", patient_id.title()),
                "is_demo": pdata.get("is_demo", True),
                "last_mood": moods[-1] if moods else None,
                "last_compliance": compliance[-1] if compliance else None,
                "consecutive_missed": consecutive_missed_cycles(compliance),
                "pending_meds": pending_count,
                "has_alert": patient_has_alert(patient_id, pdata),
            }
        )
    rows.sort(key=lambda row: (not row["has_alert"], row["name"]))
    return {"patients": rows}


@app.get("/api/provider/alerts")
def provider_alerts() -> dict:
    patients = load_db().get("patients", {})
    alerts: list[dict] = []
    for patient_id, pdata in patients.items():
        name = pdata.get("name", patient_id.title())
        moods = pdata.get("mood_history") or []
        if moods and moods[-1] < 3:
            alerts.append(
                {
                    "patient_id": patient_id,
                    "patient_name": name,
                    "kind": "alert",
                    "summary": f"Critical mood score {moods[-1]}/10 for {name}",
                    "created_at": utc_now(),
                }
            )
        missed = consecutive_missed_cycles(pdata.get("compliance_history") or [])
        if missed >= 2:
            alerts.append(
                {
                    "patient_id": patient_id,
                    "patient_name": name,
                    "kind": "alert",
                    "summary": f"{missed} consecutive missed medication cycles for {name}",
                    "created_at": utc_now(),
                }
            )

    for patient_id, items in load_activity().get("patients", {}).items():
        pdata = patients.get(patient_id, {})
        name = pdata.get("name", patient_id.title())
        for item in items:
            if item.get("kind") == "alert":
                alerts.append(
                    {
                        "patient_id": patient_id,
                        "patient_name": name,
                        "kind": "alert",
                        "summary": item.get("summary", "Alert"),
                        "created_at": item.get("created_at", ""),
                        "detail": item.get("detail", ""),
                    }
                )

    for patient_id, pdata in patients.items():
        name = pdata.get("name", patient_id.title())
        for item in pdata.get("activity_log") or []:
            if item.get("kind") == "alert":
                alerts.append(
                    {
                        "patient_id": patient_id,
                        "patient_name": name,
                        "kind": "alert",
                        "summary": item.get("summary", "Alert"),
                        "created_at": item.get("created_at", ""),
                        "detail": item.get("detail", ""),
                    }
                )

    alerts.sort(key=lambda item: item.get("created_at", ""), reverse=True)
    return {"items": alerts[:50]}


@app.post("/api/patients")
def create_patient(
    req: PatientCreate,
    x_provider_passcode: str | None = Header(default=None),
) -> dict:
    require_provider(x_provider_passcode)
    patient_id = slugify_patient_id(req.id)
    db = load_db()
    patients = db.setdefault("patients", {})
    if patient_id in patients:
        raise HTTPException(status_code=409, detail=f"Patient '{patient_id}' already exists")

    now = utc_now()
    meds = {
        med_id: med.model_dump()
        for med_id, med in req.medications.items()
    }
    patients[patient_id] = {
        "name": req.name,
        "address": req.address,
        "phone": req.phone,
        "passcode": req.passcode,
        "is_demo": req.is_demo,
        "created_at": now,
        "updated_at": now,
        "medications": meds,
        "mood_history": [],
        "compliance_history": [],
        "activity_log": [],
    }
    save_db(db)
    return {"success": True, "patient": public_patient(patient_id)}


@app.put("/api/patient/{patient_id}")
def update_patient(
    patient_id: str,
    req: PatientUpdate,
    x_provider_passcode: str | None = Header(default=None),
) -> dict:
    require_provider(x_provider_passcode)
    patient_id_clean = patient_id.lower().strip()
    db = load_db()
    patients = db.get("patients", {})
    if patient_id_clean not in patients:
        raise HTTPException(status_code=404, detail=f"Patient '{patient_id}' not found")

    patient = patients[patient_id_clean]
    if req.name is not None:
        patient["name"] = req.name
    if req.address is not None:
        patient["address"] = req.address
    if req.phone is not None:
        patient["phone"] = req.phone
    if req.passcode is not None:
        patient["passcode"] = req.passcode
    if req.is_demo is not None:
        patient["is_demo"] = req.is_demo
    if req.medications is not None:
        patient["medications"] = {
            med_id: med.model_dump() for med_id, med in req.medications.items()
        }
    patient["updated_at"] = utc_now()
    save_db(db)
    return {"success": True, "patient": public_patient(patient_id_clean)}


@app.delete("/api/patient/{patient_id}")
def delete_patient(
    patient_id: str,
    x_provider_passcode: str | None = Header(default=None),
) -> dict:
    require_provider(x_provider_passcode)
    patient_id_clean = patient_id.lower().strip()
    db = load_db()
    patients = db.get("patients", {})
    if patient_id_clean not in patients:
        raise HTTPException(status_code=404, detail=f"Patient '{patient_id}' not found")
    del patients[patient_id_clean]
    save_db(db)
    clear_patient_activity(patient_id_clean)
    return {"success": True}


@app.patch("/api/patient/{patient_id}/type")
def toggle_patient_type(
    patient_id: str,
    req: PatientTypeToggle,
    x_provider_passcode: str | None = Header(default=None),
) -> dict:
    require_provider(x_provider_passcode)
    patient_id_clean = patient_id.lower().strip()
    db = load_db()
    patients = db.get("patients", {})
    if patient_id_clean not in patients:
        raise HTTPException(status_code=404, detail=f"Patient '{patient_id}' not found")
    patients[patient_id_clean]["is_demo"] = req.is_demo
    patients[patient_id_clean]["updated_at"] = utc_now()
    save_db(db)
    return {"success": True, "patient": public_patient(patient_id_clean)}


@app.post("/api/reset")
def reset_demo_data() -> dict:
    import copy

    seed = apply_passcodes_from_env(copy.deepcopy(load_json(SEED_DB_PATH, {"patients": {}})))
    save_json(DB_PATH, seed)
    save_json(ACTIVITY_PATH, {"patients": {}})
    return {"success": True}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
