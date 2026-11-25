// frequences.js — interactive grids of people for the page comprendre/frequences.
// Two tools, found by their data-outil attribute:
//   data-outil="frequences": one radio button per frequency category of the RCP;
//   data-outil="placebo":    a fictitious example comparing a drug with a placebo.
// The grids are decorative (aria-hidden); the sentence under each grid, in an
// aria-live region, says the same thing in words.
(function () {
  "use strict";

  var INK = "#1b4f8a";
  var NEUTRAL = "#d0d4d9";

  var CATEGORIES = {
    "tres-frequent": {
      total: 100, sure: 10, maybe: 0,
      texte: "Très fréquent : plus d’une personne sur 10. Dans ce groupe de 100 personnes, 10 personnes ou plus ont l’effet."
    },
    "frequent": {
      total: 100, sure: 1, maybe: 8,
      texte: "Fréquent : de 1 à 10 personnes sur 100. Dans ce groupe de 100 personnes, au moins 1 personne a l’effet (en plein), et jusqu’à 9 (en hachuré)."
    },
    "peu-frequent": {
      total: 1000, sure: 1, maybe: 8,
      texte: "Peu fréquent : de 1 à 10 personnes sur 1 000. Dans ce groupe de 1 000 personnes, au moins 1 personne a l’effet, et jusqu’à 9."
    },
    "rare": {
      total: 1000, sure: 0, maybe: 1,
      texte: "Rare : de 1 à 10 personnes sur 10 000. Dans ce groupe de 1 000 personnes, au plus 1 personne a l’effet."
    },
    "tres-rare": {
      total: 1000, sure: 0, maybe: 0,
      texte: "Très rare : moins d’une personne sur 10 000. Dans ce groupe de 1 000 personnes, en général, personne n’a l’effet."
    },
    "indeterminee": {
      total: 0, sure: 0, maybe: 0,
      texte: "Fréquence indéterminée : les données ne permettent pas de l’estimer. Cela ne veut pas dire que l’effet est rare."
    }
  };

  // Fictitious example, labelled as such on the page.
  var PLACEBO = { total: 100, medicament: 12, placebo: 9 };

  var gridCount = 0;

  function pattern(id) {
    return '<defs><pattern id="' + id + '" width="4" height="4" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">' +
      '<rect width="4" height="4" fill="#ffffff"/><line x1="0" y1="0" x2="0" y2="4" stroke="' + INK + '" stroke-width="2"/></pattern></defs>';
  }

  function fillFor(i, sure, maybe, id) {
    if (i < sure) { return INK; }
    if (i < sure + maybe) { return "url(#" + id + ")"; }
    return NEUTRAL;
  }

  function person(x, y, fill) {
    var stroke = fill === NEUTRAL ? "none" : INK;
    // fill is INK, NEUTRAL or a url(#hachures-n) pattern reference.
    return '<g transform="translate(' + x + ',' + y + ')">' +
      '<circle cx="7" cy="4.5" r="4" fill="' + fill + '" stroke="' + stroke + '"/>' +
      '<rect x="1.5" y="10" width="11" height="13" rx="5" fill="' + fill + '" stroke="' + stroke + '"/></g>';
  }

  function dot(x, y, fill) {
    var stroke = fill === NEUTRAL ? "none" : INK;
    return '<circle cx="' + x + '" cy="' + y + '" r="3.6" fill="' + fill + '" stroke="' + stroke + '"/>';
  }

  // Draw `total` people (100 as figures, 1000 as dots); the first `sure` are
  // filled, the next `maybe` are hatched, the rest are neutral.
  function grid(total, sure, maybe) {
    if (total === 0) { return ""; }
    gridCount += 1;
    var id = "hachures-" + gridCount;
    var parts = [];
    var cols, step, w, h, i;
    if (total <= 100) {
      cols = 10; step = 24;
      for (i = 0; i < total; i++) {
        parts.push(person((i % cols) * step + 4, Math.floor(i / cols) * (step + 4) + 4, fillFor(i, sure, maybe, id)));
      }
      w = cols * step + 8; h = Math.ceil(total / cols) * (step + 4) + 8;
    } else {
      cols = 40; step = 11;
      for (i = 0; i < total; i++) {
        parts.push(dot((i % cols) * step + 8, Math.floor(i / cols) * step + 8, fillFor(i, sure, maybe, id)));
      }
      w = cols * step + 8; h = Math.ceil(total / cols) * step + 8;
    }
    return '<svg viewBox="0 0 ' + w + ' ' + h + '" width="' + w + '" height="' + h + '" focusable="false">' +
      pattern(id) + parts.join("") + "</svg>";
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
          " ont aussi mal à la tête (en hachuré). Le médicament n’en ajoute que " +
          (p.medicament - p.placebo) + " sur " + p.total + " (en plein).";
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
