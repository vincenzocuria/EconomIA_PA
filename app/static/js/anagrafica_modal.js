(function () {
  function csrfToken() {
    var m = document.querySelector('meta[name="csrf-token"]');
    return m ? m.getAttribute("content") : "";
  }

  function el(id) {
    return document.getElementById(id);
  }

  function mostraErrore(msg) {
    var box = el("eg-ben-errore");
    if (!box) return;
    box.textContent = msg || "";
    box.classList.toggle("d-none", !msg);
  }

  function apriBeneficiario(prefill, onSaved) {
    var modalEl = el("modal-nuovo-beneficiario");
    if (!modalEl || !window.bootstrap) return;
    el("eg-ben-denominazione").value = (prefill && prefill.denominazione) || "";
    el("eg-ben-cf").value = (prefill && prefill.cf_piva) || "";
    mostraErrore("");
    modalEl._egOnSaved = onSaved;
    window.bootstrap.Modal.getOrCreateInstance(modalEl).show();
    setTimeout(function () { el("eg-ben-denominazione").focus(); }, 180);
  }

  function chiudi() {
    var modalEl = el("modal-nuovo-beneficiario");
    if (!modalEl || !window.bootstrap) return;
    var inst = window.bootstrap.Modal.getInstance(modalEl);
    if (inst) inst.hide();
  }

  function salva() {
    var modalEl = el("modal-nuovo-beneficiario");
    var url = modalEl && modalEl.getAttribute("data-salva-url");
    var btn = el("eg-ben-salva");
    if (!url) return;
    var body = {
      denominazione: (el("eg-ben-denominazione").value || "").trim(),
      cf_piva: (el("eg-ben-cf").value || "").trim()
    };
    if (!body.denominazione) {
      mostraErrore("Inserisci la denominazione del fornitore.");
      el("eg-ben-denominazione").focus();
      return;
    }
    mostraErrore("");
    if (btn) btn.disabled = true;
    fetch(url, {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken()
      },
      body: JSON.stringify(body)
    })
      .then(function (r) {
        return r.json().then(function (data) {
          return { okHttp: r.ok, data: data };
        });
      })
      .then(function (res) {
        if (!res.okHttp || !res.data || !res.data.ok || !res.data.item) {
          mostraErrore((res.data && res.data.error) || "Salvataggio non riuscito.");
          return;
        }
        var cb = modalEl._egOnSaved;
        chiudi();
        if (typeof cb === "function") cb(res.data.item);
      })
      .catch(function () {
        mostraErrore("Salvataggio non riuscito.");
      })
      .finally(function () {
        if (btn) btn.disabled = false;
      });
  }

  var modalEl = el("modal-nuovo-beneficiario");
  if (modalEl) {
    var btn = el("eg-ben-salva");
    if (btn) btn.addEventListener("click", salva);
    modalEl.addEventListener("keydown", function (e) {
      if (e.key === "Enter") {
        e.preventDefault();
        salva();
      }
    });
  }

  window.egAnagraficaModal = {
    apriBeneficiario: apriBeneficiario
  };
})();
