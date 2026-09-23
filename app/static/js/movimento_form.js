(function () {
  var form = document.getElementById("form-movimento");
  if (!form) return;

  var tipo = form.querySelector('[name="tipo"]');
  var blocco = document.getElementById("blocco-banca");
  var bloccoSpesa = document.getElementById("blocco-spesa");
  var sezionale = form.querySelector('[name="sezionale_id"]');
  var numero = form.querySelector('[name="numero_progressivo"]');
  var urlProssimo = form.getAttribute("data-prossimo-url");
  var anno = form.getAttribute("data-anno");
  var tipiBanca = { prelievo_banca: 1, versamento_banca: 1 };
  var defaultsSez = {};
  try {
    defaultsSez = JSON.parse(form.getAttribute("data-sezionali-default") || "{}");
  } catch (e) {
    defaultsSez = {};
  }

  function svuotaCampo(el) {
    if (!el) return;
    if (el.type === "checkbox" || el.type === "radio") {
      el.checked = false;
      return;
    }
    if (el.tagName === "SELECT") {
      el.value = el.querySelector('option[value="0"]') ? "0" : "";
      return;
    }
    if (el.type !== "file") el.value = "";
  }

  function svuotaDentro(box) {
    if (!box) return;
    box.querySelectorAll("input, select, textarea").forEach(svuotaCampo);
  }

  function aggiornaBanca() {
    if (!tipo) return;
    var bancario = !!tipiBanca[tipo.value];
    if (blocco) blocco.classList.toggle("d-none", !bancario);
    if (bloccoSpesa) bloccoSpesa.classList.toggle("d-none", bancario);
    if (bancario) svuotaDentro(bloccoSpesa);
    else svuotaDentro(blocco);
  }

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

  function applicaSezionaleDefault() {
    if (!tipo || !sezionale || !defaultsSez) return;
    var id = defaultsSez[tipo.value];
    if (id) sezionale.value = String(id);
    proponiNumero();
  }

  if (tipo) {
    tipo.addEventListener("change", function () {
      aggiornaBanca();
      if (form.getAttribute("data-nuovo") === "1") {
        applicaSezionaleDefault();
      }
    });
  }
  if (sezionale) {
    sezionale.addEventListener("change", proponiNumero);
  }

  aggiornaBanca();
})();
