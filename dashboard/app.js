const DASHBOARD_PASSWORD = "1qazxcvbnm,./";
const DASHBOARD_AUTH_KEY = "mqquant_dashboard_authenticated";

const GITHUB_OWNER = "Hsu7183";
const GITHUB_REPO = "mqquant-research-engine";
const BRANCH = "main";
const LATEST_REPORT_PATH = "runs/latest/reports/ranking.json";
const GITHUB_REPORT_URL =
  `https://raw.githubusercontent.com/${GITHUB_OWNER}/${GITHUB_REPO}/${BRANCH}/${LATEST_REPORT_PATH}`;
const LOCAL_REPORT_URL = "sample_ranking.json";
const GITHUB_DETAILS_BASE_URL =
  `https://raw.githubusercontent.com/${GITHUB_OWNER}/${GITHUB_REPO}/${BRANCH}/runs/latest/reports/details`;
const LOCAL_DETAILS_BASE_URL = "../runs/latest/reports/details";

const fallbackReport = {
  run_id: "20260506_sample_batch001",
  generated_at: "2026-05-06T00:00:00+00:00",
  summary: {
    total_strategies: 10,
    valid_strategies: 10,
  },
  top_10: [
    {
      rank: 1,
      strategy_name: "0313plus_EB2_DB1_ATRS1p5_ATRTP2_TS20_IDX7",
      score: 93.52,
      total_test_net_profit: 128000,
      pass_rate: 0.83,
      max_test_mdd: 8700,
      average_test_pf: 1.72,
    },
  ],
  all_results: [],
};

let currentView = "ranking";
let currentReport = null;
let currentSource = { dataSource: "", sourceUrl: "" };
let scoreChart = null;
let profitChart = null;
let detailEquityChart = null;
let detailPeriodChart = null;
let devtoolsTriggered = false;

document.addEventListener("DOMContentLoaded", () => {
  installFrontendFriction();
  bindAccessGate();
  if (isAuthenticated()) {
    showDashboard();
  } else {
    showAccessGate();
  }
});

function installFrontendFriction() {
  document.addEventListener("contextmenu", blockEvent, { capture: true });
  document.addEventListener("selectstart", blockEvent, { capture: true });
  document.addEventListener("dragstart", blockEvent, { capture: true });
  document.addEventListener("copy", blockEvent, { capture: true });
  document.addEventListener("cut", blockEvent, { capture: true });

  document.addEventListener(
    "keydown",
    (event) => {
      const key = (event.key || "").toUpperCase();
      const blocked =
        event.key === "F12" ||
        (event.ctrlKey && ["U", "S", "P"].includes(key)) ||
        (event.ctrlKey && event.shiftKey && ["I", "J"].includes(key));

      if (blocked) {
        event.preventDefault();
        resetAuthToGate();
      }
    },
    { capture: true },
  );

  window.addEventListener("resize", detectDevtools);
  setInterval(detectDevtools, 1500);
}

function blockEvent(event) {
  event.preventDefault();
}

function detectDevtools() {
  if (!isAuthenticated() || devtoolsTriggered) {
    return;
  }

  const widthGap = Math.abs(window.outerWidth - window.innerWidth);
  const heightGap = Math.abs(window.outerHeight - window.innerHeight);
  if (widthGap > 240 || heightGap > 240) {
    devtoolsTriggered = true;
    resetAuthToGate();
    setTimeout(() => {
      devtoolsTriggered = false;
    }, 1200);
  }
}

function bindAccessGate() {
  document.getElementById("enter-button").addEventListener("click", handleLogin);
  document.getElementById("logout-button").addEventListener("click", resetAuthToGate);
  document.getElementById("back-button").addEventListener("click", () => showView("ranking"));
  document.getElementById("password-input").addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      handleLogin();
    }
  });
}

function isAuthenticated() {
  return localStorage.getItem(DASHBOARD_AUTH_KEY) === "1";
}

function handleLogin() {
  const passwordInput = document.getElementById("password-input");
  const loginError = document.getElementById("login-error");
  const value = passwordInput.value.trim();

  if (value === DASHBOARD_PASSWORD) {
    localStorage.setItem(DASHBOARD_AUTH_KEY, "1");
    loginError.textContent = "";
    passwordInput.value = "";
    showDashboard();
    return;
  }

  loginError.textContent = "密碼錯誤，請重新輸入";
  passwordInput.select();
}

function resetAuthToGate() {
  localStorage.removeItem(DASHBOARD_AUTH_KEY);
  showAccessGate();
}

function showAccessGate() {
  currentView = "ranking";
  document.title = "入口";
  document.getElementById("access-gate").classList.remove("hidden");
  document.getElementById("app-shell").classList.add("hidden");
  document.getElementById("password-input").value = "";
  document.getElementById("login-error").textContent = "";
  setTimeout(() => document.getElementById("password-input").focus(), 0);
}

function showDashboard() {
  document.title = "三劍客量化科技｜策略排行榜";
  document.getElementById("access-gate").classList.add("hidden");
  document.getElementById("app-shell").classList.remove("hidden");
  showView("ranking");
  if (currentReport) {
    renderDashboard(currentReport, currentSource.dataSource, currentSource.sourceUrl);
  } else {
    loadAndRenderDashboard();
  }
}

function showView(view) {
  currentView = view;
  document.getElementById("ranking-view").classList.toggle("hidden", view !== "ranking");
  document.getElementById("detail-view").classList.toggle("hidden", view !== "detail");
}

function loadAndRenderDashboard() {
  loadLatestReport()
    .then(({ report, dataSource, sourceUrl }) => {
      validateReportSchema(report);
      currentReport = report;
      currentSource = { dataSource, sourceUrl };
      renderDashboard(report, dataSource, sourceUrl);
    })
    .catch((error) => {
      console.warn(error);
      currentReport = fallbackReport;
      currentSource = {
        dataSource: "內建備援",
        sourceUrl: "inline fallbackReport",
      };
      renderStatus("GitHub 與本地 ranking JSON 皆載入失敗，改用內建備援資料。", true);
      renderDashboard(fallbackReport, currentSource.dataSource, currentSource.sourceUrl);
    });
}

async function loadLatestReport() {
  try {
    return {
      report: await loadReport(GITHUB_REPORT_URL),
      dataSource: "GitHub",
      sourceUrl: GITHUB_REPORT_URL,
    };
  } catch (githubError) {
    console.warn("GitHub ranking JSON failed to load; falling back to local sample.", githubError);
    return {
      report: await loadReport(LOCAL_REPORT_URL),
      dataSource: "本地範例",
      sourceUrl: LOCAL_REPORT_URL,
    };
  }
}

async function loadReport(url) {
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Failed to load report: ${response.status}`);
  }
  return response.json();
}

function validateReportSchema(report) {
  const rootFields = ["run_id", "generated_at", "summary", "top_10", "all_results"];
  for (const field of rootFields) {
    if (!(field in report)) {
      throw new Error(`Missing report field: ${field}`);
    }
  }

  if (typeof report.run_id !== "string") throw new Error("run_id must be a string");
  if (typeof report.generated_at !== "string") {
    throw new Error("generated_at must be a string");
  }
  if (!Array.isArray(report.top_10)) throw new Error("top_10 must be an array");
  if (!Array.isArray(report.all_results)) throw new Error("all_results must be an array");

  const summary = report.summary;
  if (!summary || typeof summary !== "object" || Array.isArray(summary)) {
    throw new Error("summary must be an object");
  }
  if (!Number.isInteger(summary.total_strategies)) {
    throw new Error("summary.total_strategies must be an integer");
  }
  if (!Number.isInteger(summary.valid_strategies)) {
    throw new Error("summary.valid_strategies must be an integer");
  }

  for (const item of report.top_10) {
    validateRankingItem(item);
  }
  for (const item of report.all_results) {
    validateRankingItem(item);
  }
}

function validateRankingItem(item) {
  const numericFields = [
    "rank",
    "score",
    "total_test_net_profit",
    "pass_rate",
    "max_test_mdd",
    "average_test_pf",
  ];
  if (typeof item.strategy_name !== "string") {
    throw new Error("strategy_name must be a string");
  }
  for (const field of numericFields) {
    if (typeof item[field] !== "number" || Number.isNaN(item[field])) {
      throw new Error(`${field} must be numeric`);
    }
  }
}

function renderDashboard(report, dataSource, sourceUrl) {
  const top10 = report.top_10.slice(0, 10);
  document.getElementById("run-id").textContent = report.run_id;
  document.getElementById("generated-at").textContent = formatDateTime(report.generated_at);
  document.getElementById("summary").textContent =
    `${report.summary.valid_strategies} / ${report.summary.total_strategies}`;
  document.getElementById("data-source").textContent = dataSource;

  renderStatus(`已載入 ${top10.length} 筆 Top10 策略資料：${sourceUrl}`, false);
  renderTable(top10);
  renderCharts(top10);
}

function renderStatus(message, isError) {
  const status = document.getElementById("status");
  status.textContent = message;
  status.classList.toggle("error", Boolean(isError));
}

function renderTable(rows) {
  const body = document.getElementById("ranking-body");
  body.replaceChildren();

  for (const item of rows) {
    const tr = document.createElement("tr");
    const cells = [
      item.rank,
      item.strategy_name,
      formatNumber(item.score),
      formatMoney(item.total_test_net_profit),
      formatPercent(item.pass_rate),
      formatMoney(item.max_test_mdd),
      formatNumber(item.average_test_pf),
    ];

    for (const cell of cells) {
      const td = document.createElement("td");
      td.textContent = cell;
      tr.appendChild(td);
    }

    const detailCell = document.createElement("td");
    const detailButton = document.createElement("button");
    detailButton.type = "button";
    detailButton.className = "btn link";
    detailButton.textContent = "查看詳情";
    detailButton.addEventListener("click", () => renderStrategyDetail(item.strategy_name));
    detailCell.appendChild(detailButton);
    tr.appendChild(detailCell);
    body.appendChild(tr);
  }
}

function renderCharts(rows) {
  if (!window.Chart) {
    renderStatus("Chart.js 載入失敗，仍可查看排行榜表格。", true);
    return;
  }

  const labels = rows.map((item) => `#${item.rank} ${shortName(item.strategy_name)}`);
  scoreChart = renderBarChart(
    "score-chart",
    labels,
    rows.map((item) => item.score),
    "分數",
    "#2563eb",
    scoreChart,
  );
  profitChart = renderBarChart(
    "profit-chart",
    labels,
    rows.map((item) => item.total_test_net_profit),
    "總獲利",
    "#10b981",
    profitChart,
  );
}

async function renderStrategyDetail(strategyName) {
  if (!currentReport) {
    return;
  }

  const row = findStrategyRow(strategyName);
  if (!row) {
    renderStatus(`找不到策略：${strategyName}`, true);
    return;
  }

  const detail = await loadStrategyDetail(strategyName).catch((error) => {
    console.warn("Strategy detail JSON failed to load; falling back to ranking row.", error);
    return null;
  });
  const source = detail || buildDetailFromRankingRow(row);
  const summary = source.summary;
  const kpi = source.kpi;

  showView("detail");
  document.getElementById("detail-strategy-name").textContent = source.strategy_name;
  document.getElementById("detail-score").textContent = formatNumber(kpi.score);
  document.getElementById("detail-profit").textContent = formatMoney(kpi.profit);
  document.getElementById("detail-pass-rate").textContent = formatPercent(kpi.pass_rate);
  document.getElementById("detail-mdd").textContent = formatMoney(kpi.mdd);
  document.getElementById("detail-pf").textContent = formatNumber(kpi.pf);
  document.getElementById("detail-run-id").textContent = source.run_id || currentReport.run_id;
  document.getElementById("detail-generated-at").textContent = formatDateTime(
    currentReport.generated_at,
  );
  document.getElementById("detail-rank").textContent = `#${row.rank}`;

  renderDetailKpis({
    rank: row.rank,
    score: summary.score,
    total_test_net_profit: summary.total_test_net_profit,
    pass_rate: summary.pass_rate,
    max_test_mdd: summary.max_test_mdd,
    average_test_pf: summary.average_test_pf,
  });
  renderDetailCharts(source);
  window.scrollTo({ top: 0, behavior: "smooth" });
}

async function loadStrategyDetail(strategyName) {
  const filename = `${encodeURIComponent(strategyName)}.json`;
  const githubUrl = `${GITHUB_DETAILS_BASE_URL}/${filename}`;
  try {
    return await loadReport(githubUrl);
  } catch (githubError) {
    console.warn("GitHub strategy detail failed; trying local detail JSON.", githubError);
    return loadReport(`${LOCAL_DETAILS_BASE_URL}/${filename}`);
  }
}

function buildDetailFromRankingRow(row) {
  const profit = Number(row.total_test_net_profit) || 0;
  return {
    strategy_name: row.strategy_name,
    run_id: currentReport.run_id,
    summary: {
      score: Number(row.score) || 0,
      total_test_net_profit: profit,
      pass_rate: Number(row.pass_rate) || 0,
      max_test_mdd: Number(row.max_test_mdd) || 0,
      average_test_pf: Number(row.average_test_pf) || 0,
    },
    equity_curve: [],
    weekly_pnl: [],
    kpi: {
      score: Number(row.score) || 0,
      profit,
      pass_rate: Number(row.pass_rate) || 0,
      mdd: Number(row.max_test_mdd) || 0,
      pf: Number(row.average_test_pf) || 0,
    },
  };
}

function findStrategyRow(strategyName) {
  const allResults = Array.isArray(currentReport.all_results) ? currentReport.all_results : [];
  return (
    allResults.find((item) => item.strategy_name === strategyName) ||
    currentReport.top_10.find((item) => item.strategy_name === strategyName)
  );
}

function renderDetailKpis(row) {
  const items = [
    {
      label: "Score 分數",
      value: formatNumber(row.score),
      rating: rateScore(row.score),
      description: "綜合策略評分，越高代表目前 ranking 表現越強。",
    },
    {
      label: "Total Profit 總獲利",
      value: formatMoney(row.total_test_net_profit),
      rating: row.total_test_net_profit > 0 ? "Strong" : "Weak",
      description: "WFO / Pipeline 測試區間加總淨利。",
    },
    {
      label: "Pass Rate 通過率",
      value: formatPercent(row.pass_rate),
      rating: ratePassRate(row.pass_rate),
      description: "WFO rounds 通過比例。",
    },
    {
      label: "Max Drawdown 最大回撤",
      value: formatMoney(row.max_test_mdd),
      rating: rateMdd(row.max_test_mdd),
      description: "測試期間最大回撤，越低越好。",
    },
    {
      label: "Profit Factor",
      value: formatNumber(row.average_test_pf),
      rating: ratePf(row.average_test_pf),
      description: "平均 test PF，衡量獲利與虧損比例。",
    },
    {
      label: "Rank 排名",
      value: `#${row.rank}`,
      rating: row.rank <= 3 ? "Strong" : row.rank <= 10 ? "Watch" : "Weak",
      description: "目前 ranking report 中的名次。",
    },
  ];

  const body = document.getElementById("detail-kpi-body");
  body.replaceChildren();
  for (const item of items) {
    const tr = document.createElement("tr");
    appendTextCell(tr, item.label);
    appendTextCell(tr, item.value);
    const ratingCell = appendTextCell(tr, item.rating);
    ratingCell.className = `rating-${item.rating.toLowerCase()}`;
    appendTextCell(tr, item.description);
    body.appendChild(tr);
  }
}

function appendTextCell(row, value) {
  const cell = document.createElement("td");
  cell.textContent = value;
  row.appendChild(cell);
  return cell;
}

function renderDetailCharts(detail) {
  if (!window.Chart) {
    return;
  }

  const hasDetailSeries =
    Array.isArray(detail.equity_curve) &&
    detail.equity_curve.length > 0 &&
    Array.isArray(detail.weekly_pnl) &&
    detail.weekly_pnl.length > 0;

  if (hasDetailSeries) {
    document.getElementById("detail-equity-title").textContent = "資產曲線";
    document.getElementById("detail-period-title").textContent = "每期損益";
    renderEquityCurve(detail.equity_curve);
    renderPeriodPnl(detail.weekly_pnl);
    return;
  }

  document.getElementById("detail-equity-title").textContent = "尚未產生週期資料";
  document.getElementById("detail-period-title").textContent = "尚未產生週期資料";
  renderEmptyDetailCharts();
}

function renderEquityCurve(equityCurve) {
  if (detailEquityChart) {
    detailEquityChart.destroy();
  }

  detailEquityChart = new Chart(document.getElementById("detail-equity-chart"), {
    type: "line",
    data: {
      labels: equityCurve.map((item) => item.week),
      datasets: [
        {
          label: "資產曲線",
          data: equityCurve.map((item) => item.equity),
          borderColor: "#2563eb",
          backgroundColor: "rgba(37, 99, 235, 0.12)",
          fill: true,
          tension: 0.25,
          pointRadius: 3,
        },
      ],
    },
    options: detailChartOptions("累積損益"),
  });
}

function renderPeriodPnl(weeklyPnl) {
  if (detailPeriodChart) {
    detailPeriodChart.destroy();
  }

  detailPeriodChart = new Chart(document.getElementById("detail-period-chart"), {
    type: "bar",
    data: {
      labels: weeklyPnl.map((item) => item.week),
      datasets: [
        {
          label: "每期損益",
          data: weeklyPnl.map((item) => item.pnl),
          backgroundColor: weeklyPnl.map((item) =>
            item.pnl >= 0 ? "#10b981" : "#d32f2f",
          ),
          borderRadius: 6,
          maxBarThickness: 38,
        },
      ],
    },
    options: detailChartOptions("損益"),
  });
}

function renderEmptyDetailCharts() {
  if (detailEquityChart) {
    detailEquityChart.destroy();
    detailEquityChart = null;
  }
  if (detailPeriodChart) {
    detailPeriodChart.destroy();
    detailPeriodChart = null;
  }

  detailEquityChart = new Chart(document.getElementById("detail-equity-chart"), {
    type: "line",
    data: {
      labels: [],
      datasets: [
        {
          label: "尚未產生週期資料",
          data: [],
          borderColor: "#94a3b8",
        },
      ],
    },
    options: detailChartOptions("equity"),
  });

  detailPeriodChart = new Chart(document.getElementById("detail-period-chart"), {
    type: "bar",
    data: {
      labels: [],
      datasets: [
        {
          label: "尚未產生週期資料",
          data: [],
          backgroundColor: "#cbd5e1",
        },
      ],
    },
    options: detailChartOptions("pnl"),
  });
}

function detailChartOptions(yTitle) {
  return {
    maintainAspectRatio: false,
    responsive: true,
    plugins: {
      legend: { position: "bottom" },
    },
    scales: {
      x: {
        grid: { display: false },
      },
      y: {
        beginAtZero: true,
        title: { display: true, text: yTitle },
        grid: { color: "#eef2f7" },
      },
    },
  };
}

function renderBarChart(canvasId, labels, values, label, color, existingChart) {
  if (existingChart) {
    existingChart.destroy();
  }

  return new Chart(document.getElementById(canvasId), {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          label,
          data: values,
          backgroundColor: color,
          borderRadius: 6,
          maxBarThickness: 42,
        },
      ],
    },
    options: {
      maintainAspectRatio: false,
      responsive: true,
      plugins: {
        legend: { display: false },
      },
      scales: {
        x: {
          ticks: {
            autoSkip: false,
            maxRotation: 30,
            minRotation: 0,
          },
          grid: {
            display: false,
          },
        },
        y: {
          beginAtZero: true,
          grid: {
            color: "#eef2f7",
          },
        },
      },
    },
  });
}

function rateScore(value) {
  if (value >= 100) return "Strong";
  if (value >= 80) return "Watch";
  return "Weak";
}

function ratePassRate(value) {
  if (value >= 0.6) return "Strong";
  if (value >= 0.4) return "Watch";
  return "Weak";
}

function ratePf(value) {
  if (value >= 1.5) return "Strong";
  if (value >= 1.1) return "Watch";
  return "Weak";
}

function rateMdd(value) {
  if (value <= 10000) return "Strong";
  if (value <= 20000) return "Watch";
  return "Weak";
}

function shortName(value) {
  return value.length > 16 ? `${value.slice(0, 16)}...` : value;
}

function formatNumber(value) {
  return new Intl.NumberFormat("zh-TW", {
    maximumFractionDigits: 2,
  }).format(value);
}

function formatMoney(value) {
  return new Intl.NumberFormat("zh-TW", {
    maximumFractionDigits: 0,
  }).format(value);
}

function formatPercent(value) {
  return new Intl.NumberFormat("zh-TW", {
    style: "percent",
    maximumFractionDigits: 1,
  }).format(value);
}

function formatDateTime(value) {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat("zh-TW", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(parsed);
}
