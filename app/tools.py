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
import sys

from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

# Dynamically get the absolute path to mcp_server.py to avoid relative path gotchas
server_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "mcp_server.py"))

# MCP connection parameters for stdio protocol
connection_params = StdioConnectionParams(
    server_params=StdioServerParameters(
        command=sys.executable,
        args=[server_path],
    )
)

# Toolset for CompanionNode: only allowed to pull medication schedule
companion_toolset = McpToolset(
    connection_params=connection_params,
    tool_filter=["get_medication_schedule"],
)

# Toolset for AnonymizerNode: only allowed to log anonymized metrics
anonymizer_toolset = McpToolset(
    connection_params=connection_params,
    tool_filter=["log_wellness_metrics"],
)
