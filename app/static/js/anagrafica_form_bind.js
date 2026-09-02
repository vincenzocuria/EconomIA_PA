(function () {
  if (!window.egAnagraficaAutocomplete) return;

  function bindField(selector, url, onSelect, onCreate) {
    var el = document.querySelector(selector);
    if (!el || !url) return;
    window.egAnagraficaAutocomplete.bind(el, {
      url: url,
      onSelect: onSelect,
      onCreate: onCreate,
      createHint: onCreate ? "Nuovo fornitore" : ""
    });
  }

  function applicaBeneficiario(form, nomeSel, cfSel, item) {
    var nome = form.querySelector(nomeSel);
    var cf = cfSel ? form.querySelector(cfSel) : null;
    if (nome) nome.value = item.label || "";
    if (cf) cf.value = item.cf_piva || "";
    if (nome) nome.dispatchEvent(new Event("change", { bubbles: true }));
  }

  function apriNuovoBeneficiario(form, nomeSel, cfSel, prefillNome) {
    if (!window.egAnagraficaModal) return;
    var nome = form.querySelector(nomeSel);
    var cf = cfSel ? form.querySelector(cfSel) : null;
    window.egAnagraficaModal.apriBeneficiario(
      {
        denominazione: prefillNome || (nome && nome.value) || "",
        cf_piva: (cf && cf.value) || ""
      },
      function (item) { applicaBeneficiario(form, nomeSel, cfSel, item); }
    );
  }

  function bindAggiungi(form, btnSel, nomeSel, cfSel) {
    var btn = form.querySelector(btnSel);
    if (!btn) return;
    btn.addEventListener("click", function () {
      apriNuovoBeneficiario(form, nomeSel, cfSel);
    });
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
      formBuono.getAttribute("data-ac-beneficiari"),
      null,
      function (q) { apriNuovoBeneficiario(formBuono, '[name="beneficiario"]', null, q); }
    );
    bindAggiungi(formBuono, '[data-eg-add="beneficiario"]', '[name="beneficiario"]', null);
  }

  var formMov = document.getElementById("form-movimento");
  if (formMov) {
    bindField(
      '#form-movimento [name="beneficiario_fornitore"]',
      formMov.getAttribute("data-ac-beneficiari"),
      function (item) { applicaBeneficiario(formMov, '[name="beneficiario_fornitore"]', '[name="cf_piva"]', item); },
      function (q) { apriNuovoBeneficiario(formMov, '[name="beneficiario_fornitore"]', '[name="cf_piva"]', q); }
    );
    bindAggiungi(formMov, '[data-eg-add="beneficiario"]', '[name="beneficiario_fornitore"]', '[name="cf_piva"]');
  }
})();
