(function () {
  var form = document.getElementById("form-buono");
  if (!form) return;
  var sezionale = form.querySelector('[name="sezionale_id"]');
  var numero = form.querySelector('[name="numero_progressivo"]');
  var urlProssimo = form.getAttribute("data-prossimo-url");
  var anno = form.getAttribute("data-anno");

  function proponiNumero() {
    if (!urlProssimo || !sezionale || !numero || !anno) return;
    if (form.getAttribute("data-lock-numero") === "1") return;
    var sid = sezionale.value;
    if (!sid) return;
    var u = urlProssimo + "?anno=" + encodeURIComponent(anno) + "&sezionale_id=" + encodeURIComponent(sid);
    fetch(u, { headers: { Accept: "application/json" } })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data && data.numero) numero.value = data.numero;
      })
      .catch(function () {});
  }

  if (sezionale) sezionale.addEventListener("change", proponiNumero);
})();
