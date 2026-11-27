// Tests for assets/js/chercher-medicament.js (search a medicine by its name or substance).
// Run: npm run test:js
import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const cm = require("../../assets/js/chercher-medicament.js");

// Same shape as assets/data/medicaments.json (tools/build/make_bdpm_recherche.py)
const DATA = {
  source: "https://base-donnees-publique.medicaments.gouv.fr/telechargement",
  mis_a_jour: "2026-11-20",
  substances: ["ibuprofène", "paracétamol", "codéine", "rivaroxaban", "ibuprofène lysine"],
  // Each substance points to every sheet that lists it (codeine: two sheets).
  fiches: {
    "0": [["medicaments/classes/ains.html", "Les AINS"]],
    "2": [["medicaments/classes/opioides.html", "Les opioïdes"], ["medicaments/maux-courants/toux.html", "La toux"]],
    "4": [["medicaments/classes/ains.html", "Les AINS"]],
  },
  medicaments: [
    ["68634000", "ADVIL 200 mg, comprimé enrobé", [0]],
    ["60000001", "DOLIPRANE 1000 mg, comprimé", [1]],
    ["60000002", "DOLIPRANE 500 mg, gélule", [1]],
    ["60000003", "IBUPROFENE ARROW 400 mg, comprimé", [0]],
    ["60000004", "PARACETAMOL CODEINE ARROW 500 mg/30 mg, comprimé", [1, 2]],
    ["60000012", "XARELTO 10 mg, comprimé pelliculé", [3]],
    ["60000013", "IBUPROFENE LYSINE TEST 400 mg, comprimé", [0, 4]],
  ],
};
const ENTREES = cm.preparer(DATA);
const noms = (r) => r.resultats.map((e) => e.nom);

test("names are compared without case, accents or punctuation", () => {
  assert.equal(cm.normalise("  Paracétamol/Codéine, 500 MG "), "paracetamol codeine 500 mg");
});

test("a brand name finds its medicines, by the start of a word", () => {
  assert.deepEqual(noms(cm.chercher("dolip", ENTREES)), ["DOLIPRANE 1000 mg, comprimé", "DOLIPRANE 500 mg, gélule"]);
  assert.deepEqual(noms(cm.chercher("xarelto", ENTREES)), ["XARELTO 10 mg, comprimé pelliculé"]);
  assert.equal(cm.chercher("liprane", ENTREES).total, 0);
});

test("a substance finds every medicine that contains it, accents optional", () => {
  assert.deepEqual(noms(cm.chercher("codeine", ENTREES)), ["PARACETAMOL CODEINE ARROW 500 mg/30 mg, comprimé"]);
  assert.equal(cm.chercher("paracétamol", ENTREES).total, 3);
});

test("every word must match: brand and strength together", () => {
  assert.deepEqual(noms(cm.chercher("doliprane 1000", ENTREES)), ["DOLIPRANE 1000 mg, comprimé"]);
});

test("medicines whose name starts with the search come first", () => {
  const r = cm.chercher("ibuprof", ENTREES);
  assert.deepEqual(noms(r), [
    "IBUPROFENE ARROW 400 mg, comprimé",
    "IBUPROFENE LYSINE TEST 400 mg, comprimé",
    "ADVIL 200 mg, comprimé enrobé",
  ]);
});

test("results are capped and the total is kept", () => {
  const r = cm.chercher("paracetamol", ENTREES, 2);
  assert.equal(r.total, 3);
  assert.equal(r.resultats.length, 2);
});

test("a search under two characters gives nothing", () => {
  assert.equal(cm.chercher("d", ENTREES).total, 0);
  assert.equal(cm.chercher("  ", ENTREES).total, 0);
});

test("each medicine carries its official page, substances and the site's sheets", () => {
  const combo = ENTREES.find((e) => e.cis === "60000004");
  assert.equal(combo.url, "https://base-donnees-publique.medicaments.gouv.fr/medicament/60000004/extrait");
  assert.deepEqual(combo.substances, ["paracétamol", "codéine"]);
  assert.deepEqual(combo.fiches, [
    ["medicaments/classes/opioides.html", "Les opioïdes"],
    ["medicaments/maux-courants/toux.html", "La toux"],
  ]);
  assert.deepEqual(ENTREES.find((e) => e.cis === "60000012").fiches, []);
});

test("a sheet reached through two salts of the same substance is listed once", () => {
  const e = ENTREES.find((x) => x.cis === "60000013");
  assert.deepEqual(e.fiches, [["medicaments/classes/ains.html", "Les AINS"]]);
});
