(function () {
  "use strict";

  var DEBOUNCE_MS = 150;

  function initSuggest(wrap) {
    var input = wrap.querySelector('input[name="q"]');
    var list = wrap.querySelector('.search-suggest-list');
    var form = wrap.closest('form');
    if (!input || !list || !form) return;
    var langField = form.querySelector('input[name="lang"]');

    var debounceTimer = null;
    var controller = null;
    var cache = new Map();
    var items = [];
    var activeIndex = -1;

    function lang() {
      return langField ? langField.value : "en";
    }

    function hideList() {
      list.hidden = true;
      list.innerHTML = "";
      items = [];
      activeIndex = -1;
      input.setAttribute("aria-expanded", "false");
      input.removeAttribute("aria-activedescendant");
    }

    function updateActive() {
      var options = list.children;
      for (var i = 0; i < options.length; i++) {
        var link = options[i].querySelector("a");
        if (i === activeIndex) {
          link.classList.add("active");
          input.setAttribute("aria-activedescendant", link.id);
        } else {
          link.classList.remove("active");
        }
      }
      if (activeIndex === -1) {
        input.removeAttribute("aria-activedescendant");
      }
    }

    function render(data, query) {
      items = data;
      list.innerHTML = "";
      activeIndex = -1;

      if (!items.length) {
        hideList();
        return;
      }

      items.forEach(function (item, i) {
        var li = document.createElement("li");
        li.setAttribute("role", "presentation");

        var a = document.createElement("a");
        a.href = "/term/" + item.id;
        a.className = "search-suggest-item";
        a.id = "search-suggest-opt-" + i;
        a.setAttribute("role", "option");

        var matched = item.word.slice(0, query.length);
        var rest = item.word.slice(query.length);

        var strong = document.createElement("strong");
        strong.textContent = matched;
        a.appendChild(strong);
        a.appendChild(document.createTextNode(rest));

        li.appendChild(a);
        list.appendChild(li);
      });

      list.hidden = false;
      input.setAttribute("aria-expanded", "true");
    }

    function fetchSuggestions(query) {
      var key = lang() + "::" + query.toLowerCase();
      var cached = cache.get(key);
      if (cached) {
        render(cached, query);
        return;
      }

      if (controller) controller.abort();
      controller = new AbortController();

      var url = "/search_suggestions?q=" + encodeURIComponent(query) + "&lang=" + encodeURIComponent(lang());

      fetch(url, { signal: controller.signal })
        .then(function (resp) {
          return resp.ok ? resp.json() : [];
        })
        .then(function (data) {
          cache.set(key, data);
          // Guard against a slow response landing after the input changed again.
          if (input.value.trim() === query) {
            render(data, query);
          }
        })
        .catch(function (err) {
          if (err.name !== "AbortError") {
            console.error("search suggestions failed:", err);
          }
        });
    }

    input.addEventListener("input", function () {
      var query = input.value.trim();
      window.clearTimeout(debounceTimer);

      if (!query) {
        if (controller) controller.abort();
        hideList();
        return;
      }

      debounceTimer = window.setTimeout(function () {
        fetchSuggestions(query);
      }, DEBOUNCE_MS);
    });

    input.addEventListener("keydown", function (e) {
      if (list.hidden || !items.length) return;

      if (e.key === "ArrowDown") {
        e.preventDefault();
        activeIndex = Math.min(activeIndex + 1, items.length - 1);
        updateActive();
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        activeIndex = Math.max(activeIndex - 1, -1);
        updateActive();
      } else if (e.key === "Enter") {
        if (activeIndex >= 0) {
          e.preventDefault();
          list.children[activeIndex].querySelector("a").click();
        }
        // else: let the form submit normally.
      } else if (e.key === "Escape") {
        hideList();
      }
    });

    wrap.addEventListener("focusout", function (e) {
      if (!wrap.contains(e.relatedTarget)) {
        hideList();
      }
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".search-suggest-wrap").forEach(initSuggest);
  });
})();
