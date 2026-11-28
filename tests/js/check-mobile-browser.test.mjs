// The measurements of the phone-layout check (tools/checks/mobile/measure.js) on small
// pages, in WebKit and Chromium: each rule finds its problem and leaves the right page
// alone. Needs playwright and its browsers; skipped without them (npm run test:js before
// the CI installs them). CI runs it in the "Phone layout" step.
import { after, before, describe, test } from "node:test";
import assert from "node:assert/strict";
import { fileURLToPath } from "node:url";

let playwright = null;
try {
  playwright = await import("playwright");
} catch {
  playwright = null;
}
const SKIP = playwright ? false : "playwright n'est pas installé";
const SCRIPTS = ["geometry.js", "measure.js"].map((f) => fileURLToPath(new URL(`../../tools/checks/mobile/${f}`, import.meta.url)));
const CSS = "<style>* { box-sizing: border-box; } body { margin: 0; font: 16px/1.5 sans-serif; }</style>";

function options(viewport, extra = {}) {
  return { width: viewport.width, height: viewport.height, header: false, svgText: true, allow: [], ...extra };
}

for (const engine of ["webkit", "chromium"]) {
  describe(`mesures dans ${engine}`, { skip: SKIP }, () => {
    let browser;
    let page;
    const phone = { width: 320, height: 568 };

    before(async () => {
      browser = await playwright[engine].launch();
      const context = await browser.newContext({ viewport: phone, isMobile: engine !== "firefox", hasTouch: true });
      for (const path of SCRIPTS) await context.addInitScript({ path });
      page = await context.newPage();
    });
    after(async () => browser && browser.close());

    async function measure(body, opts = options(phone)) {
      await page.setContent(`<!doctype html><html lang="fr"><head><meta name="viewport" content="width=device-width, initial-scale=1">${CSS}</head><body>${body}</body></html>`);
      return page.evaluate((o) => window.CheckMobile.measure(window, o), opts);
    }

    const rules = (result) => result.findings.map((f) => f.rule).sort();

    test("a heading label in ::after that pushes the page sideways is named as the cause", async () => {
      const result = await measure(`<style>
        h2 { display: flex; gap: 10px; margin: 0 12px; padding: 8px; font-size: 22px; }
        h2::after { content: "professionnels de santé"; margin-left: auto; white-space: nowrap; font: 700 12px monospace; }
      </style><main><h2>Pour les professionnels</h2><p>Texte.</p></main>`);
      const scroll = result.findings.filter((f) => f.rule === "defilement");
      assert.equal(scroll.length, 1);
      assert.match(scroll[0].element, /h2::after$/);
      assert.equal(scroll[0].text, "professionnels de santé");
      assert.match(scroll[0].detail, /^contenu de \d+ px dans une boîte de \d+ px \(page de \d+ px pour 320 px d'écran\)$/);
    });

    test("a fixed button cut off at the right edge is found, without blaming the page scroll", async () => {
      const result = await measure(`<header style="position: fixed; top: 0; left: 0; right: 0; height: 50px;">
        <button style="position: absolute; left: 300px; top: 8px; width: 40px; height: 34px;">R</button>
      </header><p style="margin-top: 60px;">Texte.</p>`);
      assert.deepEqual(rules(result), ["hors-ecran"]);
      assert.match(result.findings[0].element, /button$/);
      assert.equal(result.findings[0].detail, "40×34 px (fixe, hors du défilement), dépasse de 20 px à droite");
    });

    test("a wide table in its own scroll box and a page that fits pass", async () => {
      const result = await measure(`<main style="padding: 0 12px;">
        <div style="overflow-x: auto;"><table style="width: 800px;"><tr><td>Molécule</td><td>Effet</td></tr></table></div>
        <p>Un texte avec <a href="#a">un lien</a> dans la phrase.</p></main>`);
      assert.deepEqual(result.findings, []);
    });

    test("a wide table without a scroll box scrolls the page and leaves the screen", async () => {
      const result = await measure(`<table style="width: 500px;"><tr><td>Molécule</td><td>Effet</td></tr></table>`);
      assert.deepEqual(rules(result), ["defilement", "hors-ecran"]);
      assert.match(result.findings.find((f) => f.rule === "defilement").detail, /^boîte de 500×\d+ px qui dépasse de 180 px à droite/);
    });

    test("a table cut by overflow: hidden, with no way to scroll to its end, fails", async () => {
      const table = (overflow) => `<main style="padding: 0 12px;"><table style="display: block; max-width: 100%; overflow: ${overflow};">
        <tr><td style="white-space: nowrap;">Simvastatine + clarithromycine : association contre-indiquée</td></tr></table></main>`;
      const cut = await measure(table("hidden"));
      assert.deepEqual(rules(cut), ["coupe"]);
      assert.match(cut.findings[0].detail, /^contenu de \d+ px coupé à 296 px, sans défilement \(overflow-x: hidden\)$/);
      assert.deepEqual((await measure(table("auto"))).findings, []);
      const ellipsis = `<p style="overflow: hidden; white-space: nowrap; text-overflow: ellipsis;">${"Texte long ".repeat(20)}</p>`;
      assert.deepEqual((await measure(ellipsis)).findings, []);
    });

    test("an invisible child that pushes the page sideways is named", async () => {
      const result = await measure(`<h2 style="margin: 0 12px; font-size: 22px;">Un titre qui remplit sa ligne<a href="#t"
        style="opacity: 0; display: inline-block; width: 60px; margin-right: -60px;">#</a></h2>`);
      const scroll = result.findings.find((f) => f.rule === "defilement");
      assert.match(scroll.detail, /par l'enfant invisible a /);
    });

    test("texts drawn over each other overlap", async () => {
      const result = await measure(`<p style="position: absolute; top: 100px; left: 10px; margin: 0;">Premier texte posé ici</p>
        <p style="position: absolute; top: 106px; left: 30px; margin: 0;">Second texte</p>`);
      assert.deepEqual(rules(result), ["chevauchement"]);
      assert.match(result.findings[0].detail, /^chevauche p « Second texte » sur \d+×\d+ px$/);
    });

    test("the content of a closed <details> counts for nothing", async () => {
      const result = await measure(`<details><summary style="padding: 12px;">Ouvrir la section</summary>
        <p style="position: absolute; top: 0; left: 0; margin: 0; font-size: 8px;">Caché sous le résumé</p></details>`);
      assert.deepEqual(result.findings, []);
    });

    test("small tap targets fail, except inline links in a sentence and radios in their label", async () => {
      const result = await measure(`<p>Un texte avec <a href="#a">un lien</a> dans la phrase.</p>
        <button style="width: 20px; height: 20px; padding: 0;">x</button>
        <label style="display: inline-block; padding: 10px;"><input type="radio" name="r"> Choix</label>
        <ul><li><a href="#b">Seul sur sa ligne</a></li></ul>`);
      assert.deepEqual(rules(result), ["cible-tactile", "cible-tactile"]);
      assert.equal(result.findings[0].detail, "20×20 px (24×24 px au moins)");
      assert.equal(result.findings[1].text, "Seul sur sa ligne");
    });

    test("text under 12 px fails, and figure text only where it is measured", async () => {
      const svg = `<svg viewBox="0 0 440 40" style="width: 220px;"><text x="0" y="20" font-size="16">Libellé de figure</text></svg>`;
      const result = await measure(`<p style="font-size: 10px;">Petit texte</p><p style="font-size: 12px;">Assez grand</p>${svg}`);
      assert.deepEqual(result.findings.map((f) => [f.rule, f.text, f.detail]), [
        ["texte-petit", "Petit texte", "texte de 10.0 px (12 px au moins)"],
        ["texte-petit", "Libellé de figure", "texte de 8.0 px (12 px au moins)"],
      ]);
      const without = await measure(`${svg}`, options(phone, { svgText: false }));
      assert.deepEqual(without.findings, []);
    });

    test("a fixed header taller than 20 % of the first screen fails", async () => {
      const big = { width: 320, height: 568 };
      const body = (h) => `<header style="position: fixed; top: 0; left: 0; right: 0; height: ${h}px;">En-tête</header>`;
      const tall = await measure(body(150), options(big, { header: true }));
      assert.deepEqual(rules(tall), ["entete"]);
      assert.equal(tall.findings[0].detail, "couvre 150 px sur 568 px (26 %, 20 % au plus)");
      assert.deepEqual((await measure(body(100), options(big, { header: true }))).findings, []);
    });

    test("an exception removes its finding and is counted as used", async () => {
      const allow = [{ index: 4, rule: "cible-tactile", selector: "button.petit" }];
      const result = await measure(`<button class="petit" style="width: 20px; height: 20px; padding: 0;">x</button>`, options(phone, { allow }));
      assert.deepEqual(result.findings, []);
      assert.deepEqual(result.used, [4]);
      const invalid = await measure("<p>Texte.</p>", options(phone, { allow: [{ index: 0, rule: "menu", selector: "a[" }] }));
      assert.deepEqual(invalid.errors, ["exception n° 1 : sélecteur CSS invalide « a[ »"]);
    });

    test("a link of the opened menu off screen or under another element fails", async () => {
      await page.setContent(`<!doctype html><html><head>${CSS}</head><body>
        <div id="menu" style="position: fixed; top: 50px; left: 0; width: 320px;">
          <a href="#1" style="display: block; padding: 10px; margin-left: 330px;">Médicaments</a>
          <a href="#2" style="display: block; padding: 10px;">Bon usage</a>
          <a href="#3" style="display: block; padding: 10px;">Comprendre</a>
        </div>
        <div style="position: fixed; top: 140px; left: 0; width: 320px; height: 60px;"></div></body></html>`);
      const result = await page.evaluate((o) => window.CheckMobile.menu(window, o), options(phone, { panel: "#menu" }));
      assert.equal(result.findings.length, 2);
      assert.match(result.findings[0].detail, /hors de l'écran \(de x 330 à \d+/);
      assert.equal(result.findings[0].text, "Médicaments");
      assert.match(result.findings[1].detail, /^caché par div à l'endroit du doigt$/);
      assert.equal(result.findings[1].text, "Comprendre");
    });
  });
}
