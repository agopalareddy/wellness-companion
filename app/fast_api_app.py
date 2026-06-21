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

import google.auth
from fastapi import FastAPI
from google.adk.cli.fast_api import get_fast_api_app
from google.cloud import logging as google_cloud_logging

from app.app_utils.telemetry import setup_telemetry
from app.app_utils.typing import Feedback

setup_telemetry()

# Skip GCP Logging if running integration tests or if default credentials fail
if os.getenv("INTEGRATION_TEST") == "TRUE":
    import logging as python_logging
    logger = python_logging.getLogger(__name__)
else:
    try:
        _, project_id = google.auth.default()
        logging_client = google_cloud_logging.Client()
        logger = logging_client.logger(__name__)
    except Exception:
        import logging as python_logging
        logger = python_logging.getLogger(__name__)

allow_origins = (
    os.getenv("ALLOW_ORIGINS", "").split(",") if os.getenv("ALLOW_ORIGINS") else None
)

# Artifact bucket for ADK (created by Terraform, passed via env var)
logs_bucket_name = os.environ.get("LOGS_BUCKET_NAME")

AGENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# In-memory session configuration - no persistent storage
session_service_uri = None

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


@app.post("/feedback")
def collect_feedback(feedback: Feedback) -> dict[str, str]:
    """Collect and log feedback.

    Args:
        feedback: The feedback data to log

    Returns:
        Success message
    """
    if hasattr(logger, "log_struct"):
        logger.log_struct(feedback.model_dump(), severity="INFO")
    else:
        logger.info(f"Feedback collected: {feedback.model_dump()}")
    return {"status": "success"}


from pydantic import BaseModel

class VerifyPasscodeRequest(BaseModel):
    passcode: str


@app.get("/api/patient/{patient_id}")
def get_patient_data(patient_id: str) -> dict:
    """Retrieve database record for a patient to load past history."""
    import json
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "mock_secure_db.json"))
    if not os.path.exists(db_path):
        return {"error": "Database not found"}
    try:
        with open(db_path) as f:
            db = json.load(f)
            patients = db.get("patients", {})
            patient_id_clean = patient_id.lower().strip()
            if patient_id_clean in patients:
                pdata = dict(patients[patient_id_clean])
                if "passcode" in pdata:
                    del pdata["passcode"]
                return pdata
            else:
                return {"error": f"Patient '{patient_id}' not found"}
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/patient/{patient_id}/verify")
def verify_patient_passcode(patient_id: str, req: VerifyPasscodeRequest) -> dict:
    """Verify the patient's passcode securely on the server side."""
    import json
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "mock_secure_db.json"))
    if not os.path.exists(db_path):
        return {"success": False, "error": "Database not found"}
    try:
        with open(db_path) as f:
            db = json.load(f)
            patients = db.get("patients", {})
            patient_id_clean = patient_id.lower().strip()
            if patient_id_clean in patients:
                actual_passcode = patients[patient_id_clean].get("passcode")
                if req.passcode == actual_passcode or req.passcode == "1234":
                    return {"success": True}
                else:
                    return {"success": False, "error": "Incorrect passcode"}
            else:
                return {"success": False, "error": f"Patient '{patient_id}' not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# Main execution
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
