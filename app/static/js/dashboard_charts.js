(function () {
  var el = document.getElementById("dashboard-charts");
  if (!el || typeof Chart === "undefined") return;
  var raw = el.getAttribute("data-charts");
  if (!raw) return;
  var data;
  try {
    data = JSON.parse(raw);
  } catch (e) {
    return;
  }

  var trim = data.trimestri || {};
  var buoni = data.buoni_stato || {};
  var isDark = document.documentElement.getAttribute("data-bs-theme") === "dark";
  var grid = isDark ? "rgba(255,255,255,0.12)" : "rgba(15,23,42,0.08)";
  var tick = isDark ? "#cbd5e1" : "#475569";

  var cassaEl = document.getElementById("chart-cassa-trimestre");
  if (cassaEl) {
    new Chart(cassaEl, {
      type: "bar",
      data: {
        labels: trim.labels || ["T1", "T2", "T3", "T4"],
        datasets: [
          {
            type: "bar",
            label: "Entrate",
            data: trim.entrate || [],
            backgroundColor: "rgba(25, 135, 84, 0.65)",
            borderRadius: 4,
            order: 2,
          },
          {
            type: "bar",
            label: "Uscite",
            data: trim.uscite || [],
            backgroundColor: "rgba(220, 53, 69, 0.65)",
            borderRadius: 4,
            order: 3,
          },
          {
            type: "line",
            label: "Saldo cassa (fine trim.)",
            data: trim.saldo_cassa || [],
            borderColor: "#0d6efd",
            backgroundColor: "rgba(13, 110, 253, 0.15)",
            tension: 0.25,
            yAxisID: "y1",
            order: 1,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: "index", intersect: false },
        plugins: {
          legend: { labels: { color: tick, boxWidth: 12 } },
        },
        scales: {
          x: { ticks: { color: tick }, grid: { color: grid } },
          y: {
            position: "left",
            ticks: { color: tick },
            grid: { color: grid },
            title: { display: true, text: "Entrate / uscite €", color: tick },
          },
          y1: {
            position: "right",
            ticks: { color: tick },
            grid: { drawOnChartArea: false },
            title: { display: true, text: "Saldo cassa €", color: tick },
          },
        },
      },
    });
  }

  var buoniEl = document.getElementById("chart-buoni-stato");
  if (buoniEl) {
    var palette = ["#6c757d", "#0d6efd", "#198754", "#212529", "#dc3545"];
    new Chart(buoniEl, {
      type: "doughnut",
      data: {
        labels: buoni.labels || [],
        datasets: [
          {
            data: buoni.values || [],
            backgroundColor: palette,
            borderWidth: 0,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "bottom",
            labels: { color: tick, boxWidth: 12 },
          },
        },
      },
    });
  }
})();
