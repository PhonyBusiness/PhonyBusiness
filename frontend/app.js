import { Conversation } from "https://cdn.jsdelivr.net/npm/@elevenlabs/client@1.25.0/+esm";

const API = "http://localhost:8000"; // swap for the deployed backend URL

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
  const options = body === undefined
    ? {}
    : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) };
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
  } catch {
    // Keep the hardcoded options in index.html if the backend is unreachable.
  }
}

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
  show("ringing");
  startRingtone();
};

// ---------- Ringing screen ----------

$("btn-decline").onclick = () => {
  stopRingtone();
  show("start");
};

$("btn-accept").onclick = async () => {
  stopRingtone();
  callEnded = false;
  muted = false;
  $("btn-mute").classList.remove("on");
  $("call-status").textContent = "Connecting…";
  show("call");

  try {
    // Ask for mic permission up front, then release it; the SDK opens its own stream.
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    stream.getTracks().forEach((t) => t.stop());
    const session = await Conversation.startSession({
      signedUrl: callData.signed_url,
      dynamicVariables: callData.dynamic_variables,
      onConnect: () => {
        if (callEnded) return;
        $("call-status").textContent = "";
        startTimer();
      },
      onStatusChange: ({ status }) => console.log("[call] status:", status),
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
    $("call-status").textContent = "";
    startTimer();
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
  const c = conversation;
  conversation = null;
  await c?.endSession().catch(() => {});
  showRecap((await hangup) || {});
}

// ---------- Recap screen ----------

function fillList(id, items) {
  $(id).replaceChildren(...items.map((text) => {
    const li = document.createElement("li");
    li.textContent = text;
    return li;
  }));
  $(id).previousElementSibling.hidden = items.length === 0;
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

  const tips = call.tips || [];
  fillList("flags", call.flags || []);
  fillList("dos", tips.map((t) => t.do).filter(Boolean));
  fillList("donts", tips.map((t) => t.dont).filter(Boolean));
}

async function showRecap(initial) {
  renderRecap(initial);
  show("recap");

  // Poll until the post-call re-score lands (up to ~20 seconds).
  const id = callId;
  for (let i = 0; i < 10 && id === callId; i++) {
    try {
      const call = await api(`/calls/${id}`);
      renderRecap(call);
      if (call.score) return;
    } catch {
      // Endpoint may not exist yet; keep trying.
    }
    await new Promise((r) => setTimeout(r, 2000));
  }
  if ($("result-badge").textContent === "…") {
    $("result-text").textContent = "Results aren't available right now.";
  }
}

$("btn-again").onclick = () => {
  callId = null;
  callData = null;
  show("start");
};

loadScenarios();
