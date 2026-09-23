(function () {
  var root = document.querySelector("[data-registro]");
  if (!root) return;
  var table = root.querySelector("table");
  var cerca = root.querySelector("[data-registro-cerca]");
  var conteggio = root.querySelector("[data-registro-conteggio]");
  var vuoto = root.querySelector("[data-registro-vuoto]");
  var pagine = root.querySelector("[data-registro-pagine]");
  var etichetta = root.querySelector("[data-pagina-label]");
  var btnPrev = root.querySelector('[data-pagina="prev"]');
  var btnNext = root.querySelector('[data-pagina="next"]');
  if (!table) return;
  var tbody = table.tBodies[0];
  if (!tbody) return;

  var perPagina = parseInt(root.getAttribute("data-per-pagina") || "25", 10);
  if (!perPagina || perPagina < 1) perPagina = 25;
  var pagina = 1;

  function righe() {
    return Array.prototype.filter.call(tbody.rows, function (tr) {
      return tr.hasAttribute("data-registro-riga");
    });
  }

  function testoRiga(tr) {
    return (tr.getAttribute("data-cerca") || tr.textContent || "").toLowerCase();
  }

  function aggiornaConteggio(visibili, totale) {
    if (!conteggio) return;
    if (!totale) {
      conteggio.textContent = "Nessun movimento";
      return;
    }
    conteggio.textContent = visibili === totale
      ? totale + (totale === 1 ? " movimento" : " movimenti")
      : visibili + " di " + totale + " movimenti";
  }

  function mostraPagina(match) {
    var totale = match.length;
    var nPagine = Math.max(1, Math.ceil(totale / perPagina));
    if (pagina > nPagine) pagina = nPagine;
    if (pagina < 1) pagina = 1;
    var inizio = (pagina - 1) * perPagina;
    var fine = inizio + perPagina;
    match.forEach(function (tr, i) {
      tr.hidden = i < inizio || i >= fine;
    });
    if (!pagine) return;
    pagine.hidden = totale === 0;
    if (etichetta && totale) {
      var da = inizio + 1;
      var a = Math.min(fine, totale);
      etichetta.textContent = da + "–" + a + " di " + totale;
    }
    if (btnPrev) btnPrev.disabled = pagina <= 1;
    if (btnNext) btnNext.disabled = pagina >= nPagine;
  }

  function applica(resetPagina) {
    if (resetPagina) pagina = 1;
    var q = (cerca && cerca.value || "").trim().toLowerCase();
    var tutte = righe();
    var match = [];
    tutte.forEach(function (tr) {
      var ok = !q || testoRiga(tr).indexOf(q) !== -1;
      if (!ok) tr.hidden = true;
      else match.push(tr);
    });
    if (vuoto) vuoto.hidden = !q || match.length !== 0;
    aggiornaConteggio(match.length, tutte.length);
    mostraPagina(match);
  }

  function valore(tr, col) {
    var cell = tr.querySelector('[data-col="' + col + '"]');
    if (!cell) return "";
    var raw = cell.getAttribute("data-sort") || "";
    if (cell.getAttribute("data-tipo") === "num") {
      var n = parseFloat(raw);
      return isNaN(n) ? 0 : n;
    }
    return raw;
  }

  function ordina(col, verso) {
    var tutte = righe();
    tutte.sort(function (a, b) {
      var va = valore(a, col);
      var vb = valore(b, col);
      if (va < vb) return verso === "asc" ? -1 : 1;
      if (va > vb) return verso === "asc" ? 1 : -1;
      return 0;
    });
    tutte.forEach(function (tr) { tbody.appendChild(tr); });
    applica(false);
  }

  root.querySelectorAll(".eg-sort").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var col = btn.getAttribute("data-sort");
      var verso = btn.getAttribute("aria-sort") === "ascending" ? "desc" : "asc";
      root.querySelectorAll(".eg-sort").forEach(function (altro) {
        altro.removeAttribute("aria-sort");
      });
      btn.setAttribute("aria-sort", verso === "asc" ? "ascending" : "descending");
      ordina(col, verso);
    });
  });

  if (btnPrev) {
    btnPrev.addEventListener("click", function () {
      if (pagina > 1) {
        pagina -= 1;
        applica(false);
      }
    });
  }
  if (btnNext) {
    btnNext.addEventListener("click", function () {
      pagina += 1;
      applica(false);
    });
  }
  if (cerca) {
    cerca.addEventListener("input", function () {
      applica(true);
    });
  }
  applica(true);
})();
