const API = "http://localhost:8000"; // swap for the deployed backend URL

const $ = (id) => document.getElementById(id);

// Chart colors for the dark background (single series per chart).
const ACCENT = "#3987e5";
const INK_MUTED = "#9a9a9a";
const GRID = "#2a2a2a";

async function getJson(path) {
  const res = await fetch(`${API}${path}`);
  if (!res.ok) throw new Error(`${path} failed with HTTP ${res.status}`);
  return res.json();
}

const pct = (x) => (x == null ? "–" : `${Math.round(x * 100)}%`);

// "95" -> "1:35"
const clock = (secs) =>
  secs == null ? "–" : `${Math.floor(secs / 60)}:${String(Math.round(secs % 60)).padStart(2, "0")}`;

// Mongo returns UTC datetimes without a zone suffix; treat them as UTC.
const parseUtc = (s) => new Date(/[zZ]|[+-]\d\d:\d\d$/.test(s) ? s : `${s}Z`);

const shortDate = (isoDay) =>
  new Date(`${isoDay}T00:00:00`).toLocaleDateString(undefined, { month: "short", day: "numeric" });

const scenarioName = (scenario) => scenario?.display_name || scenario?.name || "Unknown";

// Show the chart's "no data" message when there's nothing to plot.
function setEmpty(id, isEmpty) {
  $(id).parentElement.querySelector(".empty").hidden = !isEmpty;
}

// Ranked bar list: rows of { label, value (0–1 bar width), note }.
function renderRank(id, rows) {
  $(id).replaceChildren(...rows.map((row) => {
    const li = document.createElement("li");
    const label = document.createElement("div");
    const name = document.createElement("span");
    const note = document.createElement("span");
    const track = document.createElement("div");
    const bar = document.createElement("div");
    label.className = "rank-label";
    note.className = "muted";
    track.className = "rank-track";
    bar.className = "rank-bar";
    name.textContent = row.label;
    note.textContent = row.note;
    bar.style.width = `${Math.round(row.value * 100)}%`;
    label.append(name, note);
    track.append(bar);
    li.append(label, track);
    return li;
  }));
  setEmpty(id, rows.length === 0);
}

// ---------- Charts ----------

Chart.defaults.color = INK_MUTED;
Chart.defaults.font.family = getComputedStyle(document.body).fontFamily;

const axes = (yOptions, xOptions = {}) => ({
  x: { grid: { display: false }, border: { color: GRID }, ...xOptions },
  y: { beginAtZero: true, grid: { color: GRID }, border: { display: false }, ...yOptions },
});

const percentAxis = { max: 1, ticks: { callback: (v) => pct(v) } };

const lineDataset = () => ({
  data: [], borderColor: ACCENT, backgroundColor: ACCENT,
  borderWidth: 2, pointRadius: 4, pointHoverRadius: 6, tension: 0.3, spanGaps: true,
});

const baseOptions = (tooltipLabel) => ({
  maintainAspectRatio: false,
  interaction: { mode: "index", intersect: false },
  plugins: { legend: { display: false }, tooltip: { callbacks: { label: tooltipLabel } } },
});

const passRateChart = new Chart($("chart-passrate"), {
  type: "line",
  data: { labels: [], datasets: [lineDataset()] },
  options: { ...baseOptions((ctx) => `Pass rate: ${pct(ctx.raw)}`), scales: axes(percentAxis) },
});

const dailyChart = new Chart($("chart-daily"), {
  type: "line",
  data: { labels: [], datasets: [lineDataset()] },
  options: { ...baseOptions((ctx) => `Calls: ${ctx.raw}`), scales: axes({ ticks: { precision: 0 } }) },
});

const frustrationTrendChart = new Chart($("chart-frustration-trend"), {
  type: "line",
  data: { labels: [], datasets: [lineDataset()] },
  options: { ...baseOptions((ctx) => `Avg. peak frustration: ${pct(ctx.raw)}`), scales: axes(percentAxis) },
});

const frustrationDistChart = new Chart($("chart-frustration-dist"), {
  type: "bar",
  data: { labels: [], datasets: [{ data: [], backgroundColor: ACCENT, borderRadius: 4, maxBarThickness: 40 }] },
  options: {
    ...baseOptions((ctx) => `${ctx.raw} calls`),
    scales: axes({ ticks: { precision: 0 } }, { title: { display: true, text: "Peak frustration", color: INK_MUTED } }),
  },
});

// Draws a dashed vertical line where the resident made their decision.
let decisionAt = null;
const decisionMarker = {
  id: "decisionMarker",
  afterDatasetsDraw(chart) {
    if (decisionAt == null) return;
    const x = chart.scales.x.getPixelForValue(decisionAt);
    const { top, bottom } = chart.chartArea;
    const ctx = chart.ctx;
    ctx.save();
    ctx.strokeStyle = "#f5f5f5";
    ctx.setLineDash([4, 4]);
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(x, top);
    ctx.lineTo(x, bottom);
    ctx.stroke();
    ctx.fillStyle = "#f5f5f5";
    ctx.font = `12px ${Chart.defaults.font.family}`;
    ctx.textAlign = x > chart.chartArea.right - 60 ? "right" : "left";
    ctx.fillText("Decided", x + (ctx.textAlign === "left" ? 6 : -6), top + 12);
    ctx.restore();
  },
};

const frustrationChart = new Chart($("chart-frustration"), {
  type: "line",
  data: { datasets: [lineDataset()] },
  options: {
    ...baseOptions((ctx) => `Frustration: ${pct(ctx.raw.y)}`),
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          title: (items) => `At ${clock(items[0].raw.x)}`,
          label: (ctx) => `Frustration: ${pct(ctx.raw.y)}`,
        },
      },
    },
    scales: axes(percentAxis, { type: "linear", ticks: { callback: (v) => clock(v) } }),
  },
  plugins: [decisionMarker],
});

// Sentiment runs from -1 (negative) to +1 (positive); 0 is neutral.
const SENTIMENT_TICKS = { "-1": "Negative", "0": "Neutral", "1": "Positive" };
const sentimentWord = (v) => (v > 0.15 ? "positive" : v < -0.15 ? "negative" : "neutral");

const sentimentChart = new Chart($("chart-sentiment"), {
  type: "line",
  data: { datasets: [lineDataset()] },
  options: {
    maintainAspectRatio: false,
    interaction: { mode: "index", intersect: false },
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          title: (items) => `At ${clock(items[0].raw.x)}`,
          label: (ctx) => `Sentiment: ${ctx.raw.y.toFixed(2)} (${sentimentWord(ctx.raw.y)})`,
        },
      },
    },
    scales: {
      x: { type: "linear", grid: { display: false }, border: { color: GRID }, ticks: { callback: (v) => clock(v) } },
      y: {
        min: -1,
        max: 1,
        border: { display: false },
        ticks: { stepSize: 0.5, callback: (v) => SENTIMENT_TICKS[v] ?? "" },
        // Emphasize the neutral line so above/below reads at a glance.
        grid: { color: (ctx) => (ctx.tick.value === 0 ? "#555" : GRID) },
      },
    },
  },
  plugins: [decisionMarker],
});

// ---------- Rendering ----------

// GET /analytics/overview → { calls, pass_rate, fail_rate, avg_decision_turn, ... }
function renderOverview(overview) {
  $("stat-total").textContent = overview.calls ?? "–";
  $("stat-pass").textContent = pct(overview.pass_rate);
  $("stat-fail").textContent = pct(overview.fail_rate);
  $("stat-turn").textContent = overview.avg_decision_turn == null ? "–" : `Turn ${overview.avg_decision_turn}`;
}

// GET /analytics/wellbeing → { stop_rate, peak_frustration_distribution, sentiment_labels, ... }
function renderWellbeing(wellbeing) {
  $("stat-stops").textContent = pct(wellbeing.stop_rate);

  // Buckets arrive as "0.0-0.2"; label them as percentages.
  const buckets = wellbeing.peak_frustration_distribution || [];
  frustrationDistChart.data.labels = buckets.map((b) => {
    const [low, high] = b.range.split("-").map(Number);
    return `${Math.round(low * 100)}–${Math.round(high * 100)}%`;
  });
  frustrationDistChart.data.datasets[0].data = buckets.map((b) => b.calls);
  frustrationDistChart.update();
  setEmpty("chart-frustration-dist", !buckets.some((b) => b.calls > 0));

  // Share of calls per overall sentiment; calls without a label are left out.
  const moods = (wellbeing.sentiment_labels || []).filter((m) => m.value);
  const total = moods.reduce((sum, m) => sum + m.calls, 0);
  renderRank("rank-mood", moods.map((m) => ({
    label: `${m.value[0].toUpperCase()}${m.value.slice(1)}`,
    value: total ? m.calls / total : 0,
    note: `${pct(total ? m.calls / total : null)} · ${m.calls} calls`,
  })));
}

// GET /analytics/trends → [{ date, calls, pass_rate, ... }]
function renderTrends(days) {
  const labels = days.map((d) => shortDate(d.date));

  passRateChart.data.labels = labels;
  passRateChart.data.datasets[0].data = days.map((d) => d.pass_rate);
  passRateChart.update();
  setEmpty("chart-passrate", !days.some((d) => d.pass_rate != null));

  dailyChart.data.labels = labels;
  dailyChart.data.datasets[0].data = days.map((d) => d.calls);
  dailyChart.update();
  setEmpty("chart-daily", days.length === 0);

  frustrationTrendChart.data.labels = labels;
  frustrationTrendChart.data.datasets[0].data = days.map((d) => d.avg_peak_frustration);
  frustrationTrendChart.update();
  setEmpty("chart-frustration-trend", !days.some((d) => d.avg_peak_frustration != null));
}

// GET /analytics/risk → { by_scenario: [...], red_flags: [{ flag, calls, on_fail, on_pass }] }
function renderRisk(risk) {
  // Already sorted by most failures; keep the top 6. Bars scale to the worst flag.
  const flags = (risk.red_flags || []).filter((row) => row.on_fail > 0).slice(0, 6);
  const mostFails = Math.max(...flags.map((row) => row.on_fail), 1);
  renderRank("rank-flags", flags.map((row) => ({
    label: row.flag,
    value: row.on_fail / mostFails,
    note: `${row.on_fail} failed · ${row.on_pass} passed`,
  })));

  // Scenarios with too few calls come back suppressed (privacy) and are left off.
  // Already sorted by fail rate; keep the top 6. Bars show the fail rate itself.
  const scenarios = (risk.by_scenario || [])
    .filter((row) => !row.suppressed && row.fail_rate != null)
    .slice(0, 6);
  renderRank("rank-scenarios", scenarios.map((row) => ({
    label: scenarioName(row),
    value: row.fail_rate,
    note: row.calls == null ? `${pct(row.fail_rate)} failed` : `${pct(row.fail_rate)} failed · ${row.calls} calls`,
  })));
}

function cell(text, className) {
  const td = document.createElement("td");
  if (className) td.className = className;
  td.textContent = text;
  return td;
}

const ICONS = { pass: "✓", fail: "✕", caution: "!", stopped: "■" };

function resultPill(result) {
  const pill = document.createElement("span");
  pill.className = `pill ${result || ""}`;
  pill.textContent = result ? `${ICONS[result] || ""} ${result.toUpperCase()}` : "NO RESULT";
  return pill;
}

// GET /analytics/conversations → [{ conversation_id, scenario, started_at, result, flags }]
function renderRecent(calls) {
  if (!calls.length) {
    const tr = document.createElement("tr");
    tr.append(Object.assign(cell("No calls yet.", "muted"), { colSpan: 4 }));
    $("recent").replaceChildren(tr);
    return;
  }

  $("recent").replaceChildren(...calls.map((call) => {
    const tr = document.createElement("tr");
    tr.className = "clickable";
    tr.tabIndex = 0;
    tr.dataset.id = call.conversation_id;
    tr.onclick = () => showDetail(call.conversation_id);
    tr.onkeydown = (e) => { if (e.key === "Enter") showDetail(call.conversation_id); };
    if (call.conversation_id === selectedId) tr.classList.add("selected");

    const time = call.started_at
      ? parseUtc(call.started_at).toLocaleString(undefined, { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" })
      : "–";
    const resultCell = document.createElement("td");
    resultCell.append(resultPill(call.result));

    tr.append(
      cell(time),
      cell(scenarioName(call.scenario)),
      resultCell,
      cell((call.flags || []).join(", ") || "–"),
    );
    return tr;
  }));
}

// ---------- Call detail ----------

let selectedId = null;

// ElevenLabs termination_reason text; anything else is shown as-is.
const ENDED_BY = {
  "end_call tool was called.": "Agent ended the call",
  "Client disconnected": "Resident hung up",
  "Client disconnected: 1000": "Resident hung up",
};

// GET /analytics/conversations/{id}
async function showDetail(conversationId) {
  selectedId = conversationId;
  document.querySelectorAll("#recent tr").forEach((tr) =>
    tr.classList.toggle("selected", tr.dataset.id === conversationId));

  let call;
  try {
    call = await getJson(`/analytics/conversations/${encodeURIComponent(conversationId)}`);
  } catch {
    $("notice").hidden = false;
    $("notice").textContent = "Couldn't load that call. Try again.";
    return;
  }
  if (selectedId !== conversationId) return; // another row was clicked meanwhile

  const outcome = call.outcome || {};
  $("detail-title").textContent = scenarioName(call.scenario);
  $("detail-sub").textContent = [
    // Difficulty arrives as a word ("medium") or a level number ("2").
    call.difficulty && (/^\d+$/.test(call.difficulty)
      ? `Difficulty ${call.difficulty}`
      : `${call.difficulty[0].toUpperCase()}${call.difficulty.slice(1)} difficulty`),
    call.started_at && parseUtc(call.started_at).toLocaleString(undefined, { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" }),
  ].filter(Boolean).join(" · ");

  $("detail-result").replaceChildren(resultPill(outcome.result));
  $("detail-duration").textContent = clock(call.duration_secs);
  $("detail-decided").textContent = outcome.decided_at_secs == null
    ? "–"
    : `${clock(outcome.decided_at_secs)}${outcome.turn ? ` (turn ${outcome.turn})` : ""}`;
  $("detail-ended").textContent = ENDED_BY[call.termination_reason] || call.termination_reason || "–";

  // Show the panel before drawing: a chart laid out while hidden has zero size.
  $("detail").hidden = false;

  const points = (call.frustration_timeline || [])
    .filter((p) => p.t != null && p.frustration != null)
    .map((p) => ({ x: p.t, y: p.frustration }));
  decisionAt = outcome.decided_at_secs ?? null;
  frustrationChart.data.datasets[0].data = points;
  frustrationChart.options.scales.x.min = 0;
  frustrationChart.options.scales.x.max = call.duration_secs || undefined;
  frustrationChart.resize();
  frustrationChart.update();
  setEmpty("chart-frustration", points.length === 0);

  const sentimentPoints = (call.frustration_timeline || [])
    .filter((p) => p.t != null && p.sentiment != null)
    .map((p) => ({ x: p.t, y: p.sentiment }));
  sentimentChart.data.datasets[0].data = sentimentPoints;
  sentimentChart.options.scales.x.min = 0;
  sentimentChart.options.scales.x.max = call.duration_secs || undefined;
  sentimentChart.resize();
  sentimentChart.update();
  setEmpty("chart-sentiment", sentimentPoints.length === 0);

  $("detail-tips").replaceChildren(...(call.tips || []).map((tip) => {
    const li = document.createElement("li");
    const flag = document.createElement("strong");
    const doText = document.createElement("span");
    const dontText = document.createElement("span");
    flag.textContent = tip.flag;
    doText.textContent = `Do: ${tip.do}`;
    dontText.textContent = `Don't: ${tip.dont}`;
    li.append(flag, doText, dontText);
    return li;
  }));

  $("detail").scrollIntoView({ behavior: "smooth", block: "start" });
}

$("btn-close-detail").onclick = () => {
  selectedId = null;
  $("detail").hidden = true;
  document.querySelectorAll("#recent tr.selected").forEach((tr) => tr.classList.remove("selected"));
};

// ---------- Refresh ----------

async function refresh() {
  $("btn-refresh").disabled = true;
  const results = await Promise.allSettled([
    getJson("/analytics/overview").then(renderOverview),
    getJson("/analytics/wellbeing").then(renderWellbeing),
    getJson("/analytics/risk").then(renderRisk),
    getJson("/analytics/trends?days=30").then(renderTrends),
    getJson("/analytics/conversations?limit=10").then(renderRecent),
  ]);

  const notice = $("notice");
  notice.hidden = results.every((r) => r.status === "fulfilled");
  notice.textContent = "Some stats couldn't be loaded. Try refreshing.";
  $("btn-refresh").disabled = false;
}

$("btn-refresh").onclick = refresh;
refresh();
