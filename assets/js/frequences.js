// frequences.js — interactive grids of people for the page comprendre/frequences.
// Two tools, found by their data-outil attribute:
//   data-outil="frequences": one radio button per frequency category of the RCP;
//   data-outil="placebo":    a fictitious example comparing a drug with a placebo.
// The grids are decorative (aria-hidden). The sentence under each grid, in an
// aria-live region, says the same thing in words, without visual references
// (the user panel showed "en hachuré" means nothing to a screen-reader user).
// Codes, readable in grey scale and by colour-blind readers: filled = has the
// effect; hollow ring = may have it; light grey = does not have it.
(function () {
  "use strict";

  var INK = "#0a5c9e";
  var NEUTRAL = "#c9d8e2";
  var SURE = "sure";
  var MAYBE = "maybe";
  var NONE = "none";

  var CATEGORIES = {
    "tres-frequent": {
      total: 100, sure: 10, maybe: 0,
      texte: "Très fréquent : plus d’une personne sur 10. Dans un groupe de 100 personnes, 10 personnes ou plus ont l’effet."
    },
    "frequent": {
      total: 100, sure: 1, maybe: 8,
      texte: "Fréquent : de 1 à 10 personnes sur 100. Dans un groupe de 100 personnes, au moins 1 personne a l’effet, et jusqu’à 9."
    },
    "peu-frequent": {
      total: 1000, sure: 1, maybe: 8,
      texte: "Peu fréquent : de 1 à 10 personnes sur 1 000. Dans un groupe de 1 000 personnes, au moins 1 personne a l’effet, et jusqu’à 9."
    },
    "rare": {
      total: 1000, sure: 0, maybe: 1,
      texte: "Rare : de 1 à 10 personnes sur 10 000. Dans un groupe de 1 000 personnes, au plus 1 personne a l’effet."
    },
    "tres-rare": {
      total: 1000, sure: 0, maybe: 0,
      texte: "Très rare : moins d’une personne sur 10 000. Dans un groupe de 1 000 personnes, en général, personne n’a l’effet."
    },
    "indeterminee": {
      total: 0, sure: 0, maybe: 0,
      texte: "Fréquence indéterminée : les données ne permettent pas de l’estimer. Cela ne veut pas dire que l’effet est rare."
    }
  };

  // Fictitious example, labelled as such on the page.
  var PLACEBO = { total: 100, medicament: 12, placebo: 9 };

  function stateFor(i, sure, maybe) {
    if (i < sure) { return SURE; }
    if (i < sure + maybe) { return MAYBE; }
    return NONE;
  }

  // A hollow ring has no fill: Dark Reader lightens small shapes, and a white fill would
  // look like the grey of the people who do not have the effect (docs/mode-sombre.md).
  // The dark theme maps these colours (assets/theme-sombre.scss, $pv-figures-sombre).
  function paint(state) {
    if (state === SURE) { return 'fill="' + INK + '"'; }
    if (state === MAYBE) { return 'fill="none" stroke="' + INK + '" stroke-width="2.2"'; }
    return 'fill="' + NEUTRAL + '"';
  }

  function person(x, y, state) {
    var p = paint(state);
    return '<g transform="translate(' + x + ',' + y + ')">' +
      '<circle cx="9" cy="6" r="5" ' + p + '/>' +
      '<rect x="2.5" y="13" width="13" height="15" rx="6" ' + p + '/></g>';
  }

  function dot(x, y, state) {
    return '<circle cx="' + x + '" cy="' + y + '" r="4.8" ' + paint(state) + '/>';
  }

  // Draw `total` people: 100 as figures (10 x 10), 1000 as dots (25 x 40, so the
  // grid never needs horizontal scrolling at 200 % zoom).
  function grid(total, sure, maybe) {
    if (total === 0) { return ""; }
    var parts = [];
    var cols, step, w, h, i;
    if (total <= 100) {
      cols = 10; step = 30;
      for (i = 0; i < total; i++) {
        parts.push(person((i % cols) * step + 4, Math.floor(i / cols) * (step + 6) + 4, stateFor(i, sure, maybe)));
      }
      w = cols * step + 8; h = Math.ceil(total / cols) * (step + 6) + 8;
    } else {
      cols = 25; step = 14;
      for (i = 0; i < total; i++) {
        parts.push(dot((i % cols) * step + 9, Math.floor(i / cols) * step + 9, stateFor(i, sure, maybe)));
      }
      w = cols * step + 8; h = Math.ceil(total / cols) * step + 8;
    }
    return '<svg viewBox="0 0 ' + w + ' ' + h + '" width="' + w + '" height="' + h + '" focusable="false">' +
      parts.join("") + "</svg>";
  }

  function setupFrequences(root) {
    var drawing = root.querySelector(".frequences-grille");
    var summary = root.querySelector(".frequences-resume");
    function render(key) {
      var c = CATEGORIES[key];
      drawing.innerHTML = grid(c.total, c.sure, c.maybe);
      summary.textContent = c.texte;
    }
    root.addEventListener("change", function (event) {
      if (event.target && event.target.name === "frequence") { render(event.target.value); }
    });
    var checked = root.querySelector('input[name="frequence"]:checked');
    render(checked ? checked.value : "tres-frequent");
  }

  function setupPlacebo(root) {
    var drawing = root.querySelector(".frequences-grille");
    var summary = root.querySelector(".frequences-resume");
    var toggle = root.querySelector('input[type="checkbox"]');
    function render() {
      var p = PLACEBO;
      if (toggle.checked) {
        drawing.innerHTML = grid(p.total, p.medicament - p.placebo, p.placebo);
        summary.textContent = "Avec le placebo, " + p.placebo + " personnes sur " + p.total +
          " ont aussi mal à la tête. Le médicament n’en ajoute que " + (p.medicament - p.placebo) +
          " sur " + p.total + ".";
      } else {
        drawing.innerHTML = grid(p.total, p.medicament, 0);
        summary.textContent = "Avec le médicament, " + p.medicament + " personnes sur " + p.total +
          " ont mal à la tête. C’est ce chiffre que le RCP indique.";
      }
    }
    toggle.addEventListener("change", render);
    render();
  }

  function init() {
    var i;
    var tools = document.querySelectorAll('[data-outil="frequences"]');
    for (i = 0; i < tools.length; i++) { setupFrequences(tools[i]); }
    var placebos = document.querySelectorAll('[data-outil="placebo"]');
    for (i = 0; i < placebos.length; i++) { setupPlacebo(placebos[i]); }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
