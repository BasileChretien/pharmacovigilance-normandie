// tableaux.js — the boxes around tables (assets/filters/tableaux.lua, docs/tableaux.md).
// Loaded on every page (_quarto.yml). When a table is wider than its box, the box scrolls
// sideways; this script then:
// - shows the cue at an edge that hides columns (classes peut-gauche and peut-droite of the
//   box, drawn by theme.scss), and follows the box as it scrolls or changes size;
// - makes the box reachable with the keyboard, as a region named after the table, so that
//   the arrow keys scroll it (WCAG 2.1.1). A box that fits stays out of the tab order. A
//   region written in the page (the cytochrome grids) is left as it is;
// - gives the tables shown as cards (.tableau-cartes) their table roles back: browsers may
//   drop a table's rows and cells for screen readers once they are displayed as blocks.
// Without JavaScript the boxes still scroll, without the cue.
(function (factory) {
  "use strict";
  var api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api; // unit tests (tests/js/)
  } else if (typeof document !== "undefined") {
    api.init(document, window);
  }
})(function () {
  "use strict";

  // Rounding: a box scrolled to 0.4 px from its end is at its end.
  var MARGE = 1;
  var ROLES = [
    ["table", "table"],
    ["thead, tbody, tfoot", "rowgroup"],
    ["tr", "row"],
    ["thead th", "columnheader"],
    ["tbody th", "rowheader"],
    ["td", "cell"],
  ];

  // What the box shows: does it scroll, and is there more to see on each side?
  function etat(cadre) {
    var reste = cadre.scrollWidth - cadre.clientWidth;
    var resteBas = cadre.scrollHeight - cadre.clientHeight;
    var gauche = cadre.scrollLeft > MARGE;
    return {
      defile: reste > MARGE || resteBas > MARGE,
      gauche: reste > MARGE && gauche,
      droite: reste > MARGE && cadre.scrollLeft < reste - MARGE,
    };
  }

  // The region's name: the table's caption, or else the heading the table comes under.
  function nom(cadre) {
    var table = cadre.querySelector("table");
    var legende = table && table.querySelector("caption");
    var texte = legende ? legende.textContent.trim() : "";
    if (texte) return texte;
    for (var noeud = cadre; noeud && noeud.tagName !== "BODY"; noeud = noeud.parentElement) {
      for (var avant = noeud.previousElementSibling; avant; avant = avant.previousElementSibling) {
        if (/^H[1-6]$/.test(avant.tagName)) return "Tableau : " + avant.textContent.trim();
      }
    }
    return "Tableau";
  }

  function basculer(element, classe, oui) {
    if (oui) element.classList.add(classe);
    else element.classList.remove(classe);
  }

  function mettreAJour(boite, cadre, regionDeLaPage) {
    var e = etat(cadre);
    basculer(boite, "peut-gauche", e.gauche);
    basculer(boite, "peut-droite", e.droite);
    if (regionDeLaPage) return;
    if (e.defile && !cadre.hasAttribute("tabindex")) {
      cadre.setAttribute("tabindex", "0");
      cadre.setAttribute("role", "region");
      cadre.setAttribute("aria-label", nom(cadre));
    } else if (!e.defile && cadre.hasAttribute("tabindex")) {
      cadre.removeAttribute("tabindex");
      cadre.removeAttribute("role");
      cadre.removeAttribute("aria-label");
    }
  }

  function rendreRoles(boite) {
    ROLES.forEach(function (paire) {
      Array.prototype.forEach.call(boite.querySelectorAll(paire[0]), function (el) {
        el.setAttribute("role", paire[1]);
      });
    });
  }

  function suivre(boite, cadre, win) {
    var regionDeLaPage = cadre.hasAttribute("tabindex");
    var attente = false;
    var maj = function () {
      attente = false;
      mettreAJour(boite, cadre, regionDeLaPage);
    };
    // One update per frame, however fast the box scrolls.
    var plusTard = function () {
      if (attente) return;
      attente = true;
      if (win && win.requestAnimationFrame) win.requestAnimationFrame(maj);
      else maj();
    };
    cadre.addEventListener("scroll", plusTard, { passive: true });
    if (win && win.ResizeObserver) {
      // The box narrows with the screen; the table changes width when the filter hides rows.
      var observateur = new win.ResizeObserver(plusTard);
      observateur.observe(cadre);
      var table = cadre.querySelector("table");
      if (table) observateur.observe(table);
    } else if (win) {
      win.addEventListener("resize", plusTard);
    }
    maj();
  }

  function init(doc, win) {
    Array.prototype.forEach.call(doc.querySelectorAll(".tableau-defile"), function (boite) {
      var cadre = boite.querySelector(".tableau-defile-cadre");
      if (!cadre) return;
      if (boite.classList.contains("tableau-cartes")) rendreRoles(boite);
      suivre(boite, cadre, win);
    });
  }

  return { etat: etat, nom: nom, mettreAJour: mettreAJour, rendreRoles: rendreRoles, init: init };
});
