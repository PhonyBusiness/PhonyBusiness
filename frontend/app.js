import { Conversation } from "https://cdn.jsdelivr.net/npm/@elevenlabs/client@1.25.0/+esm";

const API = "https://clapped-boondocks-basics.ngrok-free.dev"; // swap for the deployed backend URL

const $ = (id) => document.getElementById(id);

// Current call state
let callId = null;
let callData = null;
let conversation = null;
let timerInterval = null;
let muted = false;
let callEnded = false;

// Show exactly one screen: "start", "ringing", "call", or "recap".
function show(name) {
  document.querySelectorAll(".screen").forEach((el) => {
    el.hidden = el.id !== `screen-${name}`;
  });
}

async function api(path, body) {
  // ngrok's free tier serves an HTML warning page to browsers unless this header is sent.
  const headers = { "ngrok-skip-browser-warning": "true" };
  const options = body === undefined
    ? { headers }
    : { method: "POST", headers: { ...headers, "Content-Type": "application/json" }, body: JSON.stringify(body) };
  const res = await fetch(`${API}${path}`, options);
  if (!res.ok) throw new Error(`${path} failed with HTTP ${res.status}`);
  return res.json();
}

// ---------- Ringtone (generated, no audio file needed) ----------

let ringCtx = null;
let ringInterval = null;

function startRingtone() {
  ringCtx = new AudioContext();
  const ring = () => {
    const osc = ringCtx.createOscillator();
    const gain = ringCtx.createGain();
    osc.frequency.value = 440;
    gain.gain.value = 0.15;
    osc.connect(gain).connect(ringCtx.destination);
    osc.start();
    osc.stop(ringCtx.currentTime + 1);
  };
  ring();
  ringInterval = setInterval(ring, 3000);
}

function stopRingtone() {
  clearInterval(ringInterval);
  ringCtx?.close();
  ringCtx = null;
}

// ---------- Start screen ----------

async function loadScenarios() {
  try {
    const scenarios = await api("/scenarios");
    $("scenario").replaceChildren(...scenarios.map((s) => new Option(s.display_name, s.name)));
  } catch (err) {
    // Keep the hardcoded options in index.html if the backend is unreachable.
    console.warn("Couldn't load scenarios:", err);
  }
}

// ---------- Mascots ----------
// The gator gets one step more evil for each detail filled in (0-3).

const SCENARIO_LINES = {
  benefits_imposter: "Your benefits are *very* important to me…",
  tech_support: "Your computer has a virus. Probably.",
  family_emergency: "Grandma? It's me… your grandson!",
  tax_debt: "You owe taxes. Lots of them. Pay me.",
  jury_duty_warrant: "Missed jury duty? Tsk tsk. There's a fine…",
  bank_fraud_alert: "Your bank account is in danger… from me.",
  order_refund: "About that order you never placed…",
  utility_shutoff: "Nice lights you have. Shame if they went off.",
  prize_sweepstakes: "Congratulations! You've won… a scam!",
  health_benefits_card: "Your new health card just needs a few details…",
  debt_relief: "Lower interest? Oh, I'll lower something…",
  investment_opportunity: "Guaranteed returns. Trust me. Heh.",
  phone_carrier: "Just read me that little code we sent…",
};

const DIFFICULTY = {
  easy: { hint: "A clumsy scammer. The red flags are easy to spot.", line: "I'll go easy on you… for now." },
  medium: { hint: "A smooth talker. Stay sharp.", line: "Let's make this interesting…" },
  hard: { hint: "A ruthless pro. Pressure, urgency, no mercy.", line: "Heh heh heh. No mercy." },
};

const touched = { scenario: false, difficulty: false };

function gatorLine(field, name) {
  if (field === "name" && name) return `${name}… what a lovely name.`;
  if (field === "scenario") return SCENARIO_LINES[$("scenario").value] || "Oh, I have just the story for you…";
  if (field === "difficulty") return DIFFICULTY[$("difficulty").value]?.line;
  return "Hmm… who's there?";
}

function updateGator(field) {
  const name = $("name").value.trim();
  // One step more evil per detail (name, scenario, difficulty): looks 0–3.
  $("stage").dataset.level = (name ? 1 : 0) + touched.scenario + touched.difficulty;
  const bubble = $("gator-line");
  bubble.textContent = gatorLine(field, name);
  bubble.classList.remove("pop");
  void bubble.offsetWidth; // restart the pop animation
  bubble.classList.add("pop");
}

function applyDifficulty() {
  const d = $("difficulty").value;
  document.body.dataset.difficulty = d;
  $("difficulty-hint").textContent = DIFFICULTY[d]?.hint || "";
}

$("name").addEventListener("input", () => updateGator("name"));
$("scenario").addEventListener("change", () => {
  touched.scenario = true;
  updateGator("scenario");
});
$("difficulty").addEventListener("change", () => {
  touched.difficulty = true;
  applyDifficulty();
  updateGator("difficulty");
  if ($("difficulty").value === "hard") {
    const stage = $("stage");
    stage.classList.remove("shake");
    void stage.offsetWidth;
    stage.classList.add("shake");
  }
});
applyDifficulty();

$("btn-start").onclick = async () => {
  const firstName = $("name").value.trim();
  if (!firstName) {
    $("start-error").textContent = "Please enter your first name.";
    return;
  }
  $("start-error").textContent = "";
  $("btn-start").disabled = true;

  try {
    callData = await api("/calls/start", {
      first_name: firstName,
      scenario: $("scenario").value,
      difficulty: $("difficulty").value,
    });
    callId = callData.call_id;
  } catch {
    $("start-error").textContent = "Couldn't start the call. Please try again.";
    return;
  } finally {
    $("btn-start").disabled = false;
  }

  const callerName = callData.caller_name || "Unknown caller";
  document.querySelectorAll(".caller-name").forEach((el) => (el.textContent = callerName));
  const ringLine = $("ring-line");
  ringLine.textContent = callData.caller_name
    ? `Hello! This is… definitely ${callerName}.`
    : "Hello! Totally not a scammer here.";
  ringLine.classList.remove("pop");
  void ringLine.offsetWidth; // restart the pop animation
  ringLine.classList.add("pop");
  show("ringing");
  startRingtone();
};

// ---------- Ringing screen ----------

const SVG_NS = "http://www.w3.org/2000/svg";

// Parse an SVG snippet into nodes that can be inserted into an existing <svg>.
function svgNodes(markup) {
  const doc = new DOMParser().parseFromString(`<svg xmlns="${SVG_NS}">${markup}</svg>`, "image/svg+xml");
  return [...doc.documentElement.childNodes];
}

// Copy the start-screen gator and resident onto the ringing screen, then dress them up.
function buildRingStage() {
  const [gatorSrc, residentSrc] = document.querySelectorAll("#stage .cast svg");
  const gator = gatorSrc.cloneNode(true);
  const resident = residentSrc.cloneNode(true);

  // Clip-path ids must stay unique in the page.
  gator.querySelectorAll("[id]").forEach((el) => {
    const oldId = el.id;
    el.id = `${oldId}-ring`;
    gator.querySelectorAll(`[clip-path="url(#${oldId})"]`).forEach((user) =>
      user.setAttribute("clip-path", `url(#${oldId}-ring)`));
  });

  // Disguise: cap behind the brows, fake mustache above the mouth.
  const head = gator.querySelector(".g-head");
  svgNodes(`
    <path class="g-cap" d="M42 28 Q44 2 80 2 Q116 2 118 28Z"/>
    <rect class="g-cap-brim" x="34" y="24" width="92" height="8" rx="4"/>
    <circle class="g-badge" cx="80" cy="15" r="6"/>`).forEach((node) => head.insertBefore(node, head.querySelector(".g-brow-l")));
  svgNodes(`<path class="g-stache" d="M56 92 Q68 84 80 90 Q92 84 104 92 Q94 99 80 94 Q66 99 56 92Z"/>`)
    .forEach((node) => head.insertBefore(node, head.querySelector(".g-mouth")));

  // Phone held to the ear facing the caller, with vibration marks.
  svgNodes(`
    <g class="e-phone">
      <rect x="30" y="64" width="16" height="28" rx="3" fill="#1c1c1c" stroke="#555" stroke-width="1.5"/>
      <rect x="33" y="68" width="10" height="16" rx="1" fill="#3987e5"/>
      <circle cx="40" cy="96" r="8" fill="#f6cfa8"/>
    </g>
    <path class="e-buzz" d="M24 68 Q20 76 24 84"/>
    <path class="e-buzz" d="M17 64 Q11 76 17 88"/>`).forEach((node) => resident.querySelector(".e-body").append(node));

  $("ring-cast").replaceChildren(gator, resident);
}

buildRingStage();

// ---------- In-call cast ----------

// Same disguised gator and resident as the ringing screen, phone held still.
function buildCallStage() {
  const [gator, resident] = [...$("ring-cast").children].map((svg) => svg.cloneNode(true));

  gator.querySelectorAll("[id]").forEach((el) => {
    const oldId = el.id;
    el.id = oldId.replace(/-ring$/, "-call");
    gator.querySelectorAll(`[clip-path="url(#${oldId})"]`).forEach((user) =>
      user.setAttribute("clip-path", `url(#${el.id})`));
  });

  resident.querySelectorAll(".e-buzz").forEach((el) => el.remove());
  svgNodes(`
    <ellipse class="e-talk" cx="80" cy="105" rx="7" ry="5"/>
    <g class="e-zip">
      <path class="e-line" d="M68 105 L92 105"/>
      <path class="e-line" d="M72 101 L72 109 M78 101 L78 109 M84 101 L84 109 M90 101 L90 109" stroke-width="2"/>
    </g>`).forEach((node) => resident.querySelector(".e-body").append(node));

  $("call-cast").replaceChildren(gator, resident);
}

buildCallStage();

let agentMode = "listening";
let volumeInterval = null;

function updateCallStatus() {
  if (!conversation) return; // still "Connecting…" or an error message
  $("call-status").textContent = muted
    ? "🎙 You're muted"
    : agentMode === "speaking" ? "🐊 Caller is talking…" : "👂 Caller is listening…";
}

// ElevenLabs reports whether the agent is speaking or listening.
function setAgentMode(mode) {
  agentMode = mode;
  const stage = $("call-stage");
  stage.classList.toggle("talking", mode === "speaking");
  stage.classList.toggle("listening", mode !== "speaking");
  stage.dataset.level = mode === "speaking" ? 2 : 1;
  updateCallStatus();
}

// Move the resident's mouth while the microphone picks up your voice.
function startVolumeWatch() {
  stopVolumeWatch();
  volumeInterval = setInterval(() => {
    const volume = conversation?.getInputVolume() ?? 0;
    $("call-stage").classList.toggle("user-talking", !muted && volume > 0.08);
  }, 100);
}

function stopVolumeWatch() {
  clearInterval(volumeInterval);
  volumeInterval = null;
  $("call-stage").classList.remove("user-talking");
}

function resetCallStage() {
  $("call-stage").classList.remove("muted", "user-talking");
  setAgentMode("listening");
}

$("btn-decline").onclick = () => {
  stopRingtone();
  show("start");
};

$("btn-accept").onclick = async () => {
  stopRingtone();
  callEnded = false;
  muted = false;
  $("btn-mute").classList.remove("on");
  $("timer").textContent = "00:00";
  resetCallStage();
  $("call-status").textContent = "Connecting…";
  show("call");

  try {
    // Ask for mic permission up front, then release it; the SDK opens its own stream.
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    stream.getTracks().forEach((t) => t.stop());
    const session = await Conversation.startSession({
      signedUrl: callData.signed_url,
      dynamicVariables: callData.dynamic_variables,
      ...(callData.voice_id && { overrides: { tts: { voiceId: callData.voice_id } } }),
      onConnect: () => {
        if (callEnded) return;
        $("call-status").textContent = "";
        startTimer();
      },
      onStatusChange: ({ status }) => console.log("[call] status:", status),
      onModeChange: ({ mode }) => setAgentMode(mode),
      onDisconnect: (details) => {
        // When the agent ends the call (after a fail, pass, or safe word), mark it
        // ended so the recap gets tips. The backend keeps any recorded outcome.
        const hangup = details?.reason === "agent" && !callEnded
          ? api(`/calls/${callId}/hangup`, {}).catch(() => null)
          : null;
        endCall(hangup);
      },
      onError: () => ($("call-status").textContent = "Connection problem"),
    });
    // The user may have hung up while we were still connecting.
    if (callEnded) {
      session.endSession().catch(() => {});
      return;
    }
    conversation = session;
    // Connected: make sure the timer runs even if onConnect didn't fire.
    startTimer();
    updateCallStatus();
    startVolumeWatch();
    // Let the backend match the post-call webhook to this call.
    api(`/calls/${callId}/session`, { conversation_id: conversation.getId() }).catch(() => {});
  } catch {
    $("call-status").textContent = "Couldn't connect. Check microphone access.";
    setTimeout(() => endCall(), 2000);
  }
};

// ---------- In-call screen ----------

function startTimer() {
  if (timerInterval) return; // already running
  const started = Date.now();
  $("timer").textContent = "00:00";
  timerInterval = setInterval(() => {
    const s = Math.floor((Date.now() - started) / 1000);
    $("timer").textContent = `${String(Math.floor(s / 60)).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}`;
  }, 1000);
}

$("btn-mute").onclick = () => {
  muted = !muted;
  conversation?.setMicMuted(muted);
  $("btn-mute").classList.toggle("on", muted);
  $("call-stage").classList.toggle("muted", muted);
  if (muted) $("call-stage").classList.remove("user-talking");
  updateCallStatus();
};

$("btn-hangup").onclick = () => {
  // Hanging up on a scammer counts as a pass; the backend records that
  // and returns the call's outcome, which the recap can show right away.
  const hangup = api(`/calls/${callId}/hangup`, {}).catch(() => null);
  endCall(hangup);
};

// Runs once, whether the user hung up or the agent ended the call.
async function endCall(hangup = null) {
  if (callEnded) return;
  callEnded = true;
  clearInterval(timerInterval);
  timerInterval = null;
  $("timer").textContent = "00:00";
  stopVolumeWatch();
  const c = conversation;
  conversation = null;
  await c?.endSession().catch(() => {});
  showRecap((await hangup) || {});
}

// ---------- Recap screen ----------

// Ending scene: the disguised gator and the resident, reacting to the result.
function buildRecapStage() {
  const [gator, resident] = [...$("ring-cast").children].map((svg) => svg.cloneNode(true));
  gator.querySelectorAll("[id]").forEach((el) => {
    const oldId = el.id;
    el.id = oldId.replace(/-ring$/, "-recap");
    gator.querySelectorAll(`[clip-path="url(#${oldId})"]`).forEach((user) =>
      user.setAttribute("clip-path", `url(#${el.id})`));
  });
  resident.querySelectorAll(".e-buzz").forEach((el) => el.remove());
  $("recap-cast").replaceChildren(gator, resident);
}

buildRecapStage();

const ENDINGS = {
  pass: { scene: "win", level: 0, line: "Curses! Foiled again…" },
  fail: { scene: "lose", level: 3, line: "Gotcha! Don't worry — it was just practice." },
  caution: { scene: "lose", level: 2, line: "So close! Next time, I'll get you." },
  stopped: { scene: "stopped", level: 1, line: "Fine, fine. Good call ending it." },
};

let recapScene = null;

// Only replay the scene's animation when the result actually changes.
function setRecapScene(outcome) {
  const ending = ENDINGS[outcome];
  const scene = ending?.scene || null;
  if (scene === recapScene) return;
  recapScene = scene;

  const stage = $("recap-stage");
  stage.classList.remove("win", "lose", "stopped");
  void stage.offsetWidth; // restart animations
  if (scene) stage.classList.add(scene);
  stage.dataset.level = ending?.level ?? 1;

  const line = $("recap-line");
  line.hidden = !ending;
  line.textContent = ending?.line || "";
}

function listItems(id, items, build) {
  $(id).replaceChildren(...items.map((item) => {
    const li = document.createElement("li");
    build(li, item);
    return li;
  }));
}

function renderRecap(call) {
  const outcome = call.score || call.outcome;
  const badge = $("result-badge");
  badge.className = "badge";
  if (outcome === "pass" || outcome === "fail" || outcome === "caution") {
    badge.classList.add(outcome);
    badge.textContent = outcome.toUpperCase();
  } else if (outcome === "stopped") {
    badge.textContent = "STOPPED";
  } else {
    badge.textContent = "…";
  }

  const text = {
    pass: "Nice work — you didn't give the caller what they wanted.",
    fail: "The caller got what they wanted. Here's how to spot it next time.",
    caution: "You held on, but a few moments were risky.",
    stopped: "You ended the practice call with the safe word.",
  };
  $("result-text").textContent = text[outcome] || "Loading your results…";
  setRecapScene(outcome);

  const flags = call.flags || [];
  listItems("flag-chips", flags, (li, flag) => (li.textContent = flag));
  $("flags-section").hidden = flags.length === 0;

  // Each tip becomes one card: what to do, then what not to do.
  // The backend's "dont" text already starts with "Don't", so icons are enough.
  const tips = (call.tips || []).filter((t) => t.do || t.dont);
  listItems("tip-cards", tips, (li, tip) => {
    for (const [icon, text] of [["✅", tip.do], ["🚫", tip.dont]]) {
      if (!text) continue;
      const p = document.createElement("p");
      p.textContent = `${icon} ${text}`;
      li.append(p);
    }
  });
  $("tips-section").hidden = tips.length === 0;
}

async function showRecap(initial) {
  recapScene = null;
  renderRecap(initial);
  show("recap");

  // Fetch the result once the call is ended. Usually the first request is enough;
  // retry briefly (up to 3 times) only if the hangup hasn't been recorded yet.
  const id = callId;
  for (let i = 0; i < 3 && id === callId; i++) {
    try {
      const call = await api(`/calls/${id}`);
      renderRecap(call);
      if (call.status === "ended" && call.outcome) return;
    } catch {
      // Network hiccup; try again.
    }
    await new Promise((r) => setTimeout(r, 2000));
  }
  if ($("result-badge").textContent === "…") {
    $("result-text").textContent = "Results aren't available right now.";
  }
}

// ---------- Next steps ----------

// Another scenario: preselect the next one in the list and let the user start.
$("btn-again").onclick = () => {
  const select = $("scenario");
  select.selectedIndex = (select.selectedIndex + 1) % select.options.length;
  select.dispatchEvent(new Event("change"));
  callId = null;
  callData = null;
  show("start");
};

loadScenarios();
