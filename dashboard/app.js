const ARTIFACT_BASE = "/runs/latest";
const JOB_BASE = "/runs/jobs";

const artifacts = {
  ranking: "ranking.json",
  detail: "strategy_detail.json",
  equity: "equity_curve.csv",
  trades: "trades.csv",
  oos: "oos_summary.json",
  wfo: "wfo_summary.json",
  risk: "risk_report.json",
  audit: "decision_audit.json",
};

let equityChart = null;
let drawdownChart = null;
let jobRefreshTimer = null;

document.addEventListener("DOMContentLoaded", () => {
  bindJobMonitor();
  loadDashboard().catch((error) => {
    console.error(error);
    showFetchError();
  });
});

async function loadDashboard() {
  const [
    ranking,
    strategyDetail,
    equityRows,
    tradeRows,
    oosSummary,
    wfoSummary,
    riskReport,
    decisionAudit,
  ] = await Promise.all([
    fetchJson(artifacts.ranking),
    fetchJson(artifacts.detail),
    fetchCsv(artifacts.equity),
    fetchCsv(artifacts.trades),
    fetchJson(artifacts.oos),
    fetchJson(artifacts.wfo),
    fetchJson(artifacts.risk),
    fetchJson(artifacts.audit),
  ]);

  document.getElementById("data-source").textContent = "Source: runs/latest/";
  renderSummary(ranking, strategyDetail);
  renderTopStrategies(ranking);
  renderEquityChart(equityRows);
  renderDrawdownChart(equityRows);
  renderTrades(tradeRows);
  renderValidationCards(oosSummary, wfoSummary, riskReport);
  renderDecisionAudit(decisionAudit);
}

async function fetchJson(filename) {
  const response = await fetch(`${ARTIFACT_BASE}/${filename}`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Failed to fetch ${filename}: ${response.status}`);
  }
  return response.json();
}

async function fetchCsv(filename) {
  const response = await fetch(`${ARTIFACT_BASE}/${filename}`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Failed to fetch ${filename}: ${response.status}`);
  }
  return parseCsv(await response.text());
}

function bindJobMonitor() {
  const loadButton = document.getElementById("job-load-button");
  const input = document.getElementById("job-id-input");
  const checkbox = document.getElementById("job-auto-refresh");

  loadButton.addEventListener("click", () => {
    loadJobMonitor();
  });
  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      loadJobMonitor();
    }
  });
  checkbox.addEventListener("change", () => {
    if (checkbox.checked) {
      loadJobMonitor();
      jobRefreshTimer = window.setInterval(loadJobMonitor, 2000);
    } else {
      stopJobAutoRefresh();
    }
  });

  renderJobEmptyState("尚未指定 job_id");
}

async function loadJobMonitor() {
  const jobId = document.getElementById("job-id-input").value.trim();
  if (!jobId) {
    renderJobEmptyState("尚未指定 job_id");
    return;
  }

  try {
    const [status, progress] = await Promise.all([
      fetchJobJson(jobId, "status.json"),
      fetchJobJson(jobId, "progress.json"),
    ]);
    renderJobMonitor(jobId, status, progress);
  } catch (error) {
    console.error(error);
    renderJobMissingState("找不到 job 或尚未產生 progress");
  }
}

async function fetchJobJson(jobId, filename) {
  const safeJobId = encodeURIComponent(jobId);
  const response = await fetch(`${JOB_BASE}/${safeJobId}/${filename}`, {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch job ${filename}: ${response.status}`);
  }
  return response.json();
}

function renderJobMonitor(jobId, status, progress) {
  const completed = Number(progress.completed ?? 0);
  const total = Number(progress.total ?? 0);
  const percent = Number(progress.percent ?? (total ? (completed / total) * 100 : 0));
  const boundedPercent = Math.max(0, Math.min(100, Number.isFinite(percent) ? percent : 0));

  document.getElementById("job-message").textContent = `job_id: ${jobId}`;
  document.getElementById("job-status").textContent = status.status ?? "--";
  document.getElementById("job-count").textContent = `${formatInteger(completed)} / ${formatInteger(total)}`;
  document.getElementById("job-percent").textContent = `${boundedPercent.toFixed(2)}%`;
  document.getElementById("job-current").textContent = progress.current || "--";
  document.getElementById("job-error").textContent = status.error || "--";
  document.getElementById("job-progress-bar").style.width = `${boundedPercent}%`;

  if (["completed", "failed", "stopped"].includes(status.status)) {
    stopJobAutoRefresh();
    document.getElementById("job-auto-refresh").checked = false;
  }
}

function renderJobEmptyState(message) {
  document.getElementById("job-message").textContent = message;
  document.getElementById("job-status").textContent = "--";
  document.getElementById("job-count").textContent = "--";
  document.getElementById("job-percent").textContent = "--";
  document.getElementById("job-current").textContent = "--";
  document.getElementById("job-error").textContent = "--";
  document.getElementById("job-progress-bar").style.width = "0%";
}

function renderJobMissingState(message) {
  renderJobEmptyState(message);
}

function stopJobAutoRefresh() {
  if (jobRefreshTimer !== null) {
    window.clearInterval(jobRefreshTimer);
    jobRefreshTimer = null;
  }
}

function parseCsv(text) {
  const rows = text.trim().split(/\r?\n/);
  if (rows.length <= 1) {
    return [];
  }

  const headers = splitCsvLine(rows[0]);
  return rows.slice(1).filter(Boolean).map((line) => {
    const cells = splitCsvLine(line);
    return headers.reduce((record, header, index) => {
      record[header] = cells[index] ?? "";
      return record;
    }, {});
  });
}

function splitCsvLine(line) {
  const result = [];
  let current = "";
  let inQuotes = false;

  for (let i = 0; i < line.length; i += 1) {
    const char = line[i];
    const next = line[i + 1];

    if (char === '"' && inQuotes && next === '"') {
      current += '"';
      i += 1;
    } else if (char === '"') {
      inQuotes = !inQuotes;
    } else if (char === "," && !inQuotes) {
      result.push(current);
      current = "";
    } else {
      current += char;
    }
  }

  result.push(current);
  return result;
}

function renderSummary(ranking, strategyDetail) {
  const top = ranking[0] ?? {};
  const performance = strategyDetail.performance ?? {};
  document.getElementById("summary-return").textContent = formatPercent(
    performance.return ?? top.annual_return,
  );
  document.getElementById("summary-sharpe").textContent = formatNumber(top.sharpe, 2);
  document.getElementById("summary-mdd").textContent = formatMoney(
    performance.mdd ?? top.max_drawdown,
  );
}

function renderTopStrategies(ranking) {
  const body = document.getElementById("top-strategies-body");
  body.innerHTML = "";

  ranking.slice(0, 5).forEach((row) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${escapeHtml(row.strategy_id)}</td>
      <td>${formatNumber(row.score, 2)}</td>
      <td>${formatNumber(row.sharpe, 2)}</td>
      <td>${formatMoney(row.max_drawdown)}</td>
      <td>${formatInteger(row.trade_count)}</td>
    `;
    body.appendChild(tr);
  });
}

function renderEquityChart(rows) {
  const labels = rows.map((row) => row.datetime);
  const values = rows.map((row) => Number(row.equity));

  if (equityChart) {
    equityChart.destroy();
  }

  equityChart = new Chart(document.getElementById("equity-chart"), {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "equity",
          data: values,
          borderColor: "#38bdf8",
          backgroundColor: "rgba(56, 189, 248, 0.14)",
          pointRadius: 0,
          borderWidth: 2,
          tension: 0.25,
          fill: true,
        },
      ],
    },
    options: baseChartOptions(),
  });
}

function renderDrawdownChart(rows) {
  const labels = rows.map((row) => row.datetime);
  const values = rows.map((row) => Number(row.drawdown));

  if (drawdownChart) {
    drawdownChart.destroy();
  }

  drawdownChart = new Chart(document.getElementById("drawdown-chart"), {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "drawdown",
          data: values,
          borderColor: "#f97316",
          backgroundColor: "rgba(249, 115, 22, 0.13)",
          pointRadius: 0,
          borderWidth: 2,
          tension: 0.2,
          fill: true,
        },
      ],
    },
    options: baseChartOptions(),
  });
}

function renderTrades(trades) {
  const body = document.getElementById("trades-body");
  body.innerHTML = "";

  trades.slice(-20).reverse().forEach((row) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${escapeHtml(row.datetime)}</td>
      <td>${formatNumber(row.price, 2)}</td>
      <td><span class="side side-${escapeHtml(row.side)}">${escapeHtml(row.side)}</span></td>
      <td class="${Number(row.pnl) >= 0 ? "positive" : "negative"}">${formatNumber(row.pnl, 2)}</td>
      <td>${formatNumber(row.cumulative_pnl, 2)}</td>
    `;
    body.appendChild(tr);
  });
}

function renderValidationCards(oos, wfo, risk) {
  renderDefinitionList("oos-card", [
    ["OOS Sharpe", formatNumber(oos.oos_sharpe, 2)],
    ["OOS Return", formatPercent(oos.oos_return)],
    ["OOS MDD", formatMoney(oos.oos_mdd)],
    ["Periods", formatInteger((oos.oos_periods ?? []).length)],
  ]);

  renderDefinitionList("wfo-card", [
    ["Avg Sharpe", formatNumber(wfo.avg_sharpe, 2)],
    ["Pass Rate", formatPercent(wfo.pass_rate)],
    ["Stability", formatNumber(wfo.stability_score, 2)],
    ["Rounds", formatInteger((wfo.rounds ?? []).length)],
  ]);

  renderDefinitionList("risk-card", [
    ["Max DD", formatMoney(risk.max_dd)],
    ["Ulcer Index", formatNumber(risk.ulcer_index, 2)],
    ["Recovery Days", formatInteger(risk.recovery_days)],
    ["Volatility", formatPercent(risk.volatility)],
    ["Downside Vol", formatPercent(risk.downside_volatility)],
  ]);
}

function renderDefinitionList(elementId, rows) {
  const target = document.getElementById(elementId);
  target.innerHTML = rows
    .map(([label, value]) => `<div><dt>${label}</dt><dd>${value}</dd></div>`)
    .join("");
}

function renderDecisionAudit(audit) {
  document.getElementById("audit-baseline").textContent = audit.baseline_strategy ?? "--";
  document.getElementById("audit-challenger").textContent = audit.challenger_strategy ?? "--";
  document.getElementById("audit-decision").textContent = audit.promotion_decision ?? "--";
  document.getElementById("audit-recommendation").textContent =
    audit.recommend_promote === true
      ? "Promote"
      : audit.recommend_promote === false
        ? "Do not promote"
        : "Review required";
  document.getElementById("audit-score").textContent = formatNumber(audit.score, 2);
  document.getElementById("audit-review").textContent =
    audit.requires_human_review === false ? "No" : "Required";
  document.getElementById("audit-reason").textContent = audit.reason ?? "--";
  document.getElementById("audit-warnings").textContent = formatWarnings(audit.risk_warnings);
  renderAuditChecks(audit.checks ?? {});
}

function renderAuditChecks(checks) {
  const body = document.getElementById("audit-checks-body");
  body.innerHTML = "";

  const rows = [
    ["ranking", "score", checks.ranking?.score, checks.ranking?.min_score],
    ["ranking", "profit_factor", checks.ranking?.profit_factor, checks.ranking?.min_profit_factor],
    ["ranking", "trade_count", checks.ranking?.trade_count, checks.ranking?.min_trade_count],
    ["oos", "oos_sharpe", checks.oos?.oos_sharpe, checks.oos?.min_oos_sharpe],
    ["oos", "oos_return", checks.oos?.oos_return, checks.oos?.min_oos_return],
    ["oos", "oos_mdd", checks.oos?.oos_mdd, checks.oos?.max_oos_mdd],
    ["wfo", "pass_rate", checks.wfo?.pass_rate, checks.wfo?.min_pass_rate],
    ["wfo", "avg_sharpe", checks.wfo?.avg_sharpe, checks.wfo?.min_avg_sharpe],
    ["wfo", "stability_score", checks.wfo?.stability_score, checks.wfo?.min_stability_score],
    ["risk", "max_dd", checks.risk?.max_dd, checks.risk?.max_risk_drawdown],
    ["risk", "ulcer_index", checks.risk?.ulcer_index, checks.risk?.max_ulcer_index],
    ["risk", "recovery_days", checks.risk?.recovery_days, checks.risk?.max_recovery_days],
  ];

  rows.forEach(([group, metric, value, threshold]) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${escapeHtml(group)}</td>
      <td>${escapeHtml(metric)}</td>
      <td>${formatAuditValue(value)}</td>
      <td>${formatAuditValue(threshold)}</td>
    `;
    body.appendChild(tr);
  });
}

function baseChartOptions() {
  return {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      intersect: false,
      mode: "index",
    },
    plugins: {
      legend: {
        labels: {
          color: "#cbd5e1",
        },
      },
    },
    scales: {
      x: {
        ticks: {
          color: "#94a3b8",
          maxTicksLimit: 7,
        },
        grid: {
          color: "rgba(148, 163, 184, 0.12)",
        },
      },
      y: {
        ticks: {
          color: "#94a3b8",
        },
        grid: {
          color: "rgba(148, 163, 184, 0.12)",
        },
      },
    },
  };
}

function showFetchError() {
  document.getElementById("error-panel").classList.remove("hidden");
  document.getElementById("data-source").textContent = "Artifact fetch failed";
}

function formatNumber(value, digits = 2) {
  const number = Number(value);
  if (!Number.isFinite(number)) {
    return "--";
  }
  return number.toLocaleString("en-US", {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits,
  });
}

function formatInteger(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) {
    return "--";
  }
  return Math.round(number).toLocaleString("en-US");
}

function formatMoney(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) {
    return "--";
  }
  return number.toLocaleString("en-US", {
    maximumFractionDigits: 0,
  });
}

function formatPercent(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) {
    return "--";
  }
  return `${(number * 100).toFixed(2)}%`;
}

function formatWarnings(warnings) {
  if (!Array.isArray(warnings) || warnings.length === 0) {
    return "No risk warnings";
  }
  return warnings.join("; ");
}

function formatAuditValue(value) {
  if (value === undefined || value === null || value === "") {
    return "--";
  }
  if (typeof value === "number") {
    return formatNumber(value, Math.abs(value) >= 10 ? 2 : 4);
  }
  return escapeHtml(value);
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
