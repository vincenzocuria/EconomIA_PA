(function () {
  if (!window.egAnagraficaAutocomplete) return;

  function bindField(selector, url, onSelect) {
    var el = document.querySelector(selector);
    if (!el || !url) return;
    window.egAnagraficaAutocomplete.bind(el, { url: url, onSelect: onSelect });
  }

  function setIfEmpty(form, name, value) {
    var el = form.querySelector('[name="' + name + '"]');
    if (!el || !(value || "").trim()) return;
    if (!(el.value || "").trim()) {
      el.value = value;
    }
  }

  function setValue(form, name, value) {
    var el = form.querySelector('[name="' + name + '"]');
    if (!el || !(value || "").trim()) return;
    el.value = value;
  }

  var formBuono = document.getElementById("form-buono");
  if (formBuono) {
    bindField(
      '#form-buono [name="richiedente"]',
      formBuono.getAttribute("data-ac-richiedenti"),
      function (item) {
        setIfEmpty(formBuono, "ufficio_richiedente", item.ufficio);
        setIfEmpty(formBuono, "responsabile_ufficio", item.responsabile);
      }
    );
    bindField(
      '#form-buono [name="ufficio_richiedente"]',
      formBuono.getAttribute("data-ac-uffici"),
      function (item) {
        setValue(formBuono, "responsabile_ufficio", item.responsabile);
      }
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
