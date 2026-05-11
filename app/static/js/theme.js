(function () {
  const key = "economia_pa_theme";
  function apply(t) {
    document.documentElement.setAttribute("data-bs-theme", t);
    localStorage.setItem(key, t);
  }
  const saved = localStorage.getItem(key);
  if (saved === "dark" || saved === "light") {
    apply(saved);
  }
  document.addEventListener("DOMContentLoaded", function () {
    const btn = document.getElementById("toggleTheme");
    if (!btn) return;
    btn.addEventListener("click", function () {
      const cur = document.documentElement.getAttribute("data-bs-theme") || "light";
      apply(cur === "dark" ? "light" : "dark");
    });
  });
})();
