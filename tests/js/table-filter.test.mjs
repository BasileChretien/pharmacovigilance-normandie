// Tests for assets/js/table-filter.js (row filter of long tables). Run: npm run test:js
import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const tf = require("../../assets/js/table-filter.js");

test("fold drops accents and case", () => {
  assert.equal(tf.fold("Kétoprofène, ÉRYTHROMYCINE"), "ketoprofene, erythromycine");
});

test("fold spells out œ, æ, ß and ø, as the cytochrome checker does", () => {
  assert.equal(tf.fold("Œstrogènes, cœur, Ægle, Straße, Søren"), "oestrogenes, coeur, aegle, strasse, soren");
  assert.ok(tf.matches("Œstrogènes conjugués", "oestrogenes"));
});

test("a row matches when it holds every typed word, in any order", () => {
  const row = "Simvastatine + inhibiteurs puissants du CYP3A4 (clarithromycine, érythromycine)";
  assert.ok(tf.matches(row, "clarithromycine simvastatine"));
  assert.ok(tf.matches(row, "erythromycine")); // typed without its accent
  assert.ok(!tf.matches(row, "simvastatine rifampicine"));
});

test("an empty or blank query matches every row", () => {
  assert.ok(tf.matches("Lévothyroxine + fer", ""));
  assert.ok(tf.matches("Lévothyroxine + fer", "   "));
});

test("the status line counts rows in French, singular and plural", () => {
  assert.equal(tf.countLabel(16, 16), "16 lignes");
  assert.equal(tf.countLabel(1, 16), "1 ligne sur 16");
  assert.equal(tf.countLabel(3, 16), "3 lignes sur 16");
  assert.equal(tf.countLabel(0, 16), "Aucune ligne ne correspond (16 au total)");
});

test("a box with several tables filters the body rows of all of them", () => {
  const row = (text) => ({ textContent: text, hidden: false });
  const table = (...texts) => ({ tBodies: [{ rows: texts.map(row) }] });
  const box = { querySelectorAll: (selector) => (selector === "table" ? [table("Caféine", "Clozapine"), table("Fluvoxamine"), { tBodies: [] }] : []) };
  assert.deepEqual(tf.bodyRows(box).map((r) => r.textContent), ["Caféine", "Clozapine", "Fluvoxamine"]);
  assert.deepEqual(tf.bodyRows({ querySelectorAll: () => [] }), []);
});

test("a box can filter on the first column only (the drug names of the cytochrome grid)", () => {
  const row = { textContent: "Modafinil Puissant Modéré", cells: [{ textContent: "Modafinil" }, { textContent: "Puissant" }] };
  assert.equal(tf.rowText(row, "premiere-colonne"), "Modafinil");
  assert.equal(tf.rowText(row, null), "Modafinil Puissant Modéré");
  assert.ok(!tf.matches(tf.rowText({ textContent: "Fluoxétine Modéré", cells: [{ textContent: "Fluoxétine" }] }, "premiere-colonne"), "mod"));
});
