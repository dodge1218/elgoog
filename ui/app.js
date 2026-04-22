const state = {
  mode: "centered",
  task: "recover_work",
};

const doctorCards = document.getElementById("doctorCards");
const outputView = document.getElementById("outputView");
const outputSummary = document.getElementById("outputSummary");
const runButton = document.getElementById("runButton");
const refreshDoctor = document.getElementById("refreshDoctor");
const refreshRuns = document.getElementById("refreshRuns");
const promptInput = document.getElementById("promptInput");
const filePathInput = document.getElementById("filePathInput");
const repoPathInput = document.getElementById("repoPathInput");
const githubRepoInput = document.getElementById("githubRepoInput");
const dryRun = document.getElementById("dryRun");
const slotName = document.getElementById("slotName");
const taskLabel = document.getElementById("selectedTaskLabel");
const keyLink = document.getElementById("keyLink");
const artifactView = document.getElementById("artifactView");
const slotRows = document.getElementById("slotRows");
const addSlot = document.getElementById("addSlot");
const saveSlots = document.getElementById("saveSlots");
const slotSaveStatus = document.getElementById("slotSaveStatus");
const runHistory = document.getElementById("runHistory");
const dropZone = document.getElementById("dropZone");
const copyArtifact = document.getElementById("copyArtifact");
const downloadArtifact = document.getElementById("downloadArtifact");
const copyJson = document.getElementById("copyJson");
const runStatusBanner = document.getElementById("runStatusBanner");
const manifestView = document.getElementById("manifestView");
const STORAGE_KEY = "elgoog-ui-state-v1";
let latestDoctorPayload = null;
let latestSlotsPayload = null;

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function renderMarkdown(text) {
  if (!text || !text.trim()) {
    return `<div class="output-empty">No artifact text yet.</div>`;
  }
  const lines = text.replaceAll("\r\n", "\n").split("\n");
  const html = [];
  let inList = false;
  let inCode = false;
  let paragraph = [];

  function flushParagraph() {
    if (!paragraph.length) return;
    html.push(`<p>${paragraph.join(" ")}</p>`);
    paragraph = [];
  }

  function closeList() {
    if (!inList) return;
    html.push(`</ul>`);
    inList = false;
  }

  for (const rawLine of lines) {
    const line = rawLine.trimEnd();
    if (line.startsWith("```")) {
      flushParagraph();
      closeList();
      if (inCode) {
        html.push(`</code></pre>`);
        inCode = false;
      } else {
        html.push(`<pre><code>`);
        inCode = true;
      }
      continue;
    }
    if (inCode) {
      html.push(`${escapeHtml(rawLine)}\n`);
      continue;
    }
    const trimmed = line.trim();
    if (!trimmed) {
      flushParagraph();
      closeList();
      continue;
    }
    if (trimmed.startsWith("#")) {
      flushParagraph();
      closeList();
      const level = Math.min(3, trimmed.match(/^#+/)[0].length);
      const content = escapeHtml(trimmed.replace(/^#+\s*/, ""));
      html.push(`<h${level + 1}>${content}</h${level + 1}>`);
      continue;
    }
    if (trimmed.startsWith("- ") || trimmed.startsWith("* ") || /^\d+\.\s+/.test(trimmed)) {
      flushParagraph();
      if (!inList) {
        html.push(`<ul>`);
        inList = true;
      }
      html.push(`<li>${escapeHtml(trimmed.replace(/^(- |\* |\d+\.\s+)/, ""))}</li>`);
      continue;
    }
    paragraph.push(escapeHtml(trimmed));
  }

  flushParagraph();
  closeList();
  if (inCode) {
    html.push(`</code></pre>`);
  }
  return html.join("");
}

function statusGuidance(payload) {
  const status = payload.status || "";
  const guidance = {
    success: {
      tone: "success",
      title: "Run completed",
      detail: "Artifact and provenance files were written successfully.",
    },
    dry_run: {
      tone: "neutral",
      title: "Dry run only",
      detail: "Nothing was sent to Gemini. Inspect the run record and manifest before a real run.",
    },
    quota: {
      tone: "warn",
      title: "Quota or capacity issue",
      detail: "Try another slot or wait for reset. The failure was classified before the run silently degraded.",
    },
    auth: {
      tone: "error",
      title: "Auth or entitlement issue",
      detail: "Check the slot key, account tier, or API access. This is not a model-quality problem.",
    },
    transient: {
      tone: "warn",
      title: "Transient provider failure",
      detail: "Retry is reasonable. The provider likely timed out or returned a temporary failure.",
    },
    busy: {
      tone: "warn",
      title: "Another run is in progress",
      detail: "Wait for the current run to finish rather than creating duplicate state.",
    },
    error: {
      tone: "error",
      title: "Run failed",
      detail: "Inspect the run record and raw JSON. This was not classified as quota, auth, or transient.",
    },
  };
  return guidance[status] || null;
}

function renderStatusBanner(payload) {
  const guidance = statusGuidance(payload);
  if (!guidance) {
    runStatusBanner.className = "run-status-banner hidden";
    runStatusBanner.textContent = "";
    return;
  }
  runStatusBanner.className = `run-status-banner ${guidance.tone}`;
  runStatusBanner.innerHTML = `<strong>${escapeHtml(guidance.title)}</strong><span>${escapeHtml(guidance.detail)}</span>`;
}

function persistUiState() {
  const payload = {
    mode: state.mode,
    task: state.task,
    prompt: promptInput.value,
    filePath: filePathInput.value,
    repoPath: repoPathInput.value,
    githubRepo: githubRepoInput.value,
    slot: slotName.value,
    dryRun: dryRun.checked,
  };
  localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
}

function restoreUiState() {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) return;
  try {
    const payload = JSON.parse(raw);
    if (payload.mode) setMode(payload.mode);
    if (payload.task) setTask(payload.task);
    promptInput.value = payload.prompt || promptInput.value;
    filePathInput.value = payload.filePath || "";
    repoPathInput.value = payload.repoPath || "";
    githubRepoInput.value = payload.githubRepo || "";
    slotName.value = payload.slot || slotName.value;
    dryRun.checked = payload.dryRun !== false;
  } catch {
    return;
  }
}

function validateRunInput() {
  const hasInput = Boolean(
    promptInput.value.trim() ||
    filePathInput.value.trim() ||
    repoPathInput.value.trim() ||
    githubRepoInput.value.trim(),
  );
  if (hasInput) return true;
  renderStatusBanner({ status: "error" });
  outputSummary.innerHTML = `<div class="output-empty">Add prompt text, a file path, a repo path, or a public GitHub repo URL.</div>`;
  artifactView.innerHTML = `<div class="output-empty">No artifact text yet.</div>`;
  manifestView.textContent = "No provenance yet.";
  outputView.textContent = "Run blocked: no input sources provided.";
  return false;
}

function hasSavedSlots() {
  const slots = Array.isArray(latestSlotsPayload?.slots) ? latestSlotsPayload.slots : [];
  return slots.length > 0;
}

function validateRunSetup() {
  if (dryRun.checked) return true;
  if (hasSavedSlots()) return true;
  renderStatusBanner({ status: "auth" });
  outputSummary.innerHTML = `<div class="output-empty">Save at least one Gemini slot before a real run. Dry runs work without a slot file.</div>`;
  artifactView.innerHTML = `<div class="output-empty">No artifact text yet.</div>`;
  manifestView.textContent = "No provenance yet.";
  outputView.textContent = "Run blocked: no saved Gemini slots configured.";
  return false;
}

function setMode(mode) {
  state.mode = mode;
  document.body.dataset.mode = mode;
  document.querySelectorAll(".mode-button").forEach((button) => {
    button.classList.toggle("active", button.dataset.modeTarget === mode);
  });
  persistUiState();
}

function setTask(task) {
  state.task = task;
  taskLabel.textContent = task;
  document.querySelectorAll(".task-card").forEach((card) => {
    card.classList.toggle("active", card.dataset.task === task);
  });
  persistUiState();
}

function setButtonFeedback(button, label) {
  const original = button.dataset.originalLabel || button.textContent;
  button.dataset.originalLabel = original;
  button.textContent = label;
  window.setTimeout(() => {
    button.textContent = original;
  }, 1200);
}

async function copyText(text, button) {
  if (!text) {
    setButtonFeedback(button, "Nothing to copy");
    return;
  }
  try {
    await navigator.clipboard.writeText(text);
    setButtonFeedback(button, "Copied");
  } catch {
    setButtonFeedback(button, "Copy failed");
  }
}

function downloadText(text, filename) {
  const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function setDropZoneState(active, message = "") {
  dropZone.classList.toggle("active", active);
  if (message) {
    dropZone.dataset.status = message;
  } else {
    delete dropZone.dataset.status;
  }
}

async function loadDroppedFile(file) {
  const text = await file.text();
  promptInput.value = text;
  filePathInput.value = "";
  setDropZoneState(false, `Loaded ${file.name}`);
}

function renderDoctor(payload) {
  latestDoctorPayload = payload;
  const cards = [
    { label: "Slots available", value: String(payload.slots_available ?? 0), detail: payload.slots_path || "No slot file yet" },
    { label: "Default model", value: payload.default_model || "Unknown", detail: "Current run default" },
    { label: "Key creation", value: "Open", detail: payload.key_url || "" },
    { label: "Harness mode", value: "Artifact-first", detail: "Runs log slot, model, and status" },
  ];
  doctorCards.innerHTML = "";
  cards.forEach((card) => {
    const el = document.createElement("article");
    el.className = "doctor-card";
    el.innerHTML = `<div class="task-kicker">${card.label}</div><strong>${card.value}</strong><p>${card.detail}</p>`;
    doctorCards.appendChild(el);
  });
  const slots = Array.isArray(payload.slots) ? payload.slots : [];
  if (slots.length === 0) {
    const empty = document.createElement("article");
    empty.className = "doctor-card doctor-card-setup";
    empty.innerHTML = `
      <div class="task-kicker">Setup</div>
      <strong>No Gemini slots configured</strong>
      <p>Add at least one API key in Slot management, save it locally, then refresh slot health.</p>
      <p>Dry runs still work without a slot file. Real runs do not.</p>
    `;
    doctorCards.appendChild(empty);
  }
  slots.forEach((slot) => {
    const el = document.createElement("article");
    el.className = "doctor-card";
    el.innerHTML = `
      <div class="task-kicker">Slot ${escapeHtml(slot.slot || "unknown")}</div>
      <strong>${escapeHtml(slot.status || "unknown")}</strong>
      <p>${escapeHtml(slot.detail || "")}</p>
      <p>${escapeHtml(slot.masked_key || "")} · ${escapeHtml(slot.source || "")}</p>
    `;
    doctorCards.appendChild(el);
  });
  if (payload.key_url) {
    keyLink.href = payload.key_url;
  }
}

async function loadDoctor() {
  doctorCards.innerHTML = `<article class="doctor-card"><div class="task-kicker">Loading</div><strong>...</strong><p>Checking slot state and key path.</p></article>`;
  const response = await fetch("/api/doctor");
  const payload = await response.json();
  renderDoctor(payload);
}

function addSlotRow(slot = "", apiKey = "") {
  const row = document.createElement("div");
  row.className = "slot-row";
  row.innerHTML = `
    <input class="slot-name-input" type="text" placeholder="slot name" value="${slot}" />
    <input class="slot-key-input" type="password" placeholder="Gemini API key" value="${apiKey}" />
    <button class="slot-remove ghost-button" type="button">Remove</button>
  `;
  row.querySelector(".slot-remove").addEventListener("click", () => row.remove());
  slotRows.appendChild(row);
}

async function loadSlots() {
  const response = await fetch("/api/slots");
  const payload = await response.json();
  latestSlotsPayload = payload;
  slotRows.innerHTML = "";
  const slots = Array.isArray(payload.slots) ? payload.slots : [];
  if (slots.length === 0) {
    addSlotRow("gemini_slot_1", "");
    slotSaveStatus.textContent = "No saved slot file yet";
    return;
  }
  slots.forEach((slot) => addSlotRow(slot.slot || "", slot.api_key || ""));
  slotSaveStatus.textContent = `${slots.length} slot${slots.length === 1 ? "" : "s"} loaded`;
}

async function loadRuns() {
  const response = await fetch("/api/runs");
  const payload = await response.json();
  const runs = Array.isArray(payload.runs) ? payload.runs : [];
  if (runs.length === 0) {
    runHistory.innerHTML = `<div class="output-empty">No runs yet.</div>`;
    return;
  }
  runHistory.innerHTML = runs.map((run) => `
    <button class="run-item" type="button">
      <span class="run-main">${run.task_class || "unknown"} • ${run.status || "unknown"}</span>
      <span class="run-meta">${run.timestamp || ""}</span>
      <span class="run-meta">${run.slot || run.provider_slot || ""}</span>
      <span class="run-meta">${run.output_path || run.artifact || ""}</span>
    </button>
  `).join("");
  runHistory.querySelectorAll(".run-item").forEach((button, index) => {
    button.addEventListener("click", () => renderOutput(runs[index]));
  });
}

async function saveSlotState() {
  const slots = Array.from(slotRows.querySelectorAll(".slot-row")).map((row) => ({
    slot: row.querySelector(".slot-name-input").value.trim(),
    api_key: row.querySelector(".slot-key-input").value.trim(),
  })).filter((slot) => slot.api_key);
  const response = await fetch("/api/slots", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ slots }),
  });
  const payload = await response.json();
  slotSaveStatus.textContent = payload.status === "saved"
    ? `Saved ${payload.count} slot${payload.count === 1 ? "" : "s"}`
    : "Save failed";
  await loadSlots();
  await loadDoctor();
}

function renderOutput(payload) {
  state.lastOutput = payload;
  renderStatusBanner(payload);
  const rows = [
    ["Task", payload.task || state.task],
    ["Task class", payload.task_class || ""],
    ["Status", payload.status || ""],
    ["Slot", payload.slot || payload.provider_slot || ""],
    ["Model", payload.model || ""],
    ["Source mode", payload.source_mode || ""],
    ["Resolved input", payload.resolved_input_chars || ""],
    ["Input hash", payload.resolved_input_sha256 || ""],
    ["File", payload.input_file_path || ""],
    ["Repo", payload.input_repo_path || ""],
    ["GitHub repo", payload.input_github_repo_url || ""],
    ["Run record", payload.run_record || payload.artifact || ""],
    ["Manifest", payload.source_manifest || ""],
    ["Output", payload.output_path || ""],
  ].filter(([, value]) => value);
  outputSummary.innerHTML = rows.map(([label, value]) => `
    <div class="summary-row">
      <span class="summary-label">${label}</span>
      <span class="summary-value">${value}</span>
    </div>
  `).join("");
  artifactView.innerHTML = renderMarkdown(payload.output_text || "");
  manifestView.textContent = payload.source_manifest_text || "No provenance yet.";
  outputView.textContent = JSON.stringify(payload, null, 2);
}

async function runTask() {
  if (!validateRunInput()) return;
  if (!validateRunSetup()) return;
  outputView.textContent = "Running...";
  runStatusBanner.className = "run-status-banner neutral";
  runStatusBanner.innerHTML = "<strong>Running</strong><span>The local runtime is building an artifact-backed run.</span>";
  outputSummary.innerHTML = `<div class="output-empty">Running task...</div>`;
  artifactView.innerHTML = `<div class="output-empty">Running task...</div>`;
  manifestView.textContent = "Collecting provenance...";
  runButton.disabled = true;
  persistUiState();
  try {
    const response = await fetch("/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        task: state.task,
        text: promptInput.value,
        file_path: filePathInput.value,
        repo_path: repoPathInput.value,
        github_repo_url: githubRepoInput.value,
        slot: slotName.value.trim() || "gemini_slot_1",
        dry_run: dryRun.checked,
      }),
    });
    const payload = await response.json();
    renderOutput(payload);
    loadRuns();
  } catch (error) {
    renderStatusBanner({ status: "error" });
    outputSummary.innerHTML = `<div class="output-empty">Run failed.</div>`;
    artifactView.innerHTML = `<div class="output-empty">Run failed.</div>`;
    manifestView.textContent = "No provenance yet.";
    outputView.textContent = `Run failed\n\n${String(error)}`;
  } finally {
    runButton.disabled = false;
  }
}

document.querySelectorAll(".mode-button").forEach((button) => {
  button.addEventListener("click", () => setMode(button.dataset.modeTarget));
});

document.querySelectorAll(".task-card").forEach((card) => {
  card.addEventListener("click", () => setTask(card.dataset.task));
});

runButton.addEventListener("click", runTask);
refreshDoctor.addEventListener("click", loadDoctor);
refreshRuns.addEventListener("click", loadRuns);
addSlot.addEventListener("click", () => addSlotRow("", ""));
saveSlots.addEventListener("click", saveSlotState);

["dragenter", "dragover"].forEach((eventName) => {
  dropZone.addEventListener(eventName, (event) => {
    event.preventDefault();
    setDropZoneState(true);
  });
});

["dragleave", "dragend", "drop"].forEach((eventName) => {
  dropZone.addEventListener(eventName, (event) => {
    event.preventDefault();
    if (eventName !== "drop") {
      setDropZoneState(false);
    }
  });
});

dropZone.addEventListener("drop", async (event) => {
  const [file] = Array.from(event.dataTransfer?.files || []);
  if (!file) {
    setDropZoneState(false);
    return;
  }
  try {
    await loadDroppedFile(file);
  } catch (error) {
    setDropZoneState(false, "Could not read dropped file");
    outputView.textContent = `File load failed\n\n${String(error)}`;
  }
});

promptInput.value = `Repo summary:\n- multiple unfinished branches\n- docs and TODOs are scattered\n- need the next three bounded tasks and missing context\n\nCurrent blocker:\n- auth and quota behavior are confusing`;
filePathInput.value = "";
repoPathInput.value = "";
githubRepoInput.value = "";
setDropZoneState(false);

setMode("centered");
setTask("recover_work");
restoreUiState();
renderStatusBanner({});
loadDoctor();
loadSlots();
loadRuns();

["input", "change"].forEach((eventName) => {
  [promptInput, filePathInput, repoPathInput, githubRepoInput, slotName, dryRun].forEach((node) => {
    node.addEventListener(eventName, persistUiState);
  });
});

copyArtifact.addEventListener("click", async () => {
  await copyText(state.lastOutput?.output_text || "", copyArtifact);
});

copyJson.addEventListener("click", async () => {
  const text = state.lastOutput ? JSON.stringify(state.lastOutput, null, 2) : "";
  await copyText(text, copyJson);
});

downloadArtifact.addEventListener("click", () => {
  const text = state.lastOutput?.output_text || "";
  if (!text) {
    setButtonFeedback(downloadArtifact, "Nothing to save");
    return;
  }
  const task = state.lastOutput?.task || state.task || "artifact";
  downloadText(text, `${task}.md`);
  setButtonFeedback(downloadArtifact, "Saved");
});
