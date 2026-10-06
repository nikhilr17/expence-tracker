document.addEventListener("DOMContentLoaded", () => {
  const data = window.dashboardData;
  if (!data || typeof Chart === "undefined") return;
  new Chart(document.getElementById("incomeExpenseChart"), { type: "bar", data: { labels: ["Income", "Expenses"], datasets: [{ data: [data.income, data.expenses], backgroundColor: ["#198754", "#dc3545"] }] }, options: { responsive: true, plugins: { legend: { display: false } } } });
  new Chart(document.getElementById("categoryChart"), { type: "doughnut", data: { labels: data.categoryLabels, datasets: [{ data: data.categoryValues }] }, options: { responsive: true } });
  new Chart(document.getElementById("monthlyExpenseChart"), { type: "line", data: { labels: data.monthly.map(item => item.label), datasets: [{ label: "Expenses", data: data.monthly.map(item => item.amount), borderColor: "#dc3545", backgroundColor: "rgba(220,53,69,.15)", fill: true, tension: .25 }] }, options: { responsive: true } });
});
