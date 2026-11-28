// Tests for the helpers of the phone-layout check (tools/checks/check_mobile.mjs):
// geometry, exceptions file, report and static server. Run: npm run test:js
// The measurements in a real browser: tests/js/check-mobile-browser.test.mjs.
import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, rmSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { entriesFor, formatReport, globToRegExp, groupFindings, parseAllowlist, wrap } from "../../tools/checks/mobile/report.mjs";
import { route, serve } from "../../tools/checks/mobile/server.mjs";

const require = createRequire(import.meta.url);
const G = require("../../tools/checks/mobile/geometry.js");
const M = require("../../tools/checks/mobile/measure.js");

// ---------- geometry ----------

test("a box past the edges says by how much on each side", () => {
  assert.deepEqual(G.pastEdges(G.box(290, 0, 40, 30), 320), { left: 0, right: 10, any: true });
  assert.deepEqual(G.pastEdges(G.box(-12, 0, 100, 30), 320), { left: 12, right: 0, any: true });
  // Sub-pixel rounding is not a failure.
  assert.equal(G.pastEdges(G.box(0, 0, 320.6, 30), 320).any, false);
  assert.equal(G.pastEdges(G.box(-0.5, 0, 100, 30), 320).any, false);
});

test("inside the viewport allows a pixel of rounding on each side", () => {
  assert.ok(G.insideViewport(G.box(0, 0, 320, 568), 320, 568));
  assert.ok(G.insideViewport(G.box(-0.8, 10, 100, 40), 320, 568));
  assert.ok(!G.insideViewport(G.box(331, 16, 199, 41), 320, 568)); // the menu link of the audit
  assert.ok(!G.insideViewport(G.box(10, 540, 100, 41), 320, 568));
});

test("intersection and area", () => {
  const common = G.intersect(G.box(0, 0, 100, 20), G.box(50, 10, 100, 20));
  assert.deepEqual([common.left, common.top, common.width, common.height], [50, 10, 50, 10]);
  assert.equal(G.intersect(G.box(0, 0, 10, 10), G.box(10, 0, 10, 10)), null); // touching edges
  assert.equal(G.area(null), 0);
});

test("text boxes that only touch or cross by a sliver do not overlap", () => {
  // Two lines of 20 px whose glyph boxes cross by 2 px (tight line height).
  assert.equal(G.textOverlap(G.box(0, 0, 200, 20), G.box(0, 18, 200, 20)), null);
  // A label drawn over another text.
  assert.ok(G.textOverlap(G.box(0, 0, 200, 20), G.box(20, 5, 100, 20)));
  // A small box that crosses a large one by a corner: under 20 % of the smaller box.
  assert.equal(G.textOverlap(G.box(0, 0, 300, 100), G.box(295, 95, 40, 40)), null);
});

test("overlapping pairs skip related boxes and find the rest", () => {
  const a = { id: "a", box: G.box(0, 0, 100, 20) };
  const b = { id: "b", box: G.box(10, 5, 100, 20) };
  const c = { id: "c", box: G.box(0, 100, 100, 20) };
  const pairs = G.overlappingPairs([c, b, a], () => false);
  assert.deepEqual(pairs.map(([x, y]) => [x.id, y.id]), [["a", "b"]]);
  assert.deepEqual(G.overlappingPairs([a, b], () => true), []);
});

test("a tap target needs 24×24 px", () => {
  assert.ok(G.tooSmall(G.box(0, 0, 18, 45))); // the squeezed logo link of the audit
  assert.ok(G.tooSmall(G.box(0, 0, 117, 20)));
  assert.ok(!G.tooSmall(G.box(0, 0, 24, 24)));
  assert.ok(!G.tooSmall(G.box(0, 0, 23.98, 40))); // rounding of rem sizes
});

test("coverage is the union of the bands, clipped to the screen", () => {
  assert.equal(G.coverage([[0, 100]], 1000), 0.1);
  assert.equal(G.coverage([[0, 100], [50, 200]], 1000), 0.2); // navbar and banner overlap
  assert.equal(G.coverage([[0, 100], [300, 400]], 1000), 0.2);
  assert.equal(G.coverage([[-50, 100]], 1000), 0.1);
  assert.equal(G.coverage([], 1000), 0);
});

test("sizes print in whole pixels", () => {
  assert.equal(G.size(G.box(0, 0, 39.6, 34.2)), "40×34 px");
  assert.equal(G.px(10.4), "10 px");
});

// ---------- report labels ----------

function fakeElement(tagName, { id = "", classes = [], parent = null, attrs = {}, text = "" } = {}) {
  return {
    tagName, id, parentElement: parent, textContent: text,
    classList: classes, getAttribute: (name) => (name in attrs ? attrs[name] : null),
  };
}

test("an element is described by its parent and itself, pseudo-element included", () => {
  const body = fakeElement("BODY");
  const section = fakeElement("SECTION", { id: "pour-les-soignants", classes: ["level2", "partie", "partie-pros"], parent: body });
  const h2 = fakeElement("H2", { classes: ["anchored"], parent: section });
  assert.equal(M.describe(h2, "after"), "section#pour-les-soignants.level2.partie > h2.anchored::after");
  assert.equal(M.describe(section), "section#pour-les-soignants.level2.partie");
  assert.equal(M.label(null), "?");
});

test("excerpts are one line and cut with an ellipsis", () => {
  assert.equal(M.excerpt("  Pour les\n  professionnels  "), "Pour les professionnels");
  assert.equal(M.excerpt("x".repeat(50), 10), `${"x".repeat(9)}…`);
  assert.equal(M.excerpt(null), "");
});

test("content of a closed <details> is hidden, its summary is not", () => {
  const closed = { tagName: "DETAILS", parentElement: null, children: [] };
  const summary = { tagName: "SUMMARY", parentElement: closed, contains: (n) => n === summary || n === inSummary };
  const inSummary = { tagName: "SPAN", parentElement: summary };
  closed.children = [summary];
  const inside = { tagName: "P", parentElement: closed };
  const closest = (node) => (sel) => (sel === "details:not([open])" ? findClosed(node) : null);
  const findClosed = (node) => {
    for (let n = node; n; n = n.parentElement) if (n === closed) return closed;
    return null;
  };
  for (const n of [closed, summary, inSummary, inside]) n.closest = closest(n);
  assert.equal(M.inClosedDetails(inside), true);
  assert.equal(M.inClosedDetails(inSummary), false);
  assert.equal(M.inClosedDetails(closed), false);
  assert.equal(M.inClosedDetails(null), false);
});

// ---------- exceptions file ----------

test("globs: * stays in a folder, ** crosses folders", () => {
  assert.ok(globToRegExp("bon-usage/*.html").test("bon-usage/ecraser-couper.html"));
  assert.ok(!globToRegExp("bon-usage/*.html").test("bon-usage/sous/page.html"));
  assert.ok(globToRegExp("**").test("normandie/en/index.html"));
  assert.ok(globToRegExp("index.html").test("index.html"));
  assert.ok(!globToRegExp("index.html").test("indexXhtml")); // the dot is literal
});

test("an exception needs a known rule, a selector and a reason", () => {
  const ok = parseAllowlist({ exceptions: [{ regle: "cible-tactile", selecteur: ".carte a", raison: "Lien de carte agrandi par la carte entière." }] });
  assert.deepEqual(ok.errors, []);
  assert.equal(ok.entries[0].selector, ".carte a");
  const bad = parseAllowlist({ exceptions: [
    { regle: "tactile", selecteur: "a", raison: "Une raison assez longue." },
    { regle: "menu", selecteur: " ", raison: "court" },
    { regle: "menu", selecteur: "a", raison: "Une raison assez longue.", raisons: "faute de frappe" },
    { regle: "menu", selecteur: "a", raison: "Une raison assez longue.", pages: "index.html" },
  ] });
  assert.equal(bad.entries.length, 0);
  assert.ok(bad.errors.some((e) => e.startsWith("exception n° 1 : regle « tactile » inconnue")));
  assert.ok(bad.errors.includes("exception n° 2 : selecteur CSS manquant"));
  assert.ok(bad.errors.includes("exception n° 2 : raison manquante (une phrase)"));
  assert.ok(bad.errors.includes("exception n° 3 : clé inconnue « raisons »"));
  assert.ok(bad.errors.includes("exception n° 4 : pages doit être une liste de textes"));
  assert.deepEqual(parseAllowlist({}).errors, ["le fichier d'exceptions doit contenir une liste « exceptions »"]);
});

test("an exception applies to its pages and profiles only", () => {
  const { entries } = parseAllowlist({ exceptions: [
    { regle: "cible-tactile", selecteur: "a.x", raison: "Raison de la première.", pages: ["bon-usage/*.html"] },
    { regle: "texte-petit", selecteur: "sup", raison: "Raison de la seconde.", profils: ["iphone-se", "pixel-7-sombre"] },
  ] });
  assert.deepEqual(entriesFor(entries, "bon-usage/a.html", "pixel-7-clair").map((e) => e.index), [0]);
  assert.deepEqual(entriesFor(entries, "index.html", "iphone-se-clair").map((e) => e.index), [1]);
  assert.deepEqual(entriesFor(entries, "index.html", "pixel-7-sombre").map((e) => e.index), [1]);
  assert.deepEqual(entriesFor(entries, "index.html", "pixel-7-clair"), []);
  // "iphone-se" is a device, not the start of another one's name.
  assert.deepEqual(entriesFor(entries, "index.html", "iphone-sexy-clair"), []);
});

// ---------- report ----------

test("findings group by rule and element across pages and profiles", () => {
  const f = (rule, element, detail) => ({ rule, element, text: "professionnels de santé", detail });
  const groups = groupFindings([
    { page: "b.html", profile: "iphone-se-clair", findings: [f("defilement", "h2::after", "contenu de 316 px")] },
    { page: "a.html", profile: "iphone-se-sombre", findings: [f("defilement", "h2::after", "contenu de 310 px"), f("menu", "a.nav-link", "hors de l'écran")] },
  ]);
  assert.equal(groups.length, 2);
  assert.equal(groups[0].rule, "defilement");
  assert.equal(groups[0].count, 2);
  assert.deepEqual([...groups[0].pages].sort(), ["a.html", "b.html"]);
  const text = formatReport(groups);
  assert.match(text, /La page défile de côté — 2 constat\(s\) sur 2 page\(s\)/);
  assert.match(text, /• h2::after « professionnels de santé »/);
  assert.match(text, /profils : iphone-se-clair, iphone-se-sombre/);
  assert.match(text, /pages \(2\) : a\.html, b\.html/);
  assert.equal(formatReport([]), "");
});

test("long lists of pages wrap under their first item", () => {
  const lines = wrap("pages : ", ["aaaa.html", "bbbb.html", "cccc.html"], 26).split("\n");
  assert.deepEqual(lines, ["pages : aaaa.html,", "        bbbb.html,", "        cccc.html"]);
});

// ---------- server ----------

function site() {
  const root = mkdtempSync(join(tmpdir(), "check-mobile-"));
  mkdirSync(join(root, "bon-usage"));
  writeFileSync(join(root, "index.html"), "<p>accueil</p>");
  writeFileSync(join(root, "404.html"), "<p>introuvable</p>");
  writeFileSync(join(root, "bon-usage", "index.html"), "<p>bon usage</p>");
  writeFileSync(join(root, "bon-usage", "ecraser-couper.html"), "<p>écraser</p>");
  writeFileSync(join(root, "style.css"), "p {}");
  return root;
}

test("requests are routed as on GitHub Pages, under the subpath only", () => {
  const root = site();
  const P = "/pharmacovigilance-normandie/";
  try {
    assert.equal(route(root, P, `${P}`).file, join(root, "index.html"));
    assert.equal(route(root, P, `${P}bon-usage/`).file, join(root, "bon-usage", "index.html"));
    assert.deepEqual(route(root, P, `${P}bon-usage`), { status: 301, location: `${P}bon-usage/` });
    assert.deepEqual(route(root, P, "/pharmacovigilance-normandie"), { status: 301, location: P });
    assert.equal(route(root, P, `${P}bon-usage/ecraser-couper?x=1`).file, join(root, "bon-usage", "ecraser-couper.html"));
    assert.equal(route(root, P, `${P}style.css`).status, 200);
    assert.deepEqual(route(root, P, `${P}absent.html`), { status: 404, file: join(root, "404.html") });
    assert.equal(route(root, P, "/style.css").status, 404); // outside the subpath
    assert.equal(route(root, P, `${P}..%2F..%2Fsecret`).status, 404); // no way out of the folder
    assert.equal(route(root, P, `${P}%E0%A4%A`).status, 400);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("the server answers with the file and its type", async () => {
  const root = site();
  const server = await serve(root, "/pharmacovigilance-normandie/");
  try {
    const page = await fetch(`${server.url}bon-usage/ecraser-couper.html`);
    assert.equal(page.status, 200);
    assert.equal(page.headers.get("content-type"), "text/html; charset=utf-8");
    assert.equal(await page.text(), "<p>écraser</p>");
    const missing = await fetch(`${server.url}absent.html`);
    assert.equal(missing.status, 404);
    assert.equal(await missing.text(), "<p>introuvable</p>");
    const folder = await fetch(`${server.url}bon-usage`, { redirect: "manual" });
    assert.equal(folder.status, 301);
  } finally {
    await server.close();
    rmSync(root, { recursive: true, force: true });
  }
});
