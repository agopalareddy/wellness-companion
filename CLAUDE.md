# Coding Agent Guide — Wellness Companion

Kaggle **Agents for Good** capstone: ambient elderly wellness check-ins via Google ADK 2.0 multi-agent graph.

## Key files

| Path | Role |
|------|------|
| `app/graph.py` | ADK workflow: CompanionNode → persist_metrics_node → EscalationNode |
| `app/mcp_server.py` | MCP tools + `apply_wellness_metrics` (allowlist-validated JSON writes) |
| `app/fast_api_app.py` | FastAPI routes: patient/provider APIs, CRUD, health, reset |
| `app/aura_ui.py` | Patient, provider, and about HTML/CSS/JS (single file) |
| `app/seed_db.json` | Canonical demo clinical data (no passcodes — set via env) |
| `app/mock_secure_db.json` | Runtime DB |
| `.env.example` | Template for passcodes and provider auth |

## Architecture notes

- **Deterministic persistence**: `persist_metrics_node` calls `apply_wellness_metrics` directly — do not rely on LLM tool calls for JSON updates.
- **Per-med updates**: Explicit `medication_updates` keys change status. Empty updates + `medication_compliance: true` marks all meds `taken`. Empty updates + `false` leaves statuses unchanged.
- **Tool isolation**: CompanionNode gets `get_medication_schedule` only; no DB write access.
- **Subpath deploy**: Nav links in `aura_ui.py` use relative paths (`provider/`, `about/`, `..`). Routes redirect to trailing slashes (`/provider` → `/provider/`).
- **Session UX**: Unlock buttons become **Log out** when patient/provider session is active.
- **Secrets**: Never commit passcodes, SSH hosts, or server paths. Configure via `.env` on each deployment.

## Prerequisites

Install the CLI (one-time):
```bash
uv tool install google-agents-cli
```

Copy and fill credentials locally:
```bash
cp .env.example .env
```

---

## Development Phases

### Phase 1: Understand Requirements
Before writing any code, understand the project's requirements, constraints, and success criteria.

### Phase 2: Build and Implement
Implement agent logic in `app/`. Use `agents-cli playground` for interactive testing. Iterate based on user feedback.

### Phase 3: The Evaluation Loop (Main Iteration Phase)
Start with 1-2 eval cases, run `agents-cli eval generate`, then `agents-cli eval grade`, iterate by making changes and rerunning both commands until satisfied. Expect 5-10+ iterations. Once you have a baseline, reach for `agents-cli eval compare` (regression diffs), `agents-cli eval analyze` (cluster failure modes), and `agents-cli eval optimize` (auto-tune prompts). See the **Evaluation Guide** for metrics, dataset schema, LLM-as-judge config, and common gotchas.

### Phase 4: Pre-Deployment Tests
Run `uv run pytest tests/unit tests/integration`. Fix issues until all tests pass.

### Phase 5: Deploy to Dev
**Requires explicit human approval.** Run `agents-cli deploy` only after user confirms. See the **Deployment Guide** for details.

### Phase 6: Production Deployment
Configure environment variables on the host (see `.env.example`). Do not document hostnames, SSH aliases, or filesystem paths in this repo.

## Development Commands

| Command | Purpose |
|---------|---------|
| `agents-cli playground` | Interactive local testing |
| `uv run pytest tests/unit tests/integration` | Run unit and integration tests |
| `agents-cli eval dataset synthesize` | Synthesize multi-turn eval scenarios for your agent |
| `agents-cli eval generate` | Run agent on eval dataset, produce traces |
| `agents-cli eval grade` | Run agent evaluations on the traces |
| `agents-cli eval compare` | Compare two grade-results files (regression check) |
| `agents-cli eval analyze` | Cluster failure modes from grade results |
| `agents-cli eval metric list` | List built-in metrics available in the SDK |
| `agents-cli eval optimize` | Auto-tune agent prompts using eval data |
| `agents-cli lint` | Check code quality |
| `agents-cli infra single-project` | Set up project infrastructure (Terraform) |
| `agents-cli deploy` | Deploy to dev |
| `agents-cli scaffold enhance` | Add deployment target or CI/CD to project |
| `agents-cli scaffold upgrade` | Upgrade project to latest version |

---

## Operational Guidelines for Coding Agents

- **Code preservation**: Only modify code directly targeted by the user's request. Preserve all surrounding code, config values (e.g., `model`), comments, and formatting.
- **NEVER change the model** unless explicitly asked.
- **Model 404 errors**: Fix `GOOGLE_CLOUD_LOCATION` (e.g., `global` instead of `us-east1`), not the model name.
- **ADK tool imports**: Import the tool instance, not the module: `from google.adk.tools.load_web_page import load_web_page`
- **Run Python with `uv`**: `uv run python script.py`. Run `agents-cli install` first.
- **Stop on repeated errors**: If the same error appears 3+ times, fix the root cause instead of retrying.
- **Terraform conflicts** (Error 409): Use `terraform import` instead of retrying creation.
- **Never commit secrets**: No passcodes, server hostnames, SSH config, or deployment paths in tracked files.
