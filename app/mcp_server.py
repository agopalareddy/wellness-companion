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


@mcp.tool()
def get_medication_schedule() -> str:
    """Pull the local daily medication schedule for the elderly patient.

    Returns:
        A string describing the active medication schedule.
    """
    return (
        "Daily Medication Schedule:\n"
        "- Morning (08:00): Cardiovascular support (1 tablet)\n"
        "- Evening (20:00): Cholesterol management (1 tablet)\n"
        "Please check if the patient has taken their medication."
    )


@mcp.tool()
def log_wellness_metrics(metrics: dict) -> str:
    """Log anonymized wellness metrics to the secure local database file.

    Args:
        metrics: A dictionary containing metrics. It must NOT contain PII or chat text.
                 Format: {"mood_score": int, "medication_compliance": bool, "consecutive_missed_cycles": int}

    Returns:
        A confirmation message indicating success.
    """
    # Secure, local mock database file path (mock_secure_db.json)
    db_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "mock_secure_db.json")
    )

    # Read existing metrics
    data = []
    if os.path.exists(db_path):
        try:
            with open(db_path) as f:
                data = json.load(f)
        except Exception:
            data = []

    # Append the new metrics
    data.append(metrics)

    # Write back
    with open(db_path, "w") as f:
        json.dump(data, f, indent=2)

    return f"Successfully logged anonymized telemetry metrics: {json.dumps(metrics)}"


if __name__ == "__main__":
    mcp.run()
