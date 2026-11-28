// Tests for assets/js/tableaux.js (cue and keyboard access of the boxes around tables,
// docs/tableaux.md). Run: npm run test:js
import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const tx = require("../../assets/js/tableaux.js");

// A box element: classes, attributes, scroll metrics and the elements a selector finds.
function element(tag, { found = {}, text = "", ...metrics } = {}) {
  const classes = new Set();
  const attrs = new Map();
  const listeners = {};
  return {
    tagName: tag.toUpperCase(),
    textContent: text,
    parentElement: null,
    previousElementSibling: null,
    scrollWidth: 0, clientWidth: 0, scrollHeight: 0, clientHeight: 0, scrollLeft: 0,
    ...metrics,
    classList: {
      add: (c) => classes.add(c),
      remove: (c) => classes.delete(c),
      contains: (c) => classes.has(c),
    },
    classes,
    setAttribute: (k, v) => attrs.set(k, String(v)),
    getAttribute: (k) => (attrs.has(k) ? attrs.get(k) : null),
    hasAttribute: (k) => attrs.has(k),
    removeAttribute: (k) => attrs.delete(k),
    querySelector: (sel) => (found[sel] || [])[0] || null,
    querySelectorAll: (sel) => found[sel] || [],
    addEventListener: (type, fn) => { (listeners[type] = listeners[type] || []).push(fn); },
    fire: (type) => (listeners[type] || []).forEach((fn) => fn({ type })),
  };
}

// A table of 600 px in a box of 300 px, scrolled to `left`.
function wide(left = 0, caption = "Tableau 1. Substrats") {
  const legende = element("caption", { text: `  ${caption}  ` });
  const table = element("table", { found: { caption: caption ? [legende] : [] } });
  const cadre = element("div", { scrollWidth: 600, clientWidth: 300, scrollLeft: left, found: { table: [table] } });
  const boite = element("div", { found: { ".tableau-defile-cadre": [cadre] } });
  return { boite, cadre, table };
}

test("a table that fits: no cue, nothing to scroll", () => {
  const cadre = element("div", { scrollWidth: 300, clientWidth: 300 });
  assert.deepEqual(tx.etat(cadre), { defile: false, gauche: false, droite: false });
});

test("a wider table shows more on the right at first, on both sides in the middle, on the left at the end", () => {
  assert.deepEqual(tx.etat(wide(0).cadre), { defile: true, gauche: false, droite: true });
  assert.deepEqual(tx.etat(wide(150).cadre), { defile: true, gauche: true, droite: true });
  assert.deepEqual(tx.etat(wide(300).cadre), { defile: true, gauche: true, droite: false });
});

test("half a pixel from either end counts as the end", () => {
  assert.equal(tx.etat(wide(0.5).cadre).gauche, false);
  assert.equal(tx.etat(wide(299.5).cadre).droite, false);
});

test("a box that only scrolls down (a grid's rows) scrolls, without a side cue", () => {
  const cadre = element("div", { scrollWidth: 300, clientWidth: 300, scrollHeight: 900, clientHeight: 500 });
  assert.deepEqual(tx.etat(cadre), { defile: true, gauche: false, droite: false });
});

test("a box that scrolls becomes a named region in the tab order, and leaves it once it fits", () => {
  const { boite, cadre } = wide(0);
  tx.mettreAJour(boite, cadre, false);
  assert.ok(boite.classList.contains("peut-droite"));
  assert.ok(!boite.classList.contains("peut-gauche"));
  assert.equal(cadre.getAttribute("tabindex"), "0");
  assert.equal(cadre.getAttribute("role"), "region");
  assert.equal(cadre.getAttribute("aria-label"), "Tableau 1. Substrats");

  cadre.clientWidth = 600; // the screen turned to landscape
  tx.mettreAJour(boite, cadre, false);
  assert.ok(!boite.classList.contains("peut-droite"));
  assert.equal(cadre.hasAttribute("tabindex"), false);
  assert.equal(cadre.hasAttribute("role"), false);
  assert.equal(cadre.hasAttribute("aria-label"), false);
});

test("a region written in the page keeps its attributes, and still gets the cue", () => {
  const { boite, cadre } = wide(0);
  cadre.setAttribute("tabindex", "0");
  cadre.setAttribute("aria-label", "Tableau 1 : substrats");
  cadre.clientWidth = 600;
  tx.mettreAJour(boite, cadre, true);
  assert.equal(cadre.getAttribute("aria-label"), "Tableau 1 : substrats");
  assert.equal(cadre.getAttribute("tabindex"), "0");
  cadre.clientWidth = 300;
  tx.mettreAJour(boite, cadre, true);
  assert.ok(boite.classList.contains("peut-droite"));
});

test("without a caption, the region is named after the heading the table comes under", () => {
  const { cadre } = wide(0, "");
  const h2 = element("h2", { text: "Où chercher quoi ?" });
  const p = element("p", { text: "Intro" });
  p.previousElementSibling = h2;
  const boite = element("div");
  boite.previousElementSibling = p;
  cadre.parentElement = boite;
  boite.parentElement = element("body");
  assert.equal(tx.nom(cadre), "Tableau : Où chercher quoi ?");
});

test("with neither caption nor heading, the region is called Tableau", () => {
  const { cadre } = wide(0, "");
  cadre.parentElement = element("body");
  assert.equal(tx.nom(cadre), "Tableau");
});

test("tables shown as cards get their table roles back", () => {
  const cells = { table: [element("table")], "thead, tbody, tfoot": [element("thead"), element("tbody")],
    tr: [element("tr")], "thead th": [element("th")], "tbody th": [element("th")], td: [element("td")] };
  const boite = element("div", { found: cells });
  tx.rendreRoles(boite);
  assert.equal(cells.table[0].getAttribute("role"), "table");
  assert.deepEqual(cells["thead, tbody, tfoot"].map((e) => e.getAttribute("role")), ["rowgroup", "rowgroup"]);
  assert.equal(cells.tr[0].getAttribute("role"), "row");
  assert.equal(cells["thead th"][0].getAttribute("role"), "columnheader");
  assert.equal(cells["tbody th"][0].getAttribute("role"), "rowheader");
  assert.equal(cells.td[0].getAttribute("role"), "cell");
});

test("init follows each box: the cue moves as the box scrolls", () => {
  const { boite, cadre } = wide(0);
  boite.classList.add("tableau-cartes");
  const doc = { querySelectorAll: (sel) => (sel === ".tableau-defile" ? [boite] : []) };
  const win = { requestAnimationFrame: (fn) => fn() }; // no ResizeObserver: falls back to resize
  win.addEventListener = (type, fn) => { win[type] = fn; };
  tx.init(doc, win);
  assert.ok(boite.classList.contains("peut-droite"));
  cadre.scrollLeft = 300;
  cadre.fire("scroll");
  assert.ok(boite.classList.contains("peut-gauche"));
  assert.ok(!boite.classList.contains("peut-droite"));
  cadre.clientWidth = 600;
  win.resize();
  assert.ok(!boite.classList.contains("peut-gauche"));
});
