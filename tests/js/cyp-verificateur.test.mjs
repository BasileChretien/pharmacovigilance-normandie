// Tests for assets/js/cyp-verificateur.js (two-drug checker of bon-usage/cytochromes.qmd).
// Run: npm run test:js. The real-data tests read the JSON that tools/build/make_cytochromes.py
// writes into _includes/cyp-donnees.md, so the checker is tested on what the page ships.
import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { readFileSync } from "node:fs";

const require = createRequire(import.meta.url);
const cv = require("../../assets/js/cyp-verificateur.js");

const include = readFileSync(new URL("../../_includes/cyp-donnees.md", import.meta.url), "utf8");
const json = include.match(/<script type="application\/json" id="cyp-donnees">([\s\S]*?)<\/script>/)[1];
const REAL = cv.prepare(JSON.parse(json));

const ENZYMES = [
  { id: "CYP2C9", de: "du CYP2C9", ancre: "exemples-cyp2c9" },
  { id: "CYP2B6", de: "du CYP2B6", ancre: "exemples-cyp2b6" },
  { id: "P-gp", de: "de la P-gp", ancre: "exemples-p-gp" },
];
const S = (voie, extra) => ({ substrat: Object.assign({ voie: voie, prodrogue: false, actif: false, source: "hug" }, extra) });
const FIXTURE = cv.prepare({
  enzymes: ENZYMES,
  sources: { hug: { court: "HUG", long: "carte des HUG (mars 2020)" }, thesaurus: { court: "Thésaurus", long: "liste du Thésaurus de l'ANSM (septembre 2023)" } },
  medicaments: [
    { nom: "Éfavirenz", precision: "", roles: { CYP2B6: Object.assign(S("majeure"), { inhibiteur: { force: "modéré", source: "hug" }, inducteur: { force: "modéré", source: "hug" } }) } },
    { nom: "Érythromycine", precision: "", roles: { "P-gp": { inhibiteur: { force: "puissant", source: "hug" } } } },
    { nom: "Fluconazole", precision: "", roles: { CYP2C9: { inhibiteur: { force: "puissant", source: "hug" } } } },
    { nom: "Fluoxétine", precision: "", roles: { CYP2C9: { inhibiteur: { force: "modéré", source: "hug" } } } },
    { nom: "Silibinine", precision: "chardon-Marie", roles: { CYP2C9: { inhibiteur: { force: "puissant", source: "thesaurus" } } } },
    { nom: "Sertraline", precision: "", roles: { CYP2B6: S("mineure", { actif: true }) } },
    { nom: "Warfarine", precision: "", roles: { CYP2C9: S("majeure"), "P-gp": S("majeure") } },
  ],
});

const byName = (prepared, name) => prepared.medicaments.find((m) => m.nom === name);

// ---------- Search ------------------------------------------------------------

test("fold drops accents, case and punctuation", () => {
  assert.equal(cv.fold("Éthinylestradiol (contraceptifs oraux)"), "ethinylestradiol contraceptifs oraux");
  assert.equal(cv.fold("  CYP3A4/5 "), "cyp3a4 5");
});

test("suggestions match the start of any word, accents optional", () => {
  assert.deepEqual(cv.suggest("erythro", FIXTURE.medicaments).map((m) => m.nom), ["Érythromycine"]);
  assert.deepEqual(cv.suggest("chardon", FIXTURE.medicaments).map((m) => m.nom), ["Silibinine"]);
  assert.deepEqual(cv.suggest("FLU", FIXTURE.medicaments).map((m) => m.nom), ["Fluconazole", "Fluoxétine"]);
  assert.deepEqual(cv.suggest("", FIXTURE.medicaments), []);
  assert.deepEqual(cv.suggest("zz", FIXTURE.medicaments), []);
});

test("suggestions whose name starts with the query come first, and the list is capped", () => {
  const meds = cv.prepare({ enzymes: ENZYMES, sources: {}, medicaments: [
    { nom: "Acide valproïque", precision: "", roles: {} },
    { nom: "Valsartan", precision: "", roles: {} },
  ] }).medicaments;
  assert.deepEqual(cv.suggest("val", meds).map((m) => m.nom), ["Valsartan", "Acide valproïque"]);
  assert.equal(cv.suggest("a", REAL.medicaments).length, cv.LIMITE);
});

test("a typed name resolves exactly, by a single match, or not at all", () => {
  assert.equal(cv.resolve("warfarine", FIXTURE.medicaments).medicament.nom, "Warfarine");
  assert.equal(cv.resolve("ERYTHROMYCINE", FIXTURE.medicaments).medicament.nom, "Érythromycine");
  assert.equal(cv.resolve("warf", FIXTURE.medicaments).medicament.nom, "Warfarine");
  const ambigu = cv.resolve("flu", FIXTURE.medicaments);
  assert.equal(ambigu.statut, "ambigu");
  assert.deepEqual(ambigu.candidats.map((m) => m.nom), ["Fluconazole", "Fluoxétine"]);
  assert.equal(cv.resolve("paracétamol", FIXTURE.medicaments).statut, "absent");
  assert.equal(cv.resolve("   ", FIXTURE.medicaments).statut, "vide");
});

test("arrow keys move through the suggestions and wrap", () => {
  assert.equal(cv.nextIndex(-1, "ArrowDown", 3), 0);
  assert.equal(cv.nextIndex(2, "ArrowDown", 3), 0);
  assert.equal(cv.nextIndex(-1, "ArrowUp", 3), 2);
  assert.equal(cv.nextIndex(0, "ArrowUp", 3), 2);
  assert.equal(cv.nextIndex(1, "Enter", 3), 1);
  assert.equal(cv.nextIndex(0, "ArrowDown", 0), -1);
});

// ---------- Mechanisms ----------------------------------------------------------

test("a substrate and a strong inhibitor of the same enzyme: exposure up", () => {
  const found = cv.mechanisms(byName(FIXTURE, "Warfarine"), byName(FIXTURE, "Fluconazole"), FIXTURE.enzymes);
  assert.equal(found.length, 1);
  const m = found[0];
  assert.equal(m.enzyme.id, "CYP2C9");
  assert.equal(m.substrat.nom, "Warfarine");
  assert.equal(m.effecteur.nom, "Fluconazole");
  assert.equal(m.type, "inhibiteur");
  assert.equal(m.force, "puissant");
  assert.equal(m.sens, "hausse");
  assert.equal(m.cible, "medicament");
});

test("the order of the two drugs does not matter", () => {
  const ab = cv.mechanisms(byName(FIXTURE, "Warfarine"), byName(FIXTURE, "Fluconazole"), FIXTURE.enzymes);
  const ba = cv.mechanisms(byName(FIXTURE, "Fluconazole"), byName(FIXTURE, "Warfarine"), FIXTURE.enzymes);
  assert.deepEqual(ab, ba);
});

test("P-glycoprotein counts like an enzyme", () => {
  const found = cv.mechanisms(byName(FIXTURE, "Warfarine"), byName(FIXTURE, "Érythromycine"), FIXTURE.enzymes);
  assert.deepEqual(found.map((m) => [m.enzyme.id, m.sens]), [["P-gp", "hausse"]]);
});

test("two inhibitors, or two drugs on different enzymes, give nothing", () => {
  assert.deepEqual(cv.mechanisms(byName(FIXTURE, "Fluconazole"), byName(FIXTURE, "Fluoxétine"), FIXTURE.enzymes), []);
  assert.deepEqual(cv.mechanisms(byName(FIXTURE, "Sertraline"), byName(FIXTURE, "Fluconazole"), FIXTURE.enzymes), []);
});

test("a drug that both inhibits and induces the enzyme gives two opposite mechanisms", () => {
  const found = cv.mechanisms(byName(FIXTURE, "Sertraline"), byName(FIXTURE, "Éfavirenz"), FIXTURE.enzymes);
  assert.deepEqual(found.map((m) => [m.type, m.sens]), [["inhibiteur", "hausse"], ["inducteur", "baisse"]]);
  assert.ok(cv.notes(found[0], found).some((n) => /à la fois inhibiteur et inducteur/.test(n)));
});

test("real data: warfarin and fluconazole, CYP2C9, warfarin up", () => {
  const found = cv.mechanisms(byName(REAL, "Warfarine"), byName(REAL, "Fluconazole"), REAL.enzymes);
  assert.deepEqual(found.map((m) => [m.enzyme.id, m.substrat.nom, m.sens]), [["CYP2C9", "Warfarine", "hausse"]]);
});

test("real data: a prodrug with an inhibitor of its activating enzyme, less active metabolite", () => {
  const codeine = cv.mechanisms(byName(REAL, "Codéine"), byName(REAL, "Fluoxétine"), REAL.enzymes);
  assert.deepEqual(codeine.map((m) => [m.enzyme.id, m.sens, m.cible]), [["CYP2D6", "baisse", "metabolite"]]);
  const clopidogrel = cv.mechanisms(byName(REAL, "Clopidogrel"), byName(REAL, "Oméprazole"), REAL.enzymes);
  assert.deepEqual(clopidogrel.map((m) => [m.enzyme.id, m.substrat.nom, m.sens, m.cible]), [["CYP2C19", "Clopidogrel", "baisse", "metabolite"]]);
});

test("real data: an inducer lowers the substrate", () => {
  const found = cv.mechanisms(byName(REAL, "Dabigatran"), byName(REAL, "Rifampicine"), REAL.enzymes);
  assert.deepEqual(found.map((m) => [m.enzyme.id, m.type, m.sens]), [["P-gp", "inducteur", "baisse"]]);
});

test("real data: amiodarone raises digoxin through P-gp", () => {
  const found = cv.mechanisms(byName(REAL, "Digoxine"), byName(REAL, "Amiodarone"), REAL.enzymes);
  assert.deepEqual(found.map((m) => [m.enzyme.id, m.substrat.nom, m.sens]), [["P-gp", "Digoxine", "hausse"]]);
});

// ---------- Plain-French wording -------------------------------------------------

const one = (a, b, data) => cv.mechanisms(byName(data, a), byName(data, b), data.enzymes)[0];

test("headline names the drug whose exposure changes and the direction", () => {
  assert.equal(cv.headline(one("Warfarine", "Fluconazole", FIXTURE)), "Warfarine : exposition en hausse");
  assert.equal(cv.headline(one("Dabigatran", "Rifampicine", REAL)), "Dabigatran : exposition en baisse");
  assert.equal(cv.headline(one("Codéine", "Fluoxétine", REAL)), "Codéine : métabolite actif en baisse");
});

test("the consequence is said in plain French for the four cases", () => {
  assert.equal(cv.consequence(one("Warfarine", "Fluconazole", FIXTURE)), "Ses concentrations peuvent augmenter : risque de surdosage ou d'effets indésirables.");
  assert.equal(cv.consequence(one("Dabigatran", "Rifampicine", REAL)), "Ses concentrations peuvent diminuer : risque de perte d'efficacité.");
  assert.equal(cv.consequence(one("Codéine", "Fluoxétine", REAL)), "Moins de métabolite actif formé : son efficacité peut diminuer.");
  const prodrugInduced = Object.assign({}, one("Codéine", "Fluoxétine", REAL), { type: "inducteur", sens: "hausse" });
  assert.equal(cv.consequence(prodrugInduced), "Plus de métabolite actif formé : son effet peut augmenter.");
});

test("the mechanism line gives both roles and the enzyme with its article", () => {
  assert.equal(cv.cause(one("Warfarine", "Fluconazole", FIXTURE)), "Fluconazole : inhibiteur puissant du CYP2C9. Warfarine : substrat (voie majeure).");
  assert.equal(cv.cause(one("Warfarine", "Érythromycine", FIXTURE)), "Érythromycine : inhibiteur puissant de la P-gp. Warfarine : substrat (voie majeure).");
});

test("notes flag a minor pathway, an active metabolite and a source other than the HUG card", () => {
  const minor = one("Sertraline", "Éfavirenz", FIXTURE);
  const notes = cv.notes(minor, [minor]);
  assert.ok(notes.some((n) => n === "Voie mineure pour sertraline : l'effet dépend de la part de cette voie dans son élimination."));
  assert.ok(notes.some((n) => n === "Sertraline a un métabolite actif : l'effet dépend aussi de ce métabolite."));
  const thesaurus = one("Warfarine", "Silibinine", FIXTURE);
  assert.deepEqual(cv.notes(thesaurus, [thesaurus], FIXTURE), ["Classement de silibinine : liste du Thésaurus de l'ANSM (septembre 2023)."]);
});

test("a minor pathway that forms a prodrug's active substance is not played down", () => {
  // codeine + paroxetine, clopidogrel + omeprazole: "association déconseillée" on the page.
  for (const [s, e] of [["Codéine", "Paroxétine"], ["Clopidogrel", "Oméprazole"], ["Tramadol", "Fluoxétine"]]) {
    const m = one(s, e, REAL);
    const notes = cv.notes(m, [m], REAL);
    assert.ok(!notes.some((n) => /dépend de la part de cette voie/.test(n)), s);
    // "participe à": the enzyme need not be the only route to the active metabolite (clopidogrel).
    assert.ok(notes.includes("Voie mineure de l'élimination de " + s.toLowerCase() + ", mais elle participe à la formation de son métabolite actif."), s);
    assert.ok(!notes.some((n) => /c'est elle qui forme/.test(n)), s);
  }
});

test("summary for the live region, with or without a mechanism", () => {
  const w = byName(FIXTURE, "Warfarine");
  const f = byName(FIXTURE, "Fluconazole");
  assert.equal(cv.summary(w, f, cv.mechanisms(w, f, FIXTURE.enzymes)), "Warfarine et fluconazole : 1 mécanisme possible dans ce tableau (CYP2C9).");
  const e = byName(FIXTURE, "Érythromycine");
  assert.equal(cv.summary(w, e, []), "Warfarine et érythromycine : aucun mécanisme substrat-inhibiteur ou substrat-inducteur dans ce tableau. Cela ne veut pas dire qu'il n'y a pas d'interaction.");
  const s = byName(FIXTURE, "Sertraline");
  const ef = byName(FIXTURE, "Éfavirenz");
  assert.equal(cv.summary(s, ef, cv.mechanisms(s, ef, FIXTURE.enzymes)), "Sertraline et éfavirenz : 2 mécanismes possibles dans ce tableau (CYP2B6).");
});

test("role labels for the enzyme-by-enzyme table", () => {
  const efa = byName(FIXTURE, "Éfavirenz");
  assert.equal(cv.roleLabel(efa.roles.CYP2B6), "Substrat (voie majeure) ; inhibiteur modéré ; inducteur modéré");
  assert.equal(cv.roleLabel(byName(REAL, "Codéine").roles.CYP2D6), "Substrat (voie mineure, prodrogue)");
  assert.equal(cv.roleLabel(byName(FIXTURE, "Sertraline").roles.CYP2B6), "Substrat (voie mineure, métabolite actif)");
  assert.equal(cv.roleLabel(undefined), "");
});

test("messages for an empty, unknown, ambiguous or repeated entry", () => {
  assert.equal(cv.problem("A", { statut: "vide" }), "Saisissez le médicament A.");
  assert.equal(cv.problem("B", { statut: "absent", saisie: "paracétamol" }), "« paracétamol » n'est pas dans ce tableau, qui ne cite que des exemples : cela ne veut pas dire qu'il n'interagit pas.");
  const ambigu = cv.resolve("flu", FIXTURE.medicaments);
  assert.equal(cv.problem("A", ambigu), "Médicament A : plusieurs correspondances (fluconazole, fluoxétine). Choisissez-en un dans la liste.");
  assert.equal(cv.problem("B", { statut: "meme" }), "Choisissez deux médicaments différents.");
});
