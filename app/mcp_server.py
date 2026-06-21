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

from mcp.server.fastmcp import FastMCP

# Initialize FastMCP Server
mcp = FastMCP("WellnessCompanionServer")

DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "mock_secure_db.json")
)


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
        schedule_lines.append(f"- {med_info.get('time')}: {med_info.get('name')}")
    schedule_lines.append(
        "Please verify if the patient has complied with their medication schedule."
    )

    return "\n".join(schedule_lines)


@mcp.tool()
def log_wellness_metrics(patient_id: str, metrics: dict) -> str:
    """Log anonymized wellness metrics to the secure local database file for a specific patient.

    Args:
        patient_id: The ID of the patient.
        metrics: A dictionary containing metrics. It must NOT contain PII or chat text.
                 Format: {"mood_score": int, "medication_compliance": bool}
    """
    db = load_db()
    patient_id = patient_id.lower().strip()
    patients = db.get("patients", {})
    if patient_id not in patients:
        return f"Error: Patient ID '{patient_id}' not found in database."

    patient = patients[patient_id]
    mood = metrics.get("mood_score", 5)
    compliance = metrics.get("medication_compliance", True)

    # Append history
    if "mood_history" not in patient:
        patient["mood_history"] = []
    patient["mood_history"].append(mood)

    if "compliance_history" not in patient:
        patient["compliance_history"] = []
    patient["compliance_history"].append(compliance)

    # Update current medications status based on compliance
    meds = patient.get("medications", {})
    for med_id, med_info in meds.items():
        med_info["status"] = "taken" if compliance else "missed"

    save_db(db)
    return f"Successfully logged metrics for {patient.get('name')}: {json.dumps(metrics)}"


if __name__ == "__main__":
    mcp.run()
