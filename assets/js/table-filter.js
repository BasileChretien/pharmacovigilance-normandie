// table-filter.js — a filter field above long tables (user panel, round 2: the
// interactions table and the cytochrome index were "a long table without a filter").
// In a page: wrap the table in ::: {.tableau-filtrable} ... ::: and load this script. A box may
// hold several tables (the three tables of the cytochrome grid): one field filters them all.
// With cible="premiere-colonne" only the first cell of a row is searched (the drug names of
// the grid, whose other cells hold "Puissant", "Modéré"…).
// Rows that do not hold every typed word are hidden; accents and case are ignored, so
// "erythromycine" finds "érythromycine". A status line gives the count, announced to
// screen readers once typing pauses rather than at every key. Without JavaScript the
// table is simply complete. Printing always shows every row (see theme.scss).
(function (factory) {
  "use strict";
  var api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api; // unit tests (tests/js/)
  } else if (typeof document !== "undefined") {
    api.init(document);
  }
})(function () {
  "use strict";

  var ANNOUNCE_DELAY_MS = 400;
  var DEFAULT_LABEL = "Filtrer ce tableau";
  var HELP = "Un ou plusieurs mots, par exemple un médicament ou une classe. Les accents sont facultatifs.";
  var HELP_FIRST_COLUMN = "Le nom d'un médicament, ou une partie de ce nom. Les accents sont facultatifs.";
  var FIRST_COLUMN = "premiere-colonne";

  // Letters that NFD does not split into a base letter and an accent, spelt out as the
  // cytochrome checker does (assets/js/cyp-verificateur.js): "oeil" finds "œil".
  var LIGATURES = { "œ": "oe", "æ": "ae", "ß": "ss", "ø": "o" };

  function fold(text) {
    return String(text).normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase()
      .replace(/[œæßø]/g, function (c) { return LIGATURES[c]; });
  }

  function matches(rowText, query) {
    var words = fold(query).split(/\s+/).filter(Boolean);
    var haystack = fold(rowText);
    return words.every(function (word) { return haystack.indexOf(word) !== -1; });
  }

  function countLabel(shown, total) {
    if (shown === 0) return "Aucune ligne ne correspond (" + total + " au total)";
    var noun = shown === 1 ? " ligne" : " lignes";
    return shown === total ? shown + noun : shown + noun + " sur " + total;
  }

  // Body rows of every table in the box.
  function bodyRows(box) {
    var rows = [];
    Array.prototype.forEach.call(box.querySelectorAll("table"), function (table) {
      Array.prototype.forEach.call(table.tBodies || [], function (body) {
        rows = rows.concat(Array.prototype.slice.call(body.rows));
      });
    });
    return rows;
  }

  // The text a row is searched on: the whole row, or its first cell only.
  function rowText(row, target) {
    if (target === FIRST_COLUMN && row.cells && row.cells.length) return row.cells[0].textContent;
    return row.textContent;
  }

  function element(doc, tag, attributes, text) {
    var node = doc.createElement(tag);
    Object.keys(attributes).forEach(function (name) { node.setAttribute(name, attributes[name]); });
    if (text) node.textContent = text;
    return node;
  }

  function enhance(doc, box, index) {
    var rows = bodyRows(box);
    if (!rows.length) return;
    var id = "filtre-tableau-" + (index + 1);
    // Each field needs its own label when a page has several tables:
    // ::: {.tableau-filtrable libelle="Filtrer l'index par médicament"}
    var label = box.getAttribute("data-libelle") || DEFAULT_LABEL;
    var target = box.getAttribute("data-cible");

    var field = element(doc, "div", { class: "filtre-tableau" });
    var input = element(doc, "input", {
      class: "form-control", type: "search", id: id, autocomplete: "off",
      spellcheck: "false", "aria-describedby": id + "-aide " + id + "-etat",
    });
    var status = element(doc, "p", { class: "filtre-tableau-etat", id: id + "-etat", role: "status" });
    field.appendChild(element(doc, "label", { class: "form-label", for: id }, label));
    field.appendChild(input);
    field.appendChild(element(doc, "p", { class: "filtre-tableau-aide", id: id + "-aide" },
      target === FIRST_COLUMN ? HELP_FIRST_COLUMN : HELP));
    field.appendChild(status);
    box.insertBefore(field, box.firstChild);

    var timer = null;
    status.textContent = countLabel(rows.length, rows.length);

    input.addEventListener("input", function () {
      var shown = 0;
      rows.forEach(function (row) {
        var keep = matches(rowText(row, target), input.value);
        row.hidden = !keep;
        if (keep) shown += 1;
      });
      clearTimeout(timer);
      timer = setTimeout(function () {
        status.textContent = countLabel(shown, rows.length);
      }, ANNOUNCE_DELAY_MS);
    });
  }

  function init(doc) {
    var boxes = doc.querySelectorAll(".tableau-filtrable");
    Array.prototype.forEach.call(boxes, function (box, index) { enhance(doc, box, index); });
  }

  return { fold: fold, matches: matches, countLabel: countLabel, bodyRows: bodyRows, rowText: rowText, init: init };
});
