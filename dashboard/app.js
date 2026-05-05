const DASHBOARD_PASSWORD = "mqquant";
const DASHBOARD_AUTH_KEY = "mqquant_dashboard_authenticated";

const GITHUB_OWNER = "Hsu7183";
const GITHUB_REPO = "mqquant-research-engine";
const BRANCH = "main";
const LATEST_REPORT_PATH = "runs/latest/reports/ranking.json";
const GITHUB_REPORT_URL =
  `https://raw.githubusercontent.com/${GITHUB_OWNER}/${GITHUB_REPO}/${BRANCH}/${LATEST_REPORT_PATH}`;
const LOCAL_REPORT_URL = "sample_ranking.json";

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

let scoreChart = null;
let profitChart = null;

document.addEventListener("DOMContentLoaded", () => {
  bindAccessGate();
  if (isAuthenticated()) {
    showDashboard();
  } else {
    showAccessGate();
  }
});

function bindAccessGate() {
  const passwordInput = document.getElementById("password-input");
  const enterButton = document.getElementById("enter-button");
  const clearButton = document.getElementById("clear-button");
  const logoutButton = document.getElementById("logout-button");

  enterButton.addEventListener("click", handleLogin);
  clearButton.addEventListener("click", clearAccess);
  logoutButton.addEventListener("click", clearAccess);
  passwordInput.addEventListener("keydown", (event) => {
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

function clearAccess() {
  localStorage.removeItem(DASHBOARD_AUTH_KEY);
  document.getElementById("password-input").value = "";
  document.getElementById("login-error").textContent = "";
  showAccessGate();
}

function showAccessGate() {
  document.getElementById("access-gate").classList.remove("hidden");
  document.getElementById("dashboard-shell").classList.add("hidden");
  document.getElementById("password-input").focus();
}

function showDashboard() {
  document.getElementById("access-gate").classList.add("hidden");
  document.getElementById("dashboard-shell").classList.remove("hidden");
  loadAndRenderDashboard();
}

function loadAndRenderDashboard() {
  loadLatestReport()
    .then(({ report, dataSource, sourceUrl }) => {
      validateReportSchema(report);
      renderDashboard(report, dataSource, sourceUrl);
    })
    .catch((error) => {
      console.warn(error);
      renderStatus("GitHub 與本地 ranking JSON 皆載入失敗，改用內建備援資料。", true);
      renderDashboard(fallbackReport, "內建備援", "inline fallbackReport");
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

function renderBarChart(canvasId, labels, values, label, color, existingChart) {
  if (existingChart) {
    existingChart.destroy();
  }

  const canvas = document.getElementById(canvasId);
  return new Chart(canvas, {
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
