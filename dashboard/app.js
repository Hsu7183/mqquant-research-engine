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
      parseStrategyFamily(item.strategy_name),
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

function parseStrategyFamily(strategyName) {
  const familyNames = {
    trend_breakout: "趨勢突破",
    open_range_breakout: "開盤區間突破",
    vwap_pullback: "VWAP 拉回",
    mean_reversion_range: "區間均值回歸",
    volume_breakout: "量能突破",
    breakdown_momentum: "急跌/急漲動能",
    slow_grind_trend: "緩步趨勢",
    afternoon_trend_extension: "午後趨勢延伸",
  };
  for (const [family, label] of Object.entries(familyNames)) {
    if (strategyName.startsWith(`${family}_`)) return label;
  }
  return strategyName.split("_").slice(0, -1).join("_") || strategyName;
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
    "扣成本後總損益",
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

  let detailLoaded = true;
  const detail = await loadStrategyDetail(strategyName).catch((error) => {
    console.warn("Strategy detail failed to load; falling back to ranking row.", error);
    detailLoaded = false;
    return null;
  });
  const source = detail || buildDetailFromRankingRow(row);
  const metrics = extractDetailMetrics(source, row);

  showView("detail");
  document.getElementById("detail-strategy-name").textContent = source.strategy_name;
  document.getElementById("detail-score").textContent = formatNumber(metrics.score);
  document.getElementById("detail-profit").textContent = formatMoney(metrics.profit);
  document.getElementById("detail-pass-rate").textContent = formatPercent(metrics.passRate);
  document.getElementById("detail-mdd").textContent = formatMoney(metrics.mdd);
  document.getElementById("detail-pf").textContent = formatNumber(metrics.pf);
  document.getElementById("detail-run-id").textContent = source.run_id || currentReport.run_id;
  document.getElementById("detail-generated-at").textContent = formatDateTime(
    currentReport.generated_at,
  );
  document.getElementById("detail-rank").textContent = `#${row.rank}`;

  renderDetailDataStatus(source, detailLoaded);
  renderDetailKpis(source, row);
  renderCostStress(source);
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
    period: {
      start: "",
      end: "",
    },
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

function extractDetailMetrics(detail, row) {
  const summary = detail.summary || {};
  const kpi = detail.kpi || {};
  const stats = detail.trade_stats || {};
  return {
    score: numericValue(kpi.score ?? summary.score ?? row.score),
    profit: numericValue(
      stats.total_profit ??
        kpi.profit ??
        summary.total_test_net_profit ??
        row.total_test_net_profit,
    ),
    passRate: numericValue(kpi.pass_rate ?? summary.pass_rate ?? row.pass_rate),
    mdd: numericValue(
      stats.max_drawdown ?? kpi.mdd ?? summary.max_test_mdd ?? row.max_test_mdd,
    ),
    pf: numericValue(
      stats.profit_factor ?? kpi.pf ?? summary.average_test_pf ?? row.average_test_pf,
    ),
  };
}

function renderDetailDataStatus(detail, detailLoaded) {
  const status = document.getElementById("detail-data-status");
  if (!detailLoaded) {
    status.textContent =
      "尚未讀取到 strategy_detail.json，目前使用 ranking 摘要資料";
    status.classList.add("error");
    return;
  }

  if (!hasWeeklySeries(detail)) {
    status.textContent =
      "detail JSON 已讀取，但 weekly 資料為空，請重新執行 Run Pipeline";
    status.classList.add("error");
    return;
  }

  if (!detail.trade_stats) {
    status.textContent =
      "目前只有排名摘要資料，請重新執行 Run Pipeline 產生完整策略詳情。";
    status.classList.add("error");
    return;
  }

  status.textContent =
    "已讀取 strategy_detail.json，圖表使用每週資產曲線與每週損益。";
  status.classList.remove("error");
}

function renderDetailKpis(detail, row) {
  const summary = detail.summary || {};
  const stats = detail.trade_stats || {};
  const period = detail.period || {};
  const items = [
    {
      category: "基本資料",
      label: "測試期間",
      value: formatPeriod(period),
      rating: "",
      description: "第一筆交易進場日至最後一筆交易出場日。",
    },
    {
      category: "基本資料",
      label: "交易比數",
      value: formatIntegerOrDash(stats.trade_count),
      rating: "",
      description: "TXT 解析出的總交易筆數。",
    },
    {
      category: "基本資料",
      label: "多單比數",
      value: formatIntegerOrDash(stats.long_count),
      rating: "",
      description: "direction = 1 的交易筆數。",
    },
    {
      category: "基本資料",
      label: "空單比數",
      value: formatIntegerOrDash(stats.short_count),
      rating: "",
      description: "direction = -1 的交易筆數。",
    },
    {
      category: "交易品質",
      label: "勝率",
      value: formatPercentOrDash(stats.win_rate),
      rating: rateWinRate(stats.win_rate),
      description: "獲利交易數 / 總交易數。",
    },
    {
      category: "交易品質",
      label: "賺錢比數",
      value: formatIntegerOrDash(stats.win_count),
      rating: "",
      description: "pnl > 0 的交易筆數。",
    },
    {
      category: "交易品質",
      label: "虧錢比數",
      value: formatIntegerOrDash(stats.loss_count),
      rating: "",
      description: "pnl < 0 的交易筆數。",
    },
    {
      category: "交易品質",
      label: "Profit Factor",
      value: formatNumberOrDash(stats.profit_factor ?? summary.average_test_pf),
      rating: ratePf(stats.profit_factor ?? summary.average_test_pf),
      description: "總獲利 / 總虧損，越高越好。",
    },
    {
      category: "交易品質",
      label: "Payoff Ratio",
      value: formatNumberOrDash(stats.payoff_ratio),
      rating: ratePayoff(stats.payoff_ratio),
      description: "平均獲利 / 平均虧損，衡量盈虧結構。",
    },
    {
      category: "交易品質",
      label: "最多連敗",
      value: formatIntegerOrDash(stats.max_losing_streak),
      rating: rateLosingStreak(stats.max_losing_streak),
      description: "連續 pnl < 0 的最大交易次數。",
    },
    {
      category: "損益表現",
      label: "扣成本後總損益",
      value: formatMoney(numericValue(stats.total_profit ?? row.total_test_net_profit)),
      rating: numericValue(stats.total_profit ?? row.total_test_net_profit) > 0 ? "Strong" : "Weak",
      description: "所有交易 net pnl 加總。",
    },
    {
      category: "損益表現",
      label: "平均每筆損益",
      value: formatMoneyOrDash(stats.avg_trade_pnl),
      rating: hasExplicitValue(stats.avg_trade_pnl)
        ? numericValue(stats.avg_trade_pnl) > 0
          ? "Strong"
          : "Weak"
        : "",
      description: "總獲利 / 交易比數。",
    },
    {
      category: "損益表現",
      label: "平均獲利",
      value: formatMoneyOrDash(stats.avg_win),
      rating: "",
      description: "獲利交易的平均 pnl。",
    },
    {
      category: "損益表現",
      label: "平均虧損",
      value: formatMoneyOrDash(stats.avg_loss),
      rating: "",
      description: "虧損交易平均 pnl 的絕對值。",
    },
    {
      category: "損益表現",
      label: "最大單筆獲利",
      value: formatMoneyOrDash(stats.largest_win),
      rating: "",
      description: "單筆最大正 pnl。",
    },
    {
      category: "損益表現",
      label: "最大單筆虧損",
      value: formatMoneyOrDash(stats.largest_loss),
      rating: "",
      description: "單筆最大負 pnl 的絕對值。",
    },
    {
      category: "風險生存",
      label: "最大回撤",
      value: formatMoney(numericValue(stats.max_drawdown ?? row.max_test_mdd)),
      rating: rateMdd(stats.max_drawdown ?? row.max_test_mdd),
      description: "用 weekly equity curve 計算的最大回撤。",
    },
    {
      category: "風險生存",
      label: "水下週數",
      value: formatIntegerOrDash(stats.underwater_weeks),
      rating: rateUnderwaterWeeks(stats.underwater_weeks),
      description: "weekly equity 低於歷史高點的週數。",
    },
    {
      category: "風險生存",
      label: "Score 分數",
      value: formatNumber(summary.score ?? row.score),
      rating: rateScore(summary.score ?? row.score),
      description: "綜合策略評分，越高代表 ranking 表現越強。",
    },
    {
      category: "風險生存",
      label: "WFO 通過率",
      value: formatPercent(summary.pass_rate ?? row.pass_rate),
      rating: ratePassRate(summary.pass_rate ?? row.pass_rate),
      description: "WFO rounds 通過比例。",
    },
  ];

  items.push(...buildCostKpiItems(detail));

  const body = document.getElementById("detail-kpi-body");
  body.replaceChildren();
  for (const item of items) {
    const tr = document.createElement("tr");
    appendTextCell(tr, item.category);
    appendTextCell(tr, item.label);
    appendTextCell(tr, item.value);
    const ratingCell = appendTextCell(tr, item.rating || "-");
    if (item.rating) {
      ratingCell.className = `rating-${item.rating.toLowerCase()}`;
    }
    appendTextCell(tr, item.description);
    body.appendChild(tr);
  }
}

function buildCostKpiItems(detail) {
  const cost = detail.cost || {};
  const stats = detail.trade_stats || {};
  return [
    ["單邊滑點", formatNumberOrDash(cost.slippage_points_per_side), "每次進場或出場假設滑點"],
    ["來回滑點", formatNumberOrDash(cost.round_trip_slippage_points), "一筆完整交易的進出場滑點"],
    ["單邊手續費", formatMoneyOrDash(cost.fee_money_per_side), "單邊手續費金額"],
    ["來回手續費", formatMoneyOrDash(cost.round_trip_fee_money), "一筆完整交易手續費"],
    ["期交稅率", hasExplicitValue(cost.tax_rate) ? String(cost.tax_rate) : "-", "股價類期貨交易稅率"],
    ["每點價值", formatMoneyOrDash(cost.point_value), "小台預設每點 50 元"],
    ["口數", formatIntegerOrDash(cost.qty), "回測換算口數"],
    ["總滑點成本", formatMoneyOrDash(cost.total_slippage_cost_points), "所有交易滑點成本點數"],
    ["總手續費成本", formatMoneyOrDash(cost.total_fee_cost_points), "所有交易手續費換算點數"],
    ["總期交稅成本", formatMoneyOrDash(cost.total_tax_cost_points), "所有交易期交稅換算點數"],
    ["總交易成本", formatMoneyOrDash(cost.total_cost_points ?? stats.total_cost), "滑點、手續費與期交稅總和"],
    ["平均每筆成本", formatMoneyOrDash(cost.avg_cost_per_trade_points ?? stats.avg_cost_per_trade), "每筆交易平均成本點數"],
    ["扣成本後平均每筆損益", formatMoneyOrDash(stats.avg_net_pnl_per_trade), "net pnl / trade count"],
    ["扣成本後總損益", formatMoneyOrDash(stats.net_total_profit ?? stats.total_profit), "扣除完整交易成本後的總損益"],
  ].map(([label, value, description]) => ({
    category: "交易成本",
    label,
    value,
    rating: "",
    description,
  }));
}

function renderCostStress(detail) {
  const body = document.getElementById("detail-cost-stress-body");
  if (!body) return;
  body.replaceChildren();

  const rows = Array.isArray(detail.cost_stress) ? detail.cost_stress : [];
  if (!rows.length) {
    const tr = document.createElement("tr");
    const cell = document.createElement("td");
    cell.colSpan = 5;
    cell.textContent = "尚未產生成本壓力測試資料，請重新執行 Run Pipeline。";
    tr.appendChild(cell);
    body.appendChild(tr);
    return;
  }

  for (const item of rows) {
    const tr = document.createElement("tr");
    appendTextCell(tr, formatNumber(item.slippage_points));
    appendTextCell(tr, formatMoney(item.total_net_pnl));
    appendTextCell(tr, formatNumber(item.profit_factor));
    appendTextCell(tr, formatMoney(item.max_drawdown));
    appendTextCell(tr, item.passed ? "通過" : "未通過");
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

  if (hasWeeklySeries(detail)) {
    document.getElementById("detail-equity-title").textContent = "每週資產曲線";
    document.getElementById("detail-period-title").textContent = "每週損益";
    renderEquityCurve(detail.equity_curve);
    renderPeriodPnl(detail.weekly_pnl);
    return;
  }

  document.getElementById("detail-equity-title").textContent = "尚未產生週期資料";
  document.getElementById("detail-period-title").textContent = "尚未產生週期資料";
  destroyDetailCharts();
}

function hasWeeklySeries(detail) {
  return (
    Array.isArray(detail.equity_curve) &&
    detail.equity_curve.length > 0 &&
    Array.isArray(detail.weekly_pnl) &&
    detail.weekly_pnl.length > 0
  );
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
          label: "每週資產曲線",
          data: equityCurve.map((item) => item.equity),
          borderColor: "#2563eb",
          backgroundColor: "rgba(37, 99, 235, 0.12)",
          fill: true,
          tension: 0.25,
          pointRadius: 3,
        },
      ],
    },
    options: detailChartOptions("資產", false),
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
          label: "每週損益",
          data: weeklyPnl.map((item) => item.pnl),
          backgroundColor: weeklyPnl.map((item) =>
            item.pnl >= 0 ? "#10b981" : "#d32f2f",
          ),
          borderRadius: 6,
          maxBarThickness: 38,
        },
      ],
    },
    options: detailChartOptions("損益", true),
  });
}

function destroyDetailCharts() {
  if (detailEquityChart) {
    detailEquityChart.destroy();
    detailEquityChart = null;
  }
  if (detailPeriodChart) {
    detailPeriodChart.destroy();
    detailPeriodChart = null;
  }
}

function detailChartOptions(yTitle, beginAtZero = true) {
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
        beginAtZero,
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
  if (!hasExplicitValue(value)) return "";
  const number = numericValue(value);
  if (number >= 100) return "Strong";
  if (number >= 80) return "Watch";
  return "Weak";
}

function ratePassRate(value) {
  if (!hasExplicitValue(value)) return "";
  const number = numericValue(value);
  if (number >= 0.6) return "Strong";
  if (number >= 0.4) return "Watch";
  return "Weak";
}

function rateWinRate(value) {
  if (!hasExplicitValue(value)) return "";
  const number = numericValue(value);
  if (number >= 0.55) return "Strong";
  if (number >= 0.45) return "Watch";
  return "Weak";
}

function ratePf(value) {
  if (!hasExplicitValue(value)) return "";
  const number = numericValue(value);
  if (number >= 1.5) return "Strong";
  if (number >= 1.1) return "Watch";
  return "Weak";
}

function ratePayoff(value) {
  if (!hasExplicitValue(value)) return "";
  const number = numericValue(value);
  if (number >= 1.2) return "Strong";
  if (number >= 0.8) return "Watch";
  return "Weak";
}

function rateMdd(value) {
  if (!hasExplicitValue(value)) return "";
  const number = numericValue(value);
  if (number <= 10000) return "Strong";
  if (number <= 20000) return "Watch";
  return "Weak";
}

function rateUnderwaterWeeks(value) {
  if (!hasExplicitValue(value)) return "";
  const number = numericValue(value);
  if (number <= 8) return "Strong";
  if (number <= 20) return "Watch";
  return "Weak";
}

function rateLosingStreak(value) {
  if (!hasExplicitValue(value)) return "";
  const number = numericValue(value);
  if (number <= 3) return "Strong";
  if (number <= 6) return "Watch";
  return "Weak";
}

function shortName(value) {
  return value.length > 16 ? `${value.slice(0, 16)}...` : value;
}

function hasExplicitValue(value) {
  return value !== undefined && value !== null && value !== "";
}

function numericValue(value) {
  if (!hasExplicitValue(value)) {
    return 0;
  }
  if (value === "Infinity") return Infinity;
  if (value === "-Infinity") return -Infinity;
  const number = Number(value);
  return Number.isNaN(number) ? 0 : number;
}

function formatNumberOrDash(value) {
  return hasExplicitValue(value) ? formatNumber(value) : "-";
}

function formatMoneyOrDash(value) {
  return hasExplicitValue(value) ? formatMoney(value) : "-";
}

function formatPercentOrDash(value) {
  return hasExplicitValue(value) ? formatPercent(value) : "-";
}

function formatIntegerOrDash(value) {
  if (!hasExplicitValue(value)) {
    return "-";
  }
  return new Intl.NumberFormat("zh-TW", {
    maximumFractionDigits: 0,
  }).format(numericValue(value));
}

function formatPeriod(period) {
  if (!period || !period.start || !period.end) {
    return "-";
  }
  return `${period.start} ～ ${period.end}`;
}

function formatNumber(value) {
  const number = numericValue(value);
  if (!Number.isFinite(number)) {
    return number > 0 ? "∞" : "-∞";
  }
  return new Intl.NumberFormat("zh-TW", {
    maximumFractionDigits: 2,
  }).format(number);
}

function formatMoney(value) {
  const number = numericValue(value);
  if (!Number.isFinite(number)) {
    return number > 0 ? "∞" : "-∞";
  }
  return new Intl.NumberFormat("zh-TW", {
    maximumFractionDigits: 0,
  }).format(number);
}

function formatPercent(value) {
  const number = numericValue(value);
  return new Intl.NumberFormat("zh-TW", {
    style: "percent",
    maximumFractionDigits: 1,
  }).format(number);
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
