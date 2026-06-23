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

# Setup environment variables for GenAI models.
# GOOGLE_API_KEY env var → AI Studio mode (user or deployer credentials).
# No GOOGLE_API_KEY → Vertex AI via Application Default Credentials (existing behavior).
if os.getenv("GOOGLE_API_KEY"):
    # AI Studio mode — genai SDK auto-detects GOOGLE_API_KEY from env.
    # Do NOT set GOOGLE_GENAI_USE_VERTEXAI (it would override the API key).
    os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "ai-studio-user")
else:
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"
    try:
        _, project_id = google.auth.default()
        os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
    except Exception:
        # Fallback if no default credentials during local/dry-run execution
        os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "mock-project-id")

os.environ["GOOGLE_CLOUD_LOCATION"] = "global"

from google.adk.apps import App

from .graph import wellness_graph

root_agent = wellness_graph

# Initialize ADK app container with our multi-agent workflow
app = App(
    root_agent=root_agent,
    name="app",
)
