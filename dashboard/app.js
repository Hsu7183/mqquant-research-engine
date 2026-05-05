const REPORT_URL = "sample_ranking.json";

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

document.addEventListener("DOMContentLoaded", () => {
  loadReport(REPORT_URL)
    .then((report) => {
      validateReportSchema(report);
      renderDashboard(report);
    })
    .catch((error) => {
      console.warn(error);
      renderStatus("sample_ranking.json failed to load; using embedded fallback.", true);
      renderDashboard(fallbackReport);
    });
});

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

function renderDashboard(report) {
  const top10 = report.top_10.slice(0, 10);
  document.getElementById("run-id").textContent = `run_id: ${report.run_id}`;
  document.getElementById("generated-at").textContent =
    `generated_at: ${report.generated_at}`;
  document.getElementById("summary").textContent =
    `strategies: ${report.summary.valid_strategies}/${report.summary.total_strategies}`;

  renderStatus(`Loaded ${top10.length} Top10 strategies from ${REPORT_URL}.`, false);
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
    renderStatus("Chart.js failed to load. Table data is still available.", true);
    return;
  }

  const labels = rows.map((item) => `#${item.rank} ${shortName(item.strategy_name)}`);
  renderBarChart("score-chart", labels, rows.map((item) => item.score), "Score", "#1f6feb");
  renderBarChart(
    "profit-chart",
    labels,
    rows.map((item) => item.total_test_net_profit),
    "Total Profit",
    "#16833a",
  );
}

function renderBarChart(canvasId, labels, values, label, color) {
  const canvas = document.getElementById(canvasId);
  new Chart(canvas, {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          label,
          data: values,
          backgroundColor: color,
          borderRadius: 4,
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
            maxRotation: 45,
            minRotation: 0,
          },
        },
        y: {
          beginAtZero: true,
        },
      },
    },
  });
}

function shortName(value) {
  return value.length > 18 ? `${value.slice(0, 18)}...` : value;
}

function formatNumber(value) {
  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 2,
  }).format(value);
}

function formatMoney(value) {
  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 0,
  }).format(value);
}

function formatPercent(value) {
  return new Intl.NumberFormat("en-US", {
    style: "percent",
    maximumFractionDigits: 1,
  }).format(value);
}
