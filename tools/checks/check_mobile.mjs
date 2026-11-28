// Phone-layout check of the rendered site (docs/mobile.md). After quarto render:
//   npm run check:mobile [-- page.html … ] [-- --profils iphone-se,pixel-7-sombre]
// Serves _site/ under the site's subpath and loads every page in WebKit (iPhone SE
// 320×568, iPhone 13 390×844) and Chromium (Pixel 7 412×839), light and dark. Fails when a
// page scrolls sideways, an element leaves the screen, the fixed header covers more than
// 20 % of the first screen, a link of the opened menu is off screen or covered, texts
// overlap, a tap target is under 24×24 px or a text under 12 px. Exceptions:
// tools/checks/mobile_allowlist.json, each with its reason. Screenshots of the failures:
// _captures-mobile/ (CI artefact). Needs playwright, installed in CI only (like run-axe.mjs).
import { mkdirSync, readFileSync, readdirSync, rmSync, statSync } from "node:fs";
import { dirname, join, relative, sep } from "node:path";
import { fileURLToPath } from "node:url";
import { chromium, devices, webkit } from "playwright";
import { serve } from "./mobile/server.mjs";
import { entriesFor, formatReport, groupFindings, parseAllowlist } from "./mobile/report.mjs";

const SITE = "_site";
const PREFIX = "/pharmacovigilance-normandie/";
const CAPTURES = "_captures-mobile";
const HERE = dirname(fileURLToPath(import.meta.url));
const ALLOWLIST = join(HERE, "mobile_allowlist.json");
const SCRIPTS = ["geometry.js", "measure.js"].map((f) => join(HERE, "mobile", f));
const TIMEOUT = 15000;
const TABS = 2;
const CAPTURES_PER_ELEMENT = 2;

// Figure text is measured from 375 px (docs/regles-redaction.md §5); the header rule
// applies to the 390×844 first screen.
const DEVICES = [
  { id: "iphone-se", device: "iPhone SE", engine: "webkit", viewport: { width: 320, height: 568 }, header: false, svgText: false },
  { id: "iphone-13", device: "iPhone 13", engine: "webkit", viewport: { width: 390, height: 844 }, header: true, svgText: true },
  { id: "pixel-7", device: "Pixel 7", engine: "chromium", viewport: { width: 412, height: 839 }, header: false, svgText: true },
];
const THEMES = [{ id: "clair", colorScheme: "light" }, { id: "sombre", colorScheme: "dark" }];
const PROFILES = DEVICES.flatMap((d) => THEMES.map((t) => ({ ...d, id: `${d.id}-${t.id}`, theme: t })));

function htmlFiles(dir) {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) return name === "site_libs" ? [] : htmlFiles(path);
    return name.endsWith(".html") ? [path] : [];
  });
}

function parseArgs(argv) {
  const pages = [];
  let profiles = PROFILES;
  for (let i = 0; i < argv.length; i += 1) {
    if (argv[i] === "--profils") {
      const wanted = (argv[(i += 1)] || "").split(",").filter(Boolean);
      profiles = PROFILES.filter((p) => wanted.some((w) => p.id === w || p.id.startsWith(`${w}-`)));
    } else {
      pages.push(argv[i].replace(/\\/g, "/").replace(/^_site\//, ""));
    }
  }
  return { pages, profiles };
}

function loadAllowlist() {
  let data;
  try {
    data = JSON.parse(readFileSync(ALLOWLIST, "utf8"));
  } catch (e) {
    return { entries: [], errors: [`${relative(".", ALLOWLIST)} illisible : ${e.message}`] };
  }
  return parseAllowlist(data);
}

function firstLine(message) {
  return String(message).split("\n")[0];
}

async function load(page, url) {
  const response = await page.goto(url, { waitUntil: "load", timeout: TIMEOUT });
  if (!response || response.status() >= 400) throw new Error(`réponse ${response ? response.status() : "absente"}`);
  await page.evaluate(() => document.fonts.ready.then(() => new Promise((done) => {
    requestAnimationFrame(() => requestAnimationFrame(done));
  })));
}

// Viewport screenshot centred on the first element reported for `rule` (WebKit refuses
// screenshots taller than 32 767 px, so never the full page).
async function capture(page, name, rule) {
  await page.evaluate((r) => {
    if (!document.getElementById("check-mobile-outline")) {
      const style = document.createElement("style");
      style.id = "check-mobile-outline";
      style.textContent = "[data-check-mobile] { outline: 3px solid #d4007a !important; outline-offset: -2px !important; }";
      document.head.appendChild(style);
    }
    const el = document.querySelector(`[data-check-mobile~="${r}"]`);
    if (el && el !== document.documentElement) el.scrollIntoView({ block: "center", inline: "nearest" });
  }, rule);
  const path = join(CAPTURES, `${name}--${rule}.png`);
  await page.screenshot({ path, scale: "css", animations: "disabled" });
  return path;
}

// One screenshot per rule that fails on the page, and no more than CAPTURES_PER_ELEMENT
// per profile for the same element (the same header on 83 pages needs two, not 83).
async function captureAll(page, name, findings, taken) {
  const files = [];
  for (const rule of new Set(findings.map((f) => f.rule))) {
    const key = `${rule}\u0000${findings.find((f) => f.rule === rule).element}`;
    if ((taken.get(key) || 0) >= CAPTURES_PER_ELEMENT) continue;
    taken.set(key, (taken.get(key) || 0) + 1);
    files.push(await capture(page, name, rule));
  }
  return files;
}

// Taps the menu button and waits for the panel to finish opening. null: no menu button.
async function openMenu(page) {
  const toggler = page.locator(".navbar-toggler").first();
  if (!(await toggler.count()) || !(await toggler.isVisible())) return null;
  const target = (await toggler.getAttribute("data-bs-target")) || `#${await toggler.getAttribute("aria-controls")}`;
  try {
    await toggler.tap({ timeout: 3000 });
  } catch (e) {
    return { panel: target, error: `bouton du menu impossible à toucher (${firstLine(e.message)})` };
  }
  const opened = await page.waitForFunction((sel) => {
    const el = document.querySelector(sel);
    return el && el.classList.contains("show") && !el.classList.contains("collapsing");
  }, target, { timeout: 3000 }).then(() => true, () => false);
  return { panel: target, error: opened ? null : "le menu ne s'ouvre pas" };
}

async function checkMenu(page, options) {
  await page.evaluate(() => window.scrollTo(0, 0));
  const opened = await openMenu(page);
  if (!opened) return { findings: [], used: [] };
  if (opened.error) {
    return { findings: [{ rule: "menu", element: "button.navbar-toggler", text: "", detail: opened.error }], used: [] };
  }
  return page.evaluate((o) => window.CheckMobile.menu(window, o), { ...options, panel: opened.panel });
}

async function checkPage(page, path, { profile, base, allowlist, taken }) {
  const name = `${path.replace(/\.html$/, "").replace(/\//g, "__")}--${profile.id}`;
  const options = {
    width: profile.viewport.width,
    height: profile.viewport.height,
    header: profile.header,
    svgText: profile.svgText,
    allow: entriesFor(allowlist, path, profile.id),
  };
  const result = { page: path, profile: profile.id, findings: [], used: [], captures: [] };
  try {
    await load(page, new URL(path, base).href);
    const fixed = await page.evaluate((o) => window.CheckMobile.measure(window, o), options);
    if (fixed.errors) return { ...result, fatal: fixed.errors };
    if (profile.theme.colorScheme === "dark" && !fixed.dark) return { ...result, error: "le thème sombre ne s'applique pas" };
    result.captures.push(...(await captureAll(page, name, fixed.findings, taken)));
    const menu = await checkMenu(page, options);
    result.captures.push(...(await captureAll(page, name, menu.findings, taken)));
    return { ...result, findings: fixed.findings.concat(menu.findings), used: fixed.used.concat(menu.used) };
  } catch (e) {
    return { ...result, error: firstLine(e.message) };
  }
}

async function runProfile(browser, profile, pages, base, allowlist) {
  const { defaultBrowserType, ...device } = devices[profile.device];
  const context = await browser.newContext({
    ...device,
    viewport: profile.viewport,
    colorScheme: profile.theme.colorScheme,
    reducedMotion: "reduce",
    serviceWorkers: "block",
  });
  const origin = new URL(base).origin;
  await context.route((url) => url.origin !== origin, (r) => r.abort());
  for (const path of SCRIPTS) await context.addInitScript({ path });
  const run = { profile, base, allowlist, taken: new Map() };
  const start = Date.now();
  const queue = pages.slice();
  const results = [];
  // A few tabs per profile: page loads wait on the browser more than on the CPU.
  const tab = async () => {
    const page = await context.newPage();
    for (let path = queue.shift(); path; path = queue.shift()) {
      results.push(await checkPage(page, path, run));
    }
  };
  await Promise.all(Array.from({ length: TABS }, tab));
  await context.close();
  console.log(`  ${profile.id} : ${pages.length} pages en ${Math.round((Date.now() - start) / 1000)} s`);
  return results;
}

function printProblems(results, allowlist, complete) {
  const fatal = [...new Set(results.flatMap((r) => r.fatal || []))];
  for (const message of fatal) console.log(`ERREUR : ${message}`);
  const errors = results.filter((r) => r.error);
  if (errors.length) console.log(`\nPages non vérifiées — ${errors.length}`);
  for (const r of errors) console.log(`  • ${r.page} (${r.profile}) : ${r.error}`);
  const used = new Set(results.flatMap((r) => r.used));
  const unused = complete ? allowlist.filter((e) => !used.has(e.index)) : [];
  for (const e of unused) {
    console.log(`avert. exception n° ${e.index + 1} (${e.rule}, « ${e.selector} ») jamais utilisée : retirez-la si le problème a disparu.`);
  }
  return { fatal: fatal.length, errors: errors.length };
}

async function main() {
  const { pages: chosen, profiles } = parseArgs(process.argv.slice(2));
  const { entries, errors } = loadAllowlist();
  if (errors.length || !profiles.length) {
    for (const message of errors) console.log(`ERREUR : ${message}`);
    if (!profiles.length) console.log(`ERREUR : aucun profil ne correspond (${PROFILES.map((p) => p.id).join(", ")})`);
    process.exit(2);
  }
  const pages = chosen.length ? chosen : htmlFiles(SITE).map((f) => relative(SITE, f).split(sep).join("/")).sort();
  rmSync(CAPTURES, { recursive: true, force: true });
  mkdirSync(CAPTURES, { recursive: true });
  console.log(`check_mobile : ${pages.length} page(s) × ${profiles.length} profil(s)`);
  const server = await serve(SITE, PREFIX);
  const engines = { webkit, chromium };
  const browsers = {};
  let results;
  try {
    for (const engine of new Set(profiles.map((p) => p.engine))) browsers[engine] = await engines[engine].launch();
    const runs = profiles.map((p) => runProfile(browsers[p.engine], p, pages, server.url, entries));
    results = (await Promise.all(runs)).flat();
  } finally {
    await Promise.all(Object.values(browsers).map((b) => b.close()));
    await server.close();
  }
  console.log(formatReport(groupFindings(results)));
  const complete = !chosen.length && profiles.length === PROFILES.length;
  const problems = printProblems(results, entries, complete);
  const failing = results.filter((r) => r.findings.length);
  const count = failing.reduce((n, r) => n + r.findings.length, 0);
  const shots = results.reduce((n, r) => n + r.captures.length, 0);
  console.log(`\ncheck_mobile : ${count} constat(s) sur ${new Set(failing.map((r) => r.page)).size} page(s)` +
    (shots ? ` ; ${shots} capture(s) dans ${CAPTURES}/.` : "."));
  if (problems.fatal) process.exit(2);
  process.exit(count || problems.errors ? 1 : 0);
}

await main();
