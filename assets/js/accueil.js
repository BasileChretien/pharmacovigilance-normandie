// accueil.js — home page: the search field opens Quarto's search overlay, and the map
// of Normandy is animated, with a pause button.
(function () {
  "use strict";

  function openSearch() {
    var trigger = document.querySelector("#quarto-search .aa-DetachedSearchButton") ||
      document.querySelector(".aa-DetachedSearchButton");
    if (trigger) {
      trigger.click();
    }
  }

  // The map moves only with JavaScript and never under reduced motion. Motion lasting
  // over 5 seconds needs a way to pause it (WCAG 2.2.2, RGAA 13.8): the button below.
  function initSignal() {
    var figure = document.querySelector(".hero-figure");
    if (!figure || !figure.querySelector("svg")) return;
    if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    var labels = ["Mettre l'animation en pause", "Relancer l'animation"];
    var button = document.createElement("button");
    button.type = "button";
    button.className = "btn btn-sm btn-outline-primary signal-pause";
    button.textContent = labels[0];
    button.addEventListener("click", function () {
      var paused = figure.classList.toggle("signal-en-pause");
      button.textContent = labels[paused ? 1 : 0];
    });
    figure.appendChild(button);
    figure.classList.add("signal-anime");
  }

  function init() {
    var field = document.querySelector(".hero-recherche");
    if (field) {
      field.addEventListener("click", openSearch);
    }
    initSignal();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
