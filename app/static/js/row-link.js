document.addEventListener("click", (e) => {
  const row = e.target.closest("tr[data-href]");
  if (!row) return;
  if (e.target.closest("a, button, input, select, textarea, label")) return;
  window.location.href = row.dataset.href;
});

document.addEventListener("keydown", (e) => {
  if (e.key !== "Enter" && e.key !== " ") return;
  const row = e.target.closest("tr[data-href]");
  if (!row || e.target !== row) return;
  e.preventDefault();
  window.location.href = row.dataset.href;
});
