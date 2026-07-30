(function () {
  if (!window.egAnagraficaAutocomplete) return;

  function bindField(selector, url, onSelect) {
    var el = document.querySelector(selector);
    if (!el || !url) return;
    window.egAnagraficaAutocomplete.bind(el, { url: url, onSelect: onSelect });
  }

  var formBuono = document.getElementById("form-buono");
  if (formBuono) {
    bindField(
      '#form-buono [name="richiedente"]',
      formBuono.getAttribute("data-ac-richiedenti"),
      function (item) {
        var uff = formBuono.querySelector('[name="ufficio_richiedente"]');
        if (uff && item.ufficio && !(uff.value || "").trim()) {
          uff.value = item.ufficio;
        }
      }
    );
    bindField(
      '#form-buono [name="ufficio_richiedente"]',
      formBuono.getAttribute("data-ac-uffici")
    );
    bindField(
      '#form-buono [name="beneficiario"]',
      formBuono.getAttribute("data-ac-beneficiari")
    );
  }

  var formMov = document.getElementById("form-movimento");
  if (formMov) {
    bindField(
      '#form-movimento [name="beneficiario_fornitore"]',
      formMov.getAttribute("data-ac-beneficiari"),
      function (item) {
        var piva = formMov.querySelector('[name="cf_piva"]');
        if (piva && item.cf_piva) {
          piva.value = item.cf_piva;
        }
      }
    );
  }
})();
