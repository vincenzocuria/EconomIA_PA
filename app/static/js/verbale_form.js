(function () {
  var form = document.getElementById("form-verbale");
  if (!form) return;
  var trim = form.querySelector('[name="trimestre"]');
  var oggetto = form.querySelector('[name="oggetto"]');
  var anno = form.getAttribute("data-anno");
  if (!trim || !oggetto || !anno) return;

  var pref = "VERIFICA DI CASSA ECONOMALE — TRIMESTRE ";
  var reDefault = /^VERIFICA DI CASSA ECONOMALE — TRIMESTRE \d+ \d+$/;

  function syncOggetto() {
    var t = trim.value;
    if (!t) return;
    var cur = (oggetto.value || "").trim();
    if (!cur || reDefault.test(cur)) {
      oggetto.value = pref + t + " " + anno;
    }
  }

  trim.addEventListener("change", syncOggetto);
})();
