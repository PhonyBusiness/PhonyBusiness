const API = "http://localhost:8000"; // swap for the deployed backend URL
const REFRESH_MS = 5000;

const $ = (id) => document.getElementById(id);

// Chart colors for the dark background (single series per chart).
const ACCENT = "#3987e5";
const INK_MUTED = "#9a9a9a";
const GRID = "#2a2a2a";

// Scenario id -> display name, filled from /scenarios.
let scenarioNames = {};

async function getJson(path) {
  const res = await fetch(`${API}${path}`);
  if (!res.ok) throw new Error(`${path} failed with HTTP ${res.status}`);
  return res.json();
}

const pct = (x) => (x == null ? "–" : `${Math.round(x * 100)}%`);

// ---------- Charts ----------

Chart.defaults.color = INK_MUTED;
Chart.defaults.font.family = getComputedStyle(document.body).fontFamily;

const axes = (yOptions) => ({
  x: { grid: { display: false }, border: { color: GRID } },
  y: { beginAtZero: true, grid: { color: GRID }, border: { display: false }, ...yOptions },
});

const scenarioChart = new Chart($("chart-scenario"), {
  type: "bar",
  data: { labels: [], datasets: [{ data: [], backgroundColor: ACCENT, borderRadius: 4, maxBarThickness: 48 }] },
  options: {
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: { callbacks: { label: (ctx) => `Fail rate: ${pct(ctx.raw)}` } },
    },
    scales: axes({ max: 1, ticks: { callback: (v) => pct(v) } }),
  },
});

const dailyChart = new Chart($("chart-daily"), {
  type: "line",
  data: {
    labels: [],
    datasets: [{ data: [], borderColor: ACCENT, backgroundColor: ACCENT, borderWidth: 2, pointRadius: 4, pointHoverRadius: 6, tension: 0.3 }],
  },
  options: {
    maintainAspectRatio: false,
    interaction: { mode: "index", intersect: false },
    plugins: {
      legend: { display: false },
      tooltip: { callbacks: { label: (ctx) => `Calls: ${ctx.raw}` } },
    },
    scales: axes({ ticks: { precision: 0 } }),
  },
});

// ---------- Rendering ----------

function renderStats(stats) {
  $("stat-total").textContent = stats.total ?? "–";
  $("stat-pass").textContent = pct(stats.pass_rate);
  $("stat-fail").textContent = pct(stats.fail_rate);

  const byScenario = Object.entries(stats.fail_rate_by_scenario || {});
  scenarioChart.data.labels = byScenario.map(([name]) => scenarioNames[name] || name);
  scenarioChart.data.datasets[0].data = byScenario.map(([, rate]) => rate);
  scenarioChart.update();

  const daily = stats.calls_per_day || [];
  dailyChart.data.labels = daily.map((d) =>
    new Date(`${d.date}T00:00:00`).toLocaleDateString(undefined, { month: "short", day: "numeric" }));
  dailyChart.data.datasets[0].data = daily.map((d) => d.count);
  dailyChart.update();
}

function cell(text, className) {
  const td = document.createElement("td");
  if (className) td.className = className;
  td.textContent = text;
  return td;
}

function renderRecent(calls) {
  if (!calls.length) {
    const tr = document.createElement("tr");
    tr.append(Object.assign(cell("No calls yet.", "muted"), { colSpan: 4 }));
    $("recent").replaceChildren(tr);
    return;
  }

  const icons = { pass: "✓", fail: "✕", caution: "!", stopped: "■" };
  $("recent").replaceChildren(...calls.map((call) => {
    const tr = document.createElement("tr");
    const time = call.created_at
      ? new Date(call.created_at).toLocaleString(undefined, { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" })
      : "–";

    const pill = document.createElement("span");
    const result = call.score || call.outcome;
    pill.className = `pill ${result || ""}`;
    pill.textContent = result ? `${icons[result] || ""} ${result.toUpperCase()}` : "IN PROGRESS";
    const resultCell = document.createElement("td");
    resultCell.append(pill);

    tr.append(
      cell(time),
      cell(scenarioNames[call.scenario_name] || call.scenario_name || "–"),
      resultCell,
      cell((call.flags || []).join(", ") || "–"),
    );
    return tr;
  }));
}

// ---------- Refresh loop ----------

async function refresh() {
  const [stats, recent] = await Promise.allSettled([getJson("/stats"), getJson("/stats/recent")]);

  if (stats.status === "fulfilled") renderStats(stats.value);
  if (recent.status === "fulfilled") renderRecent(recent.value);

  const notice = $("notice");
  notice.hidden = stats.status === "fulfilled" && recent.status === "fulfilled";
  notice.textContent = "Stats aren't available yet. Waiting for the backend's /stats endpoints…";
}

async function start() {
  try {
    const scenarios = await getJson("/scenarios");
    scenarioNames = Object.fromEntries(scenarios.map((s) => [s.name, s.display_name]));
  } catch {
    // Fall back to raw scenario ids.
  }
  refresh();
  setInterval(refresh, REFRESH_MS);
}

start();
