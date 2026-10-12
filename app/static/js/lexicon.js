(function () {
  "use strict";

  var jumpbar = document.querySelector(".lexicon-jumpbar");
  if (!jumpbar) return;

  var navbar = document.querySelector("nav.navbar.fixed-top");

  function updateOffset() {
    // The fixed navbar wraps to two rows on narrow viewports, and how narrow
    // depends on the language (the site name is much longer in some). Measure
    // it rather than assuming a single-row height, or the sticky jump bar
    // sticks too high and slides under/over the navbar when scrolling.
    if (navbar) {
      var navHeight = navbar.getBoundingClientRect().height;
      document.documentElement.style.setProperty("--lexicon-navbar-height", navHeight + "px");
    }

    var stickyTop = parseFloat(getComputedStyle(jumpbar).top) || 0;
    var offset = stickyTop + jumpbar.getBoundingClientRect().height + 16;
    document.documentElement.style.setProperty("--lexicon-jumpbar-offset", offset + "px");
  }

  updateOffset();
  window.addEventListener("resize", updateOffset);
  window.addEventListener("load", updateOffset);
  if (document.fonts && document.fonts.ready) {
    document.fonts.ready.then(updateOffset);
  }
})();
