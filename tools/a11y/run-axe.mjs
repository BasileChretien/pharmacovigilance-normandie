// Run axe-core on every rendered page of _site/ and fail on serious or critical
// WCAG 2.1 A/AA violations. Needs playwright and @axe-core/playwright, installed
// in CI only (see .github/workflows/ci.yml) to keep local installs light.
import { readdirSync, statSync } from "node:fs";
import { join, relative } from "node:path";
import { pathToFileURL } from "node:url";
import { chromium } from "playwright";
import AxeBuilder from "@axe-core/playwright";

const SITE = "_site";
const BLOCKING = new Set(["serious", "critical"]);

function htmlFiles(dir) {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) return name === "site_libs" ? [] : htmlFiles(path);
    return name.endsWith(".html") ? [path] : [];
  });
}

const browser = await chromium.launch();
// @axe-core/playwright opens extra pages in the page's context, so the page must come
// from an explicit context (browser.newPage() fails with "Please use browser.newContext()").
const context = await browser.newContext();
const page = await context.newPage();
let blocking = 0;
for (const file of htmlFiles(SITE)) {
  await page.goto(pathToFileURL(file).href);
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  for (const v of results.violations) {
    const flag = BLOCKING.has(v.impact) ? "ERREUR" : "avert.";
    if (BLOCKING.has(v.impact)) blocking += 1;
    console.log(`${relative(SITE, file)}  [${flag}] ${v.id} (${v.impact}) : ${v.help} — ${v.nodes.length} élément(s)`);
  }
}
await browser.close();
console.log(`\naxe-core : ${blocking} violation(s) bloquante(s).`);
process.exit(blocking ? 1 : 0);
