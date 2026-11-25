// accueil.js — the home page's search field opens Quarto's search overlay.
(function () {
  "use strict";

  function openSearch() {
    var trigger = document.querySelector("#quarto-search .aa-DetachedSearchButton") ||
      document.querySelector(".aa-DetachedSearchButton");
    if (trigger) {
      trigger.click();
    }
  }

  function init() {
    var field = document.querySelector(".hero-recherche");
    if (field) {
      field.addEventListener("click", openSearch);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
