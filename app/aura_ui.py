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

AURA_ABOUT_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>About AURA | Ambient Wellness Companion</title>
  <style>
    :root { color-scheme: light; }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: #eef3f8;
      color: #17202a;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 1rem;
      padding: 1rem 1.25rem;
      background: #101927;
      color: white;
      border-bottom: 1px solid #25344a;
    }
    header a { color: #cfe0ff; text-decoration: none; font-weight: 600; }
    header a:hover { text-decoration: underline; }
    .brand { display: flex; align-items: center; gap: .75rem; }
    .brand-mark {
      display: grid; place-items: center; width: 2.35rem; height: 2.35rem;
      border-radius: 6px; background: linear-gradient(135deg, #246bfe, #0f8b8d); font-weight: 800;
    }
    main { max-width: 760px; margin: 0 auto; padding: 1.5rem 1.25rem 3rem; }
    h1 { font-size: 1.6rem; margin: 1.5rem 0 .5rem; }
    h2 { font-size: 1.15rem; margin: 1.75rem 0 .5rem; color: #084275; }
    p, li { line-height: 1.55; color: #324154; }
    .muted { color: #607086; }
    section {
      background: #ffffff; border: 1px solid #d9e2ec; border-radius: 8px;
      padding: 1.25rem 1.5rem; margin-bottom: 1rem; box-shadow: 0 1px 2px rgb(32 44 64 / 5%);
    }
    code { background: #f1f5fa; padding: .1rem .35rem; border-radius: 4px; font-size: .9em; }
    .pipeline {
      display: flex; flex-wrap: wrap; gap: .5rem; align-items: center;
      font-size: .9rem; font-weight: 600; color: #084275; margin: .5rem 0 0;
    }
    .pipeline span { background: #eaf1ff; border-radius: 999px; padding: .35rem .8rem; }
  </style>
</head>
<body>
  <header>
    <div class="brand">
      <div class="brand-mark" aria-hidden="true">A</div>
      <strong>AURA</strong>
    </div>
    <a href="..">&larr; Back to demo</a>
  </header>
  <main>
    <h1>About AURA — Ambient Wellness Companion</h1>
    <p class="muted">A Google ADK multi-agent system for ambient elderly wellness check-ins, built for the Kaggle "Agents for Good" track.</p>

    <section>
      <h2>The problem</h2>
      <p>Elderly patients living independently often go unmonitored between caregiver visits. Missed
      medication and undetected mood decline are leading causes of preventable hospitalizations.
      Caregivers want an ambient check-in that catches problems early — without becoming a
      surveillance tool that exposes sensitive health data.</p>
    </section>

    <section>
      <h2>How it works</h2>
      <p>Every check-in flows through a three-node ADK state graph, each node scoped to the minimum
      tool access it needs:</p>
      <div class="pipeline">
        <span>Companion (LLM)</span> &rarr; <span>Privacy Guard (deterministic)</span> &rarr; <span>Escalation (rules)</span> &rarr; <span>alert / normal</span>
      </div>
      <ul>
        <li><strong>MedicationExtractorNode</strong> — maps patient wording to per-med ids from the injected schedule.</li>
        <li><strong>CompanionNode</strong> — empathetic Gemini agent for mood and reply; no database write access.</li>
        <li><strong>Privacy Guard</strong> — deterministic Python node with server-side allowlist validation; the only step that writes wellness metrics to patient JSON.</li>
        <li><strong>EscalationNode</strong> — deterministic Python, not an LLM call, for the highest-stakes decision: whether to alert a caregiver.</li>
      </ul>
      <p>This is real tool isolation, not an organizational convention: a prompt-injected Companion
      response cannot cause a database write, because the write tool simply isn't in its toolset.</p>
    </section>

    <section>
      <h2>Privacy by construction</h2>
      <p>The metrics tool enforces a server-side allowlist: only <code>mood_score</code> (1-10),
      <code>medication_compliance</code> (bool), and <code>medication_updates</code>
      (<code>taken</code>/<code>missed</code>/<code>pending</code> per medication) may pass through.
      Anything else — free text, names — is rejected before it is stored. Telemetry is keyed by a
      one-way hash of the patient id, never the plaintext id; the human-readable record used for the
      passcode-gated dashboard is a separate structure.</p>
    </section>

    <section>
      <h2>Why it matters</h2>
      <p>Caregivers are notified only when it matters — two or more missed cycles, or a critical mood
      score — instead of on every check-in, which reduces alert fatigue. Patients get a low-friction,
      conversational interface with no app literacy required. And the privacy architecture is
      verifiable in code, which matters for a tool that touches health data.</p>
    </section>
  </main>
</body>
</html>
"""

AURA_INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AURA | Ambient Wellness Companion</title>
  <link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='10' fill='%23246bfe'/%3E%3Ctext x='32' y='42' text-anchor='middle' font-size='34' font-family='Arial' fill='white'%3EA%3C/text%3E%3C/svg%3E">
  <style>
    :root {
      color-scheme: light;
      --bg: #eef3f8;
      --panel: #ffffff;
      --ink: #17202a;
      --muted: #607086;
      --line: #d9e2ec;
      --blue: #246bfe;
      --teal: #0f8b8d;
      --green: #227950;
      --amber: #996a00;
      --red: #bf2f39;
      --shadow: 0 18px 50px rgb(32 44 64 / 16%);
    }

    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      background: var(--bg);
      color: var(--ink);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    button, input, select, textarea {
      font: inherit;
    }

    button:focus-visible, input:focus-visible, select:focus-visible, textarea:focus-visible {
      outline: 3px solid #79a8ff;
      outline-offset: 2px;
    }

    .skip-link {
      position: fixed;
      top: .75rem;
      left: .75rem;
      z-index: 20;
      transform: translateY(-200%);
      background: var(--ink);
      color: white;
      padding: .65rem .9rem;
      border-radius: 6px;
    }
    .skip-link:focus { transform: translateY(0); }
    .visually-hidden:not(:focus):not(:active) {
      position: absolute;
      width: 1px;
      height: 1px;
      overflow: hidden;
      clip: rect(0 0 0 0);
      clip-path: inset(50%);
      white-space: nowrap;
    }

    header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 1rem;
      padding: 1rem 1.25rem;
      background: #101927;
      color: white;
      border-bottom: 1px solid #25344a;
    }

    .brand {
      display: flex;
      align-items: center;
      gap: .75rem;
      min-width: 14rem;
    }
    .brand-mark {
      display: grid;
      place-items: center;
      width: 2.35rem;
      height: 2.35rem;
      border-radius: 6px;
      background: linear-gradient(135deg, var(--blue), var(--teal));
      font-weight: 800;
    }
    h1, h2, h3, p { margin: 0; }
    h1 { font-size: 1.15rem; line-height: 1.2; }
    .brand p, .toolbar label { color: #cbd6e3; font-size: .85rem; }

    .toolbar {
      display: flex;
      align-items: center;
      justify-content: flex-end;
      gap: .75rem;
      flex-wrap: wrap;
    }
    .toolbar select, .toolbar button, .primary, .secondary, .nav-link {
      border: 1px solid #40526d;
      border-radius: 6px;
      min-height: 2.4rem;
    }
    .toolbar select {
      background: #182335;
      color: white;
      padding: 0 .7rem;
    }
    .nav-link {
      display: inline-flex;
      align-items: center;
      text-decoration: none;
      color: #cbd6e3;
      padding: 0 .75rem;
      min-height: 2.25rem;
      font-size: .88rem;
    }
    .nav-link:hover { background: #1a2a40; }
    button {
      border: 1px solid var(--line);
      background: white;
      color: var(--ink);
      border-radius: 6px;
      cursor: pointer;
      min-height: 2.25rem;
      padding: 0 .75rem;
    }
    button:hover { border-color: #9fb2c8; }
    .primary {
      background: var(--blue);
      border-color: var(--blue);
      color: white;
      font-weight: 700;
    }
    .secondary {
      background: #f7f9fc;
      color: var(--ink);
    }
    .connection {
      display: inline-flex;
      align-items: center;
      gap: .45rem;
      color: #d9f5ec;
      font-size: .88rem;
    }
    .connection::before {
      content: "";
      width: .55rem;
      height: .55rem;
      border-radius: 999px;
      background: #32d583;
    }

    main {
      display: grid;
      grid-template-columns: minmax(19rem, 25rem) minmax(0, 1fr) minmax(20rem, 27rem);
      gap: 1rem;
      padding: 1rem;
      max-width: 1500px;
      margin: 0 auto;
    }

    section, aside {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: 0 1px 2px rgb(32 44 64 / 5%);
      min-width: 0;
    }
    .panel-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: .75rem;
      padding: 1rem;
      border-bottom: 1px solid var(--line);
      flex-wrap: wrap;
    }
    .panel-head h2, .panel-head h3 { font-size: 1rem; }
    .panel-body {
      padding: 1rem;
    }
    aside .panel-body {
      max-height: calc(100vh - 10rem);
      overflow-y: auto;
    }

    .patient-card {
      display: flex;
      gap: .85rem;
      align-items: center;
      margin-bottom: 1rem;
    }
    .avatar {
      width: 3.25rem;
      height: 3.25rem;
      border-radius: 8px;
      display: grid;
      place-items: center;
      background: #d7ecff;
      color: #084275;
      font-weight: 800;
    }
    .patient-card h2 { font-size: 1.25rem; }
    .muted { color: var(--muted); font-size: .9rem; }
    dl {
      display: grid;
      grid-template-columns: 5.5rem 1fr;
      gap: .5rem .75rem;
      margin: 0 0 1rem;
      font-size: .92rem;
    }
    dt { color: var(--muted); }
    dd { margin: 0; font-weight: 600; overflow-wrap: anywhere; }

    .med-list, .log-list, .history-list {
      display: grid;
      gap: .65rem;
      margin: 0;
      padding: 0;
      list-style: none;
    }
    .log-list, .history-list {
      max-height: 16rem;
      overflow-y: auto;
    }
    .med-item {
      display: grid;
      grid-template-columns: 1fr auto;
      gap: .75rem;
      align-items: center;
      padding: .75rem;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fbfdff;
    }
    .med-item > div { overflow-wrap: anywhere; }
    .status {
      display: inline-flex;
      align-items: center;
      gap: .35rem;
      min-width: 5.5rem;
      justify-content: center;
      padding: .35rem .5rem;
      border-radius: 999px;
      font-size: .8rem;
      font-weight: 700;
      text-transform: capitalize;
    }
    .status.pending { background: #fff4d6; color: var(--amber); }
    .status.taken, .ok { background: #dff7ea; color: var(--green); }
    .status.missed, .bad { background: #ffe2e5; color: var(--red); }

    .metrics {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: .75rem;
      margin-bottom: 1rem;
    }
    .metric {
      padding: .9rem;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #f7faff;
    }
    .metric strong {
      display: block;
      font-size: 1.35rem;
      margin-bottom: .2rem;
    }
    .privacy-note {
      border-left: 4px solid var(--teal);
      background: #edfafa;
      padding: .8rem;
      border-radius: 6px;
      color: #174d50;
      font-size: .9rem;
    }

    .messages {
      min-height: 27rem;
      max-height: 52vh;
      overflow: auto;
      overflow-x: hidden;
      display: flex;
      flex-direction: column;
      gap: .75rem;
      padding: 1rem;
      background: #f6f8fb;
    }
    .message {
      max-width: 82%;
      border-radius: 8px;
      padding: .75rem .85rem;
      line-height: 1.45;
      border: 1px solid var(--line);
      background: white;
      overflow-wrap: anywhere;
    }
    .message.user {
      align-self: flex-end;
      background: #e8f0ff;
      border-color: #bfd2ff;
    }
    .message.agent {
      align-self: flex-start;
    }
    .message.alert {
      align-self: stretch;
      max-width: 100%;
      background: #fff1f2;
      border-color: #ffb8bf;
      color: #842029;
      font-weight: 700;
    }
    .prompt-chips {
      display: flex;
      flex-wrap: wrap;
      gap: .5rem;
      padding: 0 1rem;
    }
    .chip {
      border: 1px solid var(--line);
      border-radius: 999px;
      background: #fff;
      padding: .35rem .85rem;
      font-size: .85rem;
      cursor: pointer;
    }
    .chip:hover { background: #f3f4f6; }
    .composer {
      display: grid;
      grid-template-columns: 1fr auto;
      gap: .75rem;
      padding: 1rem;
      border-top: 1px solid var(--line);
    }
    textarea {
      resize: vertical;
      min-height: 3rem;
      max-height: 9rem;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: .75rem;
    }

    .agent-status {
      display: flex;
      align-items: center;
      gap: .5rem;
      color: var(--muted);
      font-size: .88rem;
    }
    .pulse {
      width: .7rem;
      height: .7rem;
      border-radius: 999px;
      background: var(--muted);
    }
    .agent-status.busy .pulse {
      background: var(--blue);
      animation: pulse 1s infinite;
    }
    @keyframes pulse { 50% { transform: scale(1.35); opacity: .55; } }

    .log-list li, .history-list li {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: .65rem;
      background: #fbfdff;
      font-size: .86rem;
      overflow-wrap: anywhere;
    }
    .log-list time, .history-list time {
      display: block;
      color: var(--muted);
      font-size: .75rem;
      margin-top: .25rem;
    }
    pre {
      overflow: auto;
      margin: 0;
      padding: .85rem;
      background: #101927;
      color: #edf4ff;
      border-radius: 8px;
      max-height: 22rem;
      font-size: .82rem;
    }
    details { margin-top: 1rem; }
    summary {
      cursor: pointer;
      font-weight: 700;
      margin-bottom: .65rem;
    }

    dialog {
      width: min(34rem, calc(100vw - 2rem));
      border: 0;
      border-radius: 8px;
      box-shadow: var(--shadow);
      padding: 0;
    }
    dialog::backdrop {
      background: rgb(12 20 32 / 62%);
      backdrop-filter: blur(3px);
    }
    .dialog-content {
      padding: 1.2rem;
    }
    .dialog-content h2 { font-size: 1.25rem; margin-bottom: .5rem; }
    .dialog-actions {
      display: flex;
      justify-content: flex-end;
      gap: .65rem;
      margin-top: 1rem;
      flex-wrap: wrap;
    }
    .field {
      display: grid;
      gap: .35rem;
      margin-top: .9rem;
    }
    .field input, .field select {
      min-height: 2.5rem;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 0 .7rem;
    }
    .error { color: var(--red); min-height: 1.2rem; font-size: .88rem; }

    .demo-grid {
      display: grid;
      gap: .55rem;
      margin-top: .75rem;
    }
    .demo-code {
      display: flex;
      justify-content: space-between;
      gap: .75rem;
      padding: .7rem;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #f7f9fc;
    }

    @media (max-width: 1120px) {
      main { grid-template-columns: 1fr; }
      .messages { max-height: none; }
    }
    @media (max-width: 680px) {
      header { align-items: flex-start; }
      .toolbar { width: 100%; justify-content: flex-start; }
      .composer { grid-template-columns: 1fr; }
      .message { max-width: 100%; }
      dl { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <a class="skip-link" href="#content">Skip to dashboard</a>
  <header>
    <div class="brand">
      <div class="brand-mark" aria-hidden="true">A</div>
      <div>
        <h1>AURA</h1>
        <p>Ambient Wellness Companion</p>
      </div>
    </div>
    <div class="toolbar" aria-label="Patient controls">
      <label for="patient-select">Patient account</label>
      <select id="patient-select"></select>
      <button type="button" id="unlock-btn" class="secondary">Unlock profile</button>
      <a href="about/" class="nav-link">About</a>
      <a href="provider/" class="nav-link">Provider view</a>
      <span class="connection" id="connection-status">Checking node…</span>
    </div>
  </header>

  <main id="content" tabindex="-1">
    <section aria-labelledby="patient-title">
      <div class="panel-head">
        <h2 id="patient-title">Patient Dashboard</h2>
        <button type="button" id="refresh-btn">Refresh</button>
      </div>
      <div class="panel-body">
        <div class="patient-card">
          <div id="patient-avatar" class="avatar" aria-hidden="true">--</div>
          <div>
            <h2 id="patient-name">Select a profile</h2>
            <p id="patient-id" class="muted">No patient unlocked</p>
          </div>
        </div>
        <dl>
          <dt>Address</dt><dd id="patient-address">Locked</dd>
          <dt>Phone</dt><dd id="patient-phone">Locked</dd>
          <dt>Status</dt><dd id="patient-status">Awaiting passcode</dd>
        </dl>
        <h3>Medication Schedule</h3>
        <ul id="med-list" class="med-list" aria-live="polite"></ul>
        <h3 style="margin-top:1rem;">Daily Wellness Analytics</h3>
        <div class="metrics" aria-live="polite">
          <div class="metric"><strong id="mood-score">--</strong><span>Mood score</span></div>
          <div class="metric"><strong id="compliance-score">--</strong><span>Medication compliance</span></div>
        </div>
        <p class="privacy-note">Only the selected patient record is shown. Passcodes are excluded from this patient JSON view.</p>
        <details>
          <summary>View selected patient JSON</summary>
          <pre id="patient-json" tabindex="0">{}</pre>
        </details>
      </div>
    </section>

    <section aria-labelledby="chat-title">
      <div class="panel-head">
        <h2 id="chat-title">Companion Check-in</h2>
        <div id="agent-status" class="agent-status"><span class="pulse" aria-hidden="true"></span><span id="status-text">Idle</span></div>
      </div>
      <div id="messages" class="messages" aria-live="polite"></div>
      <div class="prompt-chips" role="group" aria-label="Guided demo check-ins">
        <button type="button" class="chip" data-prompt="Good morning! I took all my pills today and I feel great.">Normal check-in</button>
        <button type="button" class="chip" data-prompt="I missed my medication again this morning, sorry.">Missed meds</button>
        <button type="button" class="chip" data-prompt="I feel hopeless and haven't been able to do anything, and I missed all my pills again today.">Escalation demo</button>
      </div>
      <form id="chat-form" class="composer">
        <label class="visually-hidden" for="message-input">Type patient check-in response</label>
        <textarea id="message-input" placeholder="Type patient check-in response here..." required></textarea>
        <button type="submit" class="primary">Send</button>
      </form>
    </section>

    <aside aria-labelledby="ops-title">
      <div class="panel-head">
        <h2 id="ops-title">Agent Activity</h2>
        <button type="button" id="clear-local-btn">Reset view</button>
        <button type="button" id="reset-demo-btn">Reset demo data</button>
      </div>
      <div class="panel-body">
        <h3>Run log</h3>
        <ul id="log-list" class="log-list" aria-live="polite"></ul>
        <h3 style="margin-top:1rem;">Past history and alerts</h3>
        <ul id="history-list" class="history-list"></ul>
      </div>
    </aside>
  </main>

  <dialog id="security-dialog" aria-labelledby="security-title">
    <form id="security-form" class="dialog-content">
      <h2 id="security-title">Unlock demo patient profile</h2>
      <p class="muted">Choose a demo profile and enter its passcode. This gate is for judging the demo flow, not production authentication.</p>
      <div class="field">
        <label for="security-patient">Demo profile</label>
        <select id="security-patient"></select>
      </div>
      <div class="field">
        <label for="security-passcode">Passcode</label>
        <input id="security-passcode" type="password" inputmode="numeric" autocomplete="current-password" required>
      </div>
      <p id="security-error" class="error" role="alert"></p>
      <div class="dialog-actions">
        <button type="button" id="show-demo-codes" class="secondary">Show demo passcodes</button>
        <button type="submit" class="primary">Unlock</button>
      </div>
    </form>
  </dialog>

  <dialog id="passcode-dialog" aria-labelledby="passcode-title">
    <div class="dialog-content">
      <h2 id="passcode-title">Demo passcodes only</h2>
      <p class="muted">These passcodes exist only to make the Kaggle demo easy to evaluate. They should not be reused as a production security design.</p>
      <div id="demo-passcodes" class="demo-grid"></div>
      <div class="dialog-actions">
        <button type="button" id="close-passcodes" class="primary">Close</button>
      </div>
    </div>
  </dialog>

  <div id="polite-announcer" aria-live="polite" aria-atomic="true" style="position:absolute;left:-9999px;"></div>

  <script>
    const app = {
      patients: [],
      patient: null,
      patientId: localStorage.getItem("auraPatientId") || "",
      sessionId: localStorage.getItem("auraSessionId") || "",
      pollTimer: null,
      busy: false
    };

    const $ = (id) => document.getElementById(id);

    function initials(name) {
      return (name || "--").split(" ").map((part) => part[0]).join("").slice(0, 2).toUpperCase();
    }

    function announce(text) {
      $("polite-announcer").textContent = text;
    }

    function setBusy(isBusy, text) {
      app.busy = isBusy;
      $("agent-status").classList.toggle("busy", isBusy);
      $("status-text").textContent = text;
    }

    function formatTime(value) {
      try { return new Date(value).toLocaleString(); } catch { return ""; }
    }

    function medStatusClass(status) {
      return ["taken", "missed", "pending"].includes(status) ? status : "pending";
    }

    function renderPatient(patient) {
      app.patient = patient;
      $("patient-avatar").textContent = initials(patient.name);
      $("patient-name").textContent = patient.name || "Unknown patient";
      $("patient-id").textContent = `Patient ID: #PT-${app.patientId.toUpperCase()}`;
      $("patient-address").textContent = patient.address || "Not recorded";
      $("patient-phone").textContent = patient.phone || "Not recorded";
      $("patient-status").textContent = "Active monitoring";

      const meds = patient.medications || {};
      $("med-list").innerHTML = Object.entries(meds).map(([id, med]) => `
        <li class="med-item">
          <div>
            <strong>${escapeHtml(med.name || id)}</strong>
            <div class="muted">${escapeHtml(med.time || "No time set")}</div>
          </div>
          <span class="status ${medStatusClass(med.status)}">${escapeHtml(med.status || "pending")}</span>
        </li>
      `).join("") || `<li class="med-item">No medications recorded.</li>`;

      const moods = patient.mood_history || [];
      const compliance = patient.compliance_history || [];
      const lastMood = moods.length ? moods[moods.length - 1] : "--";
      const lastCompliance = compliance.length ? compliance[compliance.length - 1] : null;
      $("mood-score").textContent = lastMood === "--" ? "--" : `${lastMood}/10`;
      $("compliance-score").textContent = lastCompliance === null ? "--" : (lastCompliance ? "Compliant" : "Needs review");
      $("compliance-score").className = lastCompliance === false ? "bad" : "ok";
      $("patient-json").textContent = JSON.stringify(patient, null, 2);
      updateSessionButton();
    }

    function renderLocked() {
      $("patient-avatar").textContent = "--";
      $("patient-name").textContent = "Select a profile";
      $("patient-id").textContent = "No patient unlocked";
      $("patient-address").textContent = "Locked";
      $("patient-phone").textContent = "Locked";
      $("patient-status").textContent = "Awaiting passcode";
      $("med-list").innerHTML = `<li class="med-item">Unlock a demo profile to load medication data.</li>`;
      $("mood-score").textContent = "--";
      $("compliance-score").textContent = "--";
      $("patient-json").textContent = "{}";
      updateSessionButton();
    }

    function isPatientUnlocked() {
      return Boolean(app.patientId);
    }

    function updateSessionButton() {
      const btn = $("unlock-btn");
      if (isPatientUnlocked()) {
        btn.textContent = "Log out";
        btn.setAttribute("aria-label", "Log out of patient profile");
      } else {
        btn.textContent = "Unlock profile";
        btn.setAttribute("aria-label", "Unlock patient profile");
      }
    }

    function logoutPatient() {
      app.patientId = "";
      app.patient = null;
      app.sessionId = "";
      localStorage.removeItem("auraPatientId");
      localStorage.removeItem("auraSessionId");
      $("patient-select").value = "";
      renderLocked();
      addLog("Logged out of patient profile", "security");
      announce("Logged out of patient profile");
    }

    function renderHistory(items) {
      $("history-list").innerHTML = items.slice(0, 12).map((item) => {
        const label = item.kind === "alert" ? "Alert" : item.kind === "message" ? "Message" : "Update";
        return `<li><strong>${label}:</strong> ${escapeHtml(item.summary || item.detail || "")}<time>${formatTime(item.created_at)}</time></li>`;
      }).join("") || `<li>No prior history for this patient yet.</li>`;
    }

    function addLog(detail, kind = "update") {
      const li = document.createElement("li");
      li.innerHTML = `<strong>${escapeHtml(kind)}:</strong> ${escapeHtml(detail)}<time>${new Date().toLocaleString()}</time>`;
      $("log-list").prepend(li);
    }

    function addMessage(role, text, alert = false) {
      const div = document.createElement("div");
      div.className = `message ${alert ? "alert" : role}`;
      div.textContent = text;
      $("messages").append(div);
      $("messages").scrollTop = $("messages").scrollHeight;
    }

    function escapeHtml(value) {
      return String(value).replace(/[&<>"']/g, (char) => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
      })[char]);
    }

    async function api(path, options = {}) {
      const response = await fetch(path, {
        headers: { "Content-Type": "application/json", ...(options.headers || {}) },
        ...options
      });
      if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
      return response.json();
    }

    async function loadPatients() {
      const data = await api("/api/patients");
      app.patients = data.patients || [];
      const options = app.patients.map((p) => `<option value="${p.id}">${escapeHtml(p.name)}</option>`).join("");
      $("patient-select").innerHTML = `<option value="">Choose patient</option>${options}`;
      $("security-patient").innerHTML = `<option value="">Choose patient</option>${options}`;
      if (app.patientId) {
        $("patient-select").value = app.patientId;
        $("security-patient").value = app.patientId;
      }
    }

    async function loadPatient() {
      if (!app.patientId) {
        renderLocked();
        return;
      }
      const patient = await api(`/api/patient/${app.patientId}`);
      if (patient.error) throw new Error(patient.error);
      renderPatient(patient);
      const history = await api(`/api/patient/${app.patientId}/activity`);
      renderHistory(history.items || []);
      return patient;
    }

    async function unlock(patientId, passcode) {
      if (!patientId) throw new Error("Choose a demo profile first");
      const result = await api(`/api/patient/${patientId}/verify`, {
        method: "POST",
        body: JSON.stringify({ passcode })
      });
      if (!result.success) throw new Error(result.error || "Incorrect passcode");
      app.patientId = patientId;
      localStorage.setItem("auraPatientId", patientId);
      $("patient-select").value = patientId;
      $("security-dialog").close();
      await loadPatient();
      updateSessionButton();
      addLog(`Unlocked ${app.patient.name} profile`, "security");
      announce(`${app.patient.name} profile loaded`);
    }

    async function loadDemoPasscodes() {
      const data = await api("/api/demo-passcodes");
      if (!data.exposed) {
        $("demo-passcodes").innerHTML = `<p class="muted">${escapeHtml(data.notice || "Passcodes are not published. Use credentials configured for this deployment.")}</p>`;
      } else {
        $("demo-passcodes").innerHTML = data.profiles.map((profile) => `
          <div class="demo-code">
            <span>${escapeHtml(profile.name)}</span>
            <strong>${escapeHtml(profile.passcode || "—")}</strong>
          </div>
        `).join("");
      }
      $("passcode-dialog").showModal();
    }

    async function ensureSession() {
      if (app.sessionId) return app.sessionId;
      const result = await api(`/apps/app/users/${app.patientId}/sessions`, {
        method: "POST",
        body: JSON.stringify({ state: { patient_id: app.patientId, preferred_language: "English" } })
      });
      app.sessionId = result.id;
      localStorage.setItem("auraSessionId", result.id);
      addLog(`Created ADK session ${result.id}`, "session");
      return app.sessionId;
    }

    function startLiveRefresh() {
      clearInterval(app.pollTimer);
      app.pollTimer = setInterval(() => {
        loadPatient().catch(() => {});
      }, 1400);
    }

    function stopLiveRefresh() {
      clearInterval(app.pollTimer);
      app.pollTimer = null;
    }

    function summarizeEvent(event) {
      if (event.error_message) return `Agent error: ${event.error_message}`;
      if (event.actions?.state_delta) {
        const keys = Object.keys(event.actions.state_delta).join(", ");
        return `State updated: ${keys}`;
      }
      if (event.content?.parts?.some((part) => part.function_call)) return "Tool call dispatched";
      if (event.content?.parts?.some((part) => part.function_response)) return "Tool response received";
      if (event.author) return `${event.author} produced an event`;
      return "Agent event received";
    }

    function extractText(event) {
      const parts = event.content?.parts || [];
      return parts.map((part) => part.text || "").filter(Boolean).join("\\n").trim();
    }

    function metricsPersisted(patient) {
      const log = patient?.activity_log || [];
      return log.some((item) => String(item.summary || "").includes("Logged mood"));
    }

    async function persistActivity(payload) {
      if (!app.patientId) return;
      await api(`/api/patient/${app.patientId}/activity`, {
        method: "POST",
        body: JSON.stringify(payload)
      }).catch(() => {});
    }

    async function sendMessage(text, retried = false) {
      if (!app.patientId) {
        $("security-dialog").showModal();
        return;
      }
      if (app.busy && !retried) return;
      if (!retried) {
        addMessage("user", text);
        await persistActivity({ kind: "message", summary: `Patient said: ${text}` });
      }
      setBusy(true, "Agent processing check-in");
      addLog("Started Companion -> Privacy Guard -> Escalation workflow", "run");
      startLiveRefresh();

      try {
        const sessionId = await ensureSession();
        const response = await fetch("/run_sse", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            app_name: "app",
            user_id: app.patientId,
            session_id: sessionId,
            new_message: { role: "user", parts: [{ text }] },
            streaming: true
          })
        });
        if (!response.ok) {
          if (!retried && [404, 409, 422].includes(response.status)) {
            app.sessionId = "";
            localStorage.removeItem("auraSessionId");
            return sendMessage(text, true);
          }
          throw new Error(`Agent request failed: ${response.status}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        let finalText = "";
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\\n");
          buffer = lines.pop();
          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;
            const event = JSON.parse(line.slice(6));
            const summary = summarizeEvent(event);
            addLog(summary, "agent");
            const textPart = extractText(event);
            if (textPart) finalText = textPart;
            await loadPatient().catch(() => {});
          }
        }

        const alert = /alert|critical|escalation/i.test(finalText);
        addMessage("agent", finalText || "Check-in processed. The dashboard has been updated.", alert);
        await persistActivity({
          kind: alert ? "alert" : "update",
          summary: finalText || "Agent completed check-in and updated wellness state."
        });
        const patient = await loadPatient();
        if (metricsPersisted(patient)) {
          addLog("Wellness metrics persisted to patient JSON", "update");
        }
        setBusy(false, alert ? "Alert generated" : "Idle");
        addLog(alert ? "Escalation alert recorded with patient context" : "Wellness metrics and medication state refreshed", alert ? "alert" : "update");
      } catch (error) {
        addMessage("agent", error.message, true);
        addLog(error.message, "error");
        setBusy(false, "Needs attention");
      } finally {
        stopLiveRefresh();
      }
    }

    $("security-form").addEventListener("submit", async (event) => {
      event.preventDefault();
      $("security-error").textContent = "";
      try {
        await unlock($("security-patient").value, $("security-passcode").value);
        $("security-passcode").value = "";
      } catch (error) {
        $("security-error").textContent = error.message;
      }
    });

    $("chat-form").addEventListener("submit", async (event) => {
      event.preventDefault();
      const text = $("message-input").value.trim();
      if (!text || app.busy) return;
      $("message-input").value = "";
      await sendMessage(text);
    });

    $("unlock-btn").addEventListener("click", () => {
      if (isPatientUnlocked()) {
        logoutPatient();
        return;
      }
      $("security-dialog").showModal();
    });
    $("show-demo-codes").addEventListener("click", loadDemoPasscodes);
    $("close-passcodes").addEventListener("click", () => $("passcode-dialog").close());
    $("refresh-btn").addEventListener("click", () => loadPatient().then(() => addLog("Patient data refreshed", "update")));
    $("clear-local-btn").addEventListener("click", () => {
      $("messages").innerHTML = "";
      $("log-list").innerHTML = "";
      addLog("Local view reset; server history preserved", "view");
    });
    $("reset-demo-btn").addEventListener("click", async () => {
      await api("/api/reset", { method: "POST" });
      $("messages").innerHTML = "";
      $("log-list").innerHTML = "";
      addLog("Demo database and activity log restored from seed", "view");
      await loadPatient().catch(() => {});
    });
    document.querySelectorAll(".chip").forEach((chip) => {
      chip.addEventListener("click", () => {
        $("message-input").value = chip.dataset.prompt;
        $("chat-form").requestSubmit();
      });
    });
    $("patient-select").addEventListener("change", () => {
      const value = $("patient-select").value;
      if (!value) return;
      $("security-patient").value = value;
      $("security-dialog").showModal();
    });

    async function checkHealth() {
      try {
        const health = await api("/api/health");
        $("connection-status").textContent = health.vertex_ok ? "GCP node connected" : "Node degraded (mock mode)";
      } catch {
        $("connection-status").textContent = "Node unreachable";
      }
    }

    (async function init() {
      renderLocked();
      await checkHealth();
      await loadPatients();
      if (app.patientId) {
        await loadPatient().catch(() => {
          localStorage.removeItem("auraPatientId");
          app.patientId = "";
          renderLocked();
          $("security-dialog").showModal();
        });
        if (app.patient) {
          addMessage("agent", `AURA restored the last unlocked profile for ${app.patient.name}.`);
          addLog(`Restored ${app.patient.name} from local session memory`, "session");
        }
      } else {
        $("security-dialog").showModal();
      }
    })();
  </script>
</body>
</html>
"""

AURA_PROVIDER_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AURA Provider | Care Team Dashboard</title>
  <link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='10' fill='%23246bfe'/%3E%3Ctext x='32' y='42' text-anchor='middle' font-size='34' font-family='Arial' fill='white'%3EA%3C/text%3E%3C/svg%3E">
  <style>
    :root {
      color-scheme: light;
      --bg: #eef3f8;
      --panel: #ffffff;
      --ink: #17202a;
      --muted: #607086;
      --line: #d9e2ec;
      --blue: #246bfe;
      --teal: #0f8b8d;
      --green: #227950;
      --amber: #996a00;
      --red: #bf2f39;
      --shadow: 0 18px 50px rgb(32 44 64 / 16%);
    }

    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      background: var(--bg);
      color: var(--ink);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    button, input, select, textarea { font: inherit; }
    button:focus-visible, input:focus-visible, select:focus-visible, textarea:focus-visible {
      outline: 3px solid #79a8ff;
      outline-offset: 2px;
    }

    header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 1rem;
      padding: 1rem 1.25rem;
      background: #101927;
      color: white;
      border-bottom: 1px solid #25344a;
    }
    .brand {
      display: flex;
      align-items: center;
      gap: .75rem;
      min-width: 14rem;
    }
    .brand-mark {
      display: grid;
      place-items: center;
      width: 2.35rem;
      height: 2.35rem;
      border-radius: 6px;
      background: linear-gradient(135deg, var(--blue), var(--teal));
      font-weight: 800;
    }
    h1, h2, h3, p { margin: 0; }
    h1 { font-size: 1.15rem; line-height: 1.2; }
    .brand p { color: #cbd6e3; font-size: .85rem; }

    .toolbar {
      display: flex;
      align-items: center;
      justify-content: flex-end;
      gap: .75rem;
      flex-wrap: wrap;
    }
    .nav-link, .toolbar button {
      border: 1px solid #40526d;
      border-radius: 6px;
      min-height: 2.4rem;
    }
    .nav-link {
      display: inline-flex;
      align-items: center;
      text-decoration: none;
      color: #cbd6e3;
      padding: 0 .75rem;
      font-size: .88rem;
    }
    .nav-link:hover { background: #1a2a40; }
    button {
      border: 1px solid var(--line);
      background: white;
      color: var(--ink);
      border-radius: 6px;
      cursor: pointer;
      min-height: 2.25rem;
      padding: 0 .75rem;
    }
    button:hover { border-color: #9fb2c8; }
    .primary {
      background: var(--blue);
      border-color: var(--blue);
      color: white;
      font-weight: 700;
    }
    .secondary {
      background: #f7f9fc;
      color: var(--ink);
    }
    .danger {
      background: #fff1f2;
      border-color: #ffb8bf;
      color: var(--red);
    }

    main {
      display: grid;
      grid-template-columns: minmax(16rem, 22rem) minmax(0, 1fr) minmax(18rem, 24rem);
      gap: 1rem;
      padding: 1rem;
      max-width: 1500px;
      margin: 0 auto;
    }

    section, aside {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: 0 1px 2px rgb(32 44 64 / 5%);
      min-width: 0;
    }
    .panel-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: .75rem;
      padding: 1rem;
      border-bottom: 1px solid var(--line);
      flex-wrap: wrap;
    }
    .panel-head h2, .panel-head h3 { font-size: 1rem; }
    .panel-body { padding: 1rem; }
    aside .panel-body {
      max-height: calc(100vh - 10rem);
      overflow-y: auto;
    }

    .muted { color: var(--muted); font-size: .9rem; }
    .roster-list {
      display: grid;
      gap: .55rem;
      margin: 0;
      padding: 0;
      list-style: none;
      max-height: calc(100vh - 14rem);
      overflow-y: auto;
    }
    .roster-item {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: .7rem;
      background: #fbfdff;
      cursor: pointer;
    }
    .roster-item:hover { border-color: #9fb2c8; }
    .roster-item.selected {
      border-color: var(--blue);
      background: #eef4ff;
    }
    .roster-main {
      display: flex;
      align-items: center;
      gap: .45rem;
      flex-wrap: wrap;
      overflow-wrap: anywhere;
    }
    .roster-meta {
      font-size: .82rem;
      margin-top: .25rem;
    }
    .badge {
      display: inline-flex;
      align-items: center;
      padding: .15rem .5rem;
      border-radius: 999px;
      font-size: .72rem;
      font-weight: 700;
      text-transform: uppercase;
    }
    .badge.demo { background: #fff4d6; color: var(--amber); }
    .badge.real { background: #dff7ea; color: var(--green); }
    .alert-dot {
      display: inline-grid;
      place-items: center;
      width: 1.1rem;
      height: 1.1rem;
      border-radius: 999px;
      background: var(--red);
      color: white;
      font-size: .7rem;
      font-weight: 800;
    }
    .toggle-type-btn {
      margin-top: .45rem;
      font-size: .78rem;
      min-height: 1.9rem;
      padding: 0 .55rem;
    }

    dl {
      display: grid;
      grid-template-columns: 5.5rem 1fr;
      gap: .5rem .75rem;
      margin: 0 0 1rem;
      font-size: .92rem;
    }
    dt { color: var(--muted); }
    dd { margin: 0; font-weight: 600; overflow-wrap: anywhere; }

    .med-list, .activity-list, .alert-inbox {
      display: grid;
      gap: .65rem;
      margin: 0;
      padding: 0;
      list-style: none;
    }
    .activity-list, .alert-inbox {
      max-height: 16rem;
      overflow-y: auto;
    }
    .med-item {
      display: grid;
      grid-template-columns: 1fr auto;
      gap: .75rem;
      align-items: center;
      padding: .75rem;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fbfdff;
    }
    .med-item > div { overflow-wrap: anywhere; }
    .status {
      display: inline-flex;
      align-items: center;
      gap: .35rem;
      min-width: 5.5rem;
      justify-content: center;
      padding: .35rem .5rem;
      border-radius: 999px;
      font-size: .8rem;
      font-weight: 700;
      text-transform: capitalize;
    }
    .status.pending { background: #fff4d6; color: var(--amber); }
    .status.taken { background: #dff7ea; color: var(--green); }
    .status.missed { background: #ffe2e5; color: var(--red); }

    .activity-list li, .alert-inbox li {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: .65rem;
      background: #fbfdff;
      font-size: .86rem;
      overflow-wrap: anywhere;
    }
    .alert-inbox li.alert {
      background: #fff1f2;
      border-color: #ffb8bf;
    }
    .activity-list time, .alert-inbox time {
      display: block;
      color: var(--muted);
      font-size: .75rem;
      margin-top: .25rem;
    }

    pre {
      overflow: auto;
      margin: 0;
      padding: .85rem;
      background: #101927;
      color: #edf4ff;
      border-radius: 8px;
      max-height: 22rem;
      font-size: .78rem;
    }

    details { margin-top: 1rem; }
    summary {
      cursor: pointer;
      font-weight: 700;
      margin-bottom: .65rem;
    }
    .manage-form {
      display: grid;
      gap: .65rem;
      margin-top: .75rem;
    }
    .manage-form input, .manage-form select {
      min-height: 2.35rem;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 0 .65rem;
    }
    .manage-actions {
      display: flex;
      flex-wrap: wrap;
      gap: .5rem;
      margin-top: .5rem;
    }
    .field-row {
      display: flex;
      align-items: center;
      gap: .5rem;
    }

    dialog {
      width: min(34rem, calc(100vw - 2rem));
      border: 0;
      border-radius: 8px;
      box-shadow: var(--shadow);
      padding: 0;
    }
    dialog::backdrop {
      background: rgb(12 20 32 / 62%);
      backdrop-filter: blur(3px);
    }
    .dialog-content { padding: 1.2rem; }
    .dialog-content h2 { font-size: 1.25rem; margin-bottom: .5rem; }
    .dialog-actions {
      display: flex;
      justify-content: flex-end;
      gap: .65rem;
      margin-top: 1rem;
      flex-wrap: wrap;
    }
    .field {
      display: grid;
      gap: .35rem;
      margin-top: .9rem;
    }
    .field input {
      min-height: 2.5rem;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 0 .7rem;
    }
    .error { color: var(--red); min-height: 1.2rem; font-size: .88rem; }

    @media (max-width: 1120px) {
      main { grid-template-columns: 1fr; }
    }
    @media (max-width: 680px) {
      header { align-items: flex-start; }
      .toolbar { width: 100%; justify-content: flex-start; }
      dl { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <header>
    <div class="brand">
      <div class="brand-mark" aria-hidden="true">A</div>
      <div>
        <h1>AURA Provider</h1>
        <p>Care team dashboard</p>
      </div>
    </div>
    <div class="toolbar" aria-label="Provider controls">
      <a href=".." class="nav-link">Patient view</a>
      <button type="button" id="provider-unlock-btn" class="secondary">Provider unlock</button>
    </div>
  </header>

  <main>
    <aside aria-labelledby="roster-title">
      <div class="panel-head">
        <h2 id="roster-title">Patient roster</h2>
      </div>
      <div class="panel-body">
        <ul id="roster-list" class="roster-list" aria-live="polite"></ul>
        <details>
          <summary>Manage patients</summary>
          <form id="create-form" class="manage-form">
            <h3>Create patient</h3>
            <input id="create-id" placeholder="Patient id (slug)" required>
            <input id="create-name" placeholder="Full name" required>
            <input id="create-address" placeholder="Address">
            <input id="create-phone" placeholder="Phone">
            <input id="create-passcode" placeholder="Passcode" required>
            <label class="field-row">
              <input id="create-is-demo" type="checkbox" checked>
              <span>Demo profile</span>
            </label>
            <div class="manage-actions">
              <button type="submit" class="primary">Create</button>
            </div>
            <p id="create-error" class="error" role="alert"></p>
          </form>
          <form id="edit-form" class="manage-form">
            <h3>Edit selected patient</h3>
            <input id="edit-name" placeholder="Full name">
            <input id="edit-address" placeholder="Address">
            <input id="edit-phone" placeholder="Phone">
            <input id="edit-passcode" placeholder="New passcode (optional)">
            <label class="field-row">
              <input id="edit-is-demo" type="checkbox">
              <span>Demo profile</span>
            </label>
            <div class="manage-actions">
              <button type="submit" class="secondary">Save changes</button>
              <button type="button" id="delete-btn" class="danger">Delete patient</button>
            </div>
            <p id="edit-error" class="error" role="alert"></p>
          </form>
        </details>
      </div>
    </aside>

    <section aria-labelledby="detail-title">
      <div class="panel-head">
        <h2 id="detail-title">Patient detail</h2>
      </div>
      <div class="panel-body">
        <p id="detail-empty" class="muted">Select a patient from the roster.</p>
        <div id="detail-content" hidden>
          <h3 id="detail-name">—</h3>
          <p id="detail-id" class="muted"></p>
          <dl>
            <dt>Status</dt><dd id="detail-status">—</dd>
            <dt>Mood</dt><dd id="detail-mood">—</dd>
            <dt>Compliance</dt><dd id="detail-compliance">—</dd>
            <dt>Address</dt><dd id="detail-address">—</dd>
            <dt>Phone</dt><dd id="detail-phone">—</dd>
          </dl>
          <h3>Medications</h3>
          <ul id="detail-meds" class="med-list"></ul>
          <h3 style="margin-top:1rem;">Activity stream</h3>
          <ul id="detail-activity" class="activity-list" aria-live="polite"></ul>
        </div>
      </div>
    </section>

    <aside aria-labelledby="alerts-title">
      <div class="panel-head">
        <h2 id="alerts-title">Alerts &amp; JSON</h2>
      </div>
      <div class="panel-body">
        <h3>Live alert inbox</h3>
        <ul id="alert-inbox" class="alert-inbox" aria-live="polite"></ul>
        <h3 style="margin-top:1rem;">Patient JSON</h3>
        <pre id="patient-json" tabindex="0">{}</pre>
      </div>
    </aside>
  </main>

  <dialog id="provider-dialog" aria-labelledby="provider-dialog-title">
    <form id="provider-form" class="dialog-content">
      <h2 id="provider-dialog-title">Provider unlock</h2>
      <p class="muted">Enter the provider passcode configured for this deployment.</p>
      <div class="field">
        <label for="provider-passcode">Provider passcode</label>
        <input id="provider-passcode" type="password" inputmode="numeric" autocomplete="current-password" required>
      </div>
      <p id="provider-error" class="error" role="alert"></p>
      <div class="dialog-actions">
        <button type="submit" class="primary">Unlock</button>
      </div>
    </form>
  </dialog>

  <script>
    const app = {
      roster: [],
      alerts: [],
      selectedId: "",
      patient: null,
      pollTimer: null
    };

    const $ = (id) => document.getElementById(id);

    function escapeHtml(value) {
      return String(value).replace(/[&<>"']/g, (char) => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
      })[char]);
    }

    function formatTime(value) {
      try { return new Date(value).toLocaleString(); } catch { return ""; }
    }

    function providerHeaders() {
      return {
        "Content-Type": "application/json",
        "X-Provider-Passcode": sessionStorage.getItem("providerPasscode") || ""
      };
    }

    function hasProviderPasscode() {
      return Boolean(sessionStorage.getItem("providerPasscode"));
    }

    function updateProviderSessionButton() {
      const btn = $("provider-unlock-btn");
      if (hasProviderPasscode()) {
        btn.textContent = "Log out";
        btn.setAttribute("aria-label", "Log out of provider session");
      } else {
        btn.textContent = "Provider unlock";
        btn.setAttribute("aria-label", "Unlock provider session");
      }
    }

    function logoutProvider() {
      sessionStorage.removeItem("providerPasscode");
      updateProviderSessionButton();
    }

    async function api(path, options = {}) {
      const response = await fetch(path, {
        headers: { "Content-Type": "application/json", ...(options.headers || {}) },
        ...options
      });
      if (!response.ok) {
        const detail = await response.text().catch(() => "");
        throw new Error(detail || `${response.status} ${response.statusText}`);
      }
      if (response.status === 204) return {};
      return response.json();
    }

    function medStatusClass(status) {
      return ["taken", "missed", "pending"].includes(status) ? status : "pending";
    }

    function renderRoster() {
      $("roster-list").innerHTML = app.roster.map((row) => `
        <li class="roster-item ${row.id === app.selectedId ? "selected" : ""}" data-id="${escapeHtml(row.id)}">
          <div class="roster-main">
            <strong>${escapeHtml(row.name)}</strong>
            <span class="badge ${row.is_demo ? "demo" : "real"}">${row.is_demo ? "demo" : "real"}</span>
            ${row.has_alert ? '<span class="alert-dot" title="Alert active">!</span>' : ""}
          </div>
          <div class="roster-meta muted">
            Mood: ${row.last_mood ?? "—"} · Missed cycles: ${row.consecutive_missed}
          </div>
          <button type="button" class="toggle-type-btn secondary" data-id="${escapeHtml(row.id)}" data-demo="${row.is_demo}">
            Mark ${row.is_demo ? "real" : "demo"}
          </button>
        </li>
      `).join("") || `<li class="muted">No patients in roster.</li>`;

      document.querySelectorAll(".roster-item").forEach((item) => {
        item.addEventListener("click", (event) => {
          if (event.target.closest(".toggle-type-btn")) return;
          selectPatient(item.dataset.id);
        });
      });
      document.querySelectorAll(".toggle-type-btn").forEach((btn) => {
        btn.addEventListener("click", async (event) => {
          event.stopPropagation();
          if (!hasProviderPasscode()) {
            $("provider-dialog").showModal();
            return;
          }
          const patientId = btn.dataset.id;
          const isDemo = btn.dataset.demo === "true";
          try {
            await api(`/api/patient/${patientId}/type`, {
              method: "PATCH",
              headers: providerHeaders(),
              body: JSON.stringify({ is_demo: !isDemo })
            });
            await refreshSummary();
          } catch (error) {
            alert(error.message);
          }
        });
      });
    }

    function renderAlerts() {
      $("alert-inbox").innerHTML = app.alerts.slice(0, 20).map((item) => `
        <li class="${item.kind === "alert" ? "alert" : ""}">
          <strong>${escapeHtml(item.patient_name || item.patient_id || "Patient")}</strong>:
          ${escapeHtml(item.summary || "")}
          <time>${formatTime(item.created_at)}</time>
        </li>
      `).join("") || `<li class="muted">No active alerts.</li>`;
    }

    function renderDetailEmpty() {
      $("detail-empty").hidden = false;
      $("detail-content").hidden = true;
      $("patient-json").textContent = "{}";
    }

    function renderDetail(patient) {
      $("detail-empty").hidden = true;
      $("detail-content").hidden = false;
      $("detail-name").textContent = patient.name || "Unknown";
      $("detail-id").textContent = `Patient ID: #PT-${(patient.patient_id || app.selectedId).toUpperCase()}`;
      const moods = patient.mood_history || [];
      const compliance = patient.compliance_history || [];
      const lastMood = moods.length ? moods[moods.length - 1] : null;
      const lastCompliance = compliance.length ? compliance[compliance.length - 1] : null;
      $("detail-status").textContent = "Active monitoring";
      $("detail-mood").textContent = lastMood === null ? "—" : `${lastMood}/10`;
      $("detail-compliance").textContent = lastCompliance === null ? "—" : (lastCompliance ? "Compliant" : "Needs review");
      $("detail-address").textContent = patient.address || "Not recorded";
      $("detail-phone").textContent = patient.phone || "Not recorded";

      const meds = patient.medications || {};
      $("detail-meds").innerHTML = Object.entries(meds).map(([id, med]) => `
        <li class="med-item">
          <div>
            <strong>${escapeHtml(med.name || id)}</strong>
            <div class="muted">${escapeHtml(med.time || "No time set")}</div>
          </div>
          <span class="status ${medStatusClass(med.status)}">${escapeHtml(med.status || "pending")}</span>
        </li>
      `).join("") || `<li class="med-item">No medications recorded.</li>`;

      $("patient-json").textContent = JSON.stringify(patient, null, 2);
    }

    function renderActivity(items) {
      $("detail-activity").innerHTML = items.slice(0, 16).map((item) => {
        const label = item.kind === "alert" ? "Alert" : item.kind === "message" ? "Message" : "Update";
        return `<li><strong>${label}:</strong> ${escapeHtml(item.summary || item.detail || "")}<time>${formatTime(item.created_at)}</time></li>`;
      }).join("") || `<li class="muted">No activity yet.</li>`;
    }

    function fillEditForm(patient) {
      $("edit-name").value = patient?.name || "";
      $("edit-address").value = patient?.address || "";
      $("edit-phone").value = patient?.phone || "";
      $("edit-passcode").value = "";
      $("edit-is-demo").checked = Boolean(patient?.is_demo ?? true);
    }

    async function refreshSummary() {
      const data = await api("/api/provider/summary");
      app.roster = data.patients || [];
      renderRoster();
      if (app.selectedId && !app.roster.some((row) => row.id === app.selectedId)) {
        app.selectedId = "";
        app.patient = null;
        renderDetailEmpty();
        fillEditForm(null);
      }
    }

    async function refreshAlerts() {
      const data = await api("/api/provider/alerts");
      app.alerts = data.items || [];
      renderAlerts();
    }

    async function loadPatientDetail() {
      if (!app.selectedId) {
        renderDetailEmpty();
        return;
      }
      const patient = await api(`/api/patient/${app.selectedId}`);
      if (patient.error) throw new Error(patient.error);
      app.patient = patient;
      renderDetail(patient);
      fillEditForm(patient);
      const activity = await api(`/api/patient/${app.selectedId}/activity`);
      renderActivity(activity.items || []);
    }

    async function selectPatient(patientId) {
      app.selectedId = patientId;
      renderRoster();
      await loadPatientDetail().catch(() => renderDetailEmpty());
    }

    function startPolling() {
      clearInterval(app.pollTimer);
      app.pollTimer = setInterval(() => {
        refreshSummary().catch(() => {});
        refreshAlerts().catch(() => {});
        if (app.selectedId) loadPatientDetail().catch(() => {});
      }, 2000);
    }

    $("provider-form").addEventListener("submit", async (event) => {
      event.preventDefault();
      $("provider-error").textContent = "";
      const passcode = $("provider-passcode").value;
      try {
        const result = await api("/api/provider/verify", {
          method: "POST",
          body: JSON.stringify({ passcode })
        });
        if (!result.success) throw new Error(result.error || "Incorrect passcode");
        sessionStorage.setItem("providerPasscode", passcode);
        $("provider-dialog").close();
        $("provider-passcode").value = "";
        updateProviderSessionButton();
      } catch (error) {
        $("provider-error").textContent = error.message;
      }
    });

    $("provider-unlock-btn").addEventListener("click", () => {
      if (hasProviderPasscode()) {
        logoutProvider();
        return;
      }
      $("provider-dialog").showModal();
    });

    $("create-form").addEventListener("submit", async (event) => {
      event.preventDefault();
      $("create-error").textContent = "";
      if (!hasProviderPasscode()) {
        $("provider-dialog").showModal();
        return;
      }
      try {
        const result = await api("/api/patients", {
          method: "POST",
          headers: providerHeaders(),
          body: JSON.stringify({
            id: $("create-id").value.trim(),
            name: $("create-name").value.trim(),
            address: $("create-address").value.trim(),
            phone: $("create-phone").value.trim(),
            passcode: $("create-passcode").value,
            is_demo: $("create-is-demo").checked
          })
        });
        $("create-form").reset();
        $("create-is-demo").checked = true;
        await refreshSummary();
        if (result.patient?.patient_id) await selectPatient(result.patient.patient_id);
      } catch (error) {
        $("create-error").textContent = error.message;
      }
    });

    $("edit-form").addEventListener("submit", async (event) => {
      event.preventDefault();
      $("edit-error").textContent = "";
      if (!app.selectedId) {
        $("edit-error").textContent = "Select a patient first.";
        return;
      }
      if (!hasProviderPasscode()) {
        $("provider-dialog").showModal();
        return;
      }
      const payload = {
        name: $("edit-name").value.trim() || undefined,
        address: $("edit-address").value.trim(),
        phone: $("edit-phone").value.trim(),
        is_demo: $("edit-is-demo").checked
      };
      const passcode = $("edit-passcode").value;
      if (passcode) payload.passcode = passcode;
      try {
        await api(`/api/patient/${app.selectedId}`, {
          method: "PUT",
          headers: providerHeaders(),
          body: JSON.stringify(payload)
        });
        await refreshSummary();
        await loadPatientDetail();
      } catch (error) {
        $("edit-error").textContent = error.message;
      }
    });

    $("delete-btn").addEventListener("click", async () => {
      if (!app.selectedId) return;
      if (!hasProviderPasscode()) {
        $("provider-dialog").showModal();
        return;
      }
      const name = app.patient?.name || app.selectedId;
      if (!confirm(`Delete patient ${name}? This cannot be undone.`)) return;
      try {
        await api(`/api/patient/${app.selectedId}`, {
          method: "DELETE",
          headers: providerHeaders()
        });
        app.selectedId = "";
        app.patient = null;
        renderDetailEmpty();
        fillEditForm(null);
        await refreshSummary();
        await refreshAlerts();
      } catch (error) {
        $("edit-error").textContent = error.message;
      }
    });

    (async function init() {
      renderDetailEmpty();
      updateProviderSessionButton();
      await refreshSummary();
      await refreshAlerts();
      startPolling();
      if (!hasProviderPasscode()) {
        $("provider-dialog").showModal();
      }
    })();
  </script>
</body>
</html>
"""
