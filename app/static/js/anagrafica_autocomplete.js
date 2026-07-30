(function () {
  function debounce(fn, ms) {
    var t;
    return function () {
      var ctx = this;
      var args = arguments;
      clearTimeout(t);
      t = setTimeout(function () { fn.apply(ctx, args); }, ms);
    };
  }

  function wrapInput(input) {
    if (input.parentElement && input.parentElement.classList.contains("eg-ac-wrap")) {
      return input.parentElement;
    }
    var wrap = document.createElement("div");
    wrap.className = "eg-ac-wrap";
    input.parentNode.insertBefore(wrap, input);
    wrap.appendChild(input);
    return wrap;
  }

  function bindAutocomplete(input, opts) {
    if (!input || !opts || !opts.url) return;
    var wrap = wrapInput(input);
    var list = document.createElement("ul");
    list.className = "eg-ac-list";
    list.hidden = true;
    wrap.appendChild(list);
    var active = -1;
    var items = [];

    function close() {
      list.hidden = true;
      list.innerHTML = "";
      active = -1;
      items = [];
    }

    function applyItem(item) {
      input.value = item.label || "";
      if (opts.onSelect) opts.onSelect(item);
      close();
      input.dispatchEvent(new Event("change", { bubbles: true }));
    }

    function render() {
      list.innerHTML = "";
      if (!items.length) {
        close();
        return;
      }
      items.forEach(function (item, idx) {
        var li = document.createElement("li");
        li.className = "eg-ac-item" + (idx === active ? " is-active" : "");
        var main = document.createElement("span");
        main.className = "eg-ac-main";
        main.textContent = item.label || "";
        li.appendChild(main);
        var hint = item.hint || item.cf_piva || item.ufficio || "";
        if (hint) {
          var sub = document.createElement("span");
          sub.className = "eg-ac-hint";
          sub.textContent = hint;
          li.appendChild(sub);
        }
        li.addEventListener("mousedown", function (e) {
          e.preventDefault();
          applyItem(item);
        });
        list.appendChild(li);
      });
      list.hidden = false;
    }

    var fetchItems = debounce(function () {
      var q = (input.value || "").trim();
      if (q.length < 1) {
        close();
        return;
      }
      var u = opts.url + (opts.url.indexOf("?") >= 0 ? "&" : "?") + "q=" + encodeURIComponent(q);
      fetch(u, { headers: { Accept: "application/json" } })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          items = (data && data.items) || [];
          active = -1;
          render();
        })
        .catch(function () { close(); });
    }, 180);

    input.setAttribute("autocomplete", "off");
    input.addEventListener("input", fetchItems);
    input.addEventListener("keydown", function (e) {
      if (list.hidden || !items.length) return;
      if (e.key === "ArrowDown") {
        e.preventDefault();
        active = (active + 1) % items.length;
        render();
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        active = (active - 1 + items.length) % items.length;
        render();
      } else if (e.key === "Enter" && active >= 0) {
        e.preventDefault();
        applyItem(items[active]);
      } else if (e.key === "Escape") {
        close();
      }
    });
    input.addEventListener("blur", function () {
      setTimeout(close, 120);
    });
  }

  window.egAnagraficaAutocomplete = {
    bind: bindAutocomplete
  };
})();
