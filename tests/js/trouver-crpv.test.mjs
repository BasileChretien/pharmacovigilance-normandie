// Tests for assets/js/trouver-crpv.js (postal code -> regional pharmacovigilance centre).
// Run: npm run test:js
import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const tc = require("../../assets/js/trouver-crpv.js");

const CENTRES = [
  { nom: "Centre de Caen", departements: [{ code: "14" }, { code: "50" }, { code: "61" }] },
  { nom: "Centre de Marseille", departements: [{ code: "13" }, { code: "2A" }, { code: "2B" }] },
  { nom: "Centre de Bordeaux", departements: [{ code: "33" }, { code: "971" }, { code: "974" }] },
  { nom: "Centre de Paris HEGP", departements: [{ code: "75", arrondissements: [14, 15, 16] }, { code: "92" }] },
  { nom: "Centre de Paris Cochin", departements: [{ code: "75", arrondissements: [1, 6] }, { code: "78", precision: "Sud" }] },
  { nom: "Centre de Paris Saint Louis", departements: [{ code: "78", precision: "Nord" }] },
];

test("a postal code gives its department, Corsica and overseas included", () => {
  assert.equal(tc.departement("14000"), "14");
  assert.equal(tc.departement("01100"), "01");
  assert.equal(tc.departement("20000"), "2A"); // Ajaccio
  assert.equal(tc.departement("20190"), "2A");
  assert.equal(tc.departement("20200"), "2B"); // Bastia
  assert.equal(tc.departement("97100"), "971");
  assert.equal(tc.departement(" 76 000 "), "76"); // spaces are ignored
});

test("anything but five digits is refused", () => {
  assert.equal(tc.departement("1400"), null);
  assert.equal(tc.departement("14O00"), null);
  assert.equal(tc.departement(""), null);
});

test("a Paris postal code gives its arrondissement, 75116 included", () => {
  assert.equal(tc.arrondissement("75015"), 15);
  assert.equal(tc.arrondissement("75116"), 16);
  assert.equal(tc.arrondissement("75021"), null);
  assert.equal(tc.arrondissement("14000"), null);
});

test("the right centre is found, by department or by arrondissement", () => {
  assert.deepEqual(tc.trouver("50100", CENTRES).map((r) => r.centre.nom), ["Centre de Caen"]);
  assert.deepEqual(tc.trouver("20200", CENTRES).map((r) => r.centre.nom), ["Centre de Marseille"]);
  assert.deepEqual(tc.trouver("97400", CENTRES).map((r) => r.centre.nom), ["Centre de Bordeaux"]);
  assert.deepEqual(tc.trouver("75116", CENTRES).map((r) => r.centre.nom), ["Centre de Paris HEGP"]);
  assert.deepEqual(tc.trouver("75006", CENTRES).map((r) => r.centre.nom), ["Centre de Paris Cochin"]);
});

test("a split department returns each centre with its part", () => {
  const results = tc.trouver("78000", CENTRES);
  assert.deepEqual(results.map((r) => [r.centre.nom, r.precision]), [
    ["Centre de Paris Cochin", "Sud"],
    ["Centre de Paris Saint Louis", "Nord"],
  ]);
});

test("an unknown department or an invalid code finds nothing", () => {
  assert.deepEqual(tc.trouver("98000", CENTRES), []); // Monaco
  assert.deepEqual(tc.trouver("abc", CENTRES), []);
});
