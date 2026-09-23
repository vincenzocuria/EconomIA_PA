(function () {
  var form = document.querySelector("[data-filtro-periodo]");
  if (!form) return;
  var sel = form.querySelector("#f-periodo");
  var blocchi = form.querySelectorAll("[data-intervallo]");
  if (!sel || !blocchi.length) return;

  function sync() {
    var attivo = sel.value === "intervallo";
    blocchi.forEach(function (blocco) {
      blocco.hidden = !attivo;
      blocco.querySelectorAll("input").forEach(function (input) {
        input.disabled = !attivo;
      });
    });
  }

  sel.addEventListener("change", sync);
  sync();
})();
