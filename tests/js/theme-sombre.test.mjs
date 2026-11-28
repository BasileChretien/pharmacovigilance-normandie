// Tests for _includes/theme-sombre.html (dark theme: Dark Reader lock, printing in the
// light theme, state of the switch). Run: npm run test:js
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import vm from "node:vm";

const html = readFileSync(new URL("../../_includes/theme-sombre.html", import.meta.url), "utf8");
const SCRIPT = html.match(/<script>([\s\S]*)<\/script>/)[1];

// A minimal page: <head> with its <meta> tags, the stylesheets Quarto writes, the switch,
// and a <body> whose class Quarto sets to quarto-dark or quarto-light.
function page({ stored = null, systemDark = false, protocol = "https:", bodyClass = "", readyState = "complete" } = {}) {
  const listeners = {};
  const observers = [];
  const head = {
    children: [],
    appendChild(el) { el.parentNode = head; head.children.push(el); },
    removeChild(el) { head.children = head.children.filter((c) => c !== el); },
    querySelector(sel) {
      const name = sel.match(/name="([^"]+)"/)[1];
      return head.children.find((c) => c.attrs.name === name) || null;
    },
  };
  const classes = new Set(bodyClass.split(" ").filter(Boolean));
  const body = { classList: { contains: (c) => classes.has(c) } };
  const sheets = [
    { rel: "stylesheet", alternate: false },
    { rel: systemDark || stored === "alternate" ? "stylesheet" : "disabled-stylesheet", alternate: true },
  ];
  const toggle = { attrs: {}, setAttribute(k, v) { this.attrs[k] = v; } };
  const document = {
    head, body, readyState,
    createElement: () => ({ attrs: {}, setAttribute(k, v) { this.attrs[k] = v; } }),
    querySelectorAll(sel) {
      if (sel.includes("quarto-color-alternate")) { return sheets.filter((s) => s.alternate); }
      if (sel === ".quarto-color-scheme-toggle") { return [toggle]; }
      return [];
    },
    addEventListener(type, fn) { (listeners[type] ||= []).push(fn); },
  };
  const window = {
    location: { protocol },
    localStorage: { getItem: (k) => (k === "quarto-color-scheme" ? stored : null) },
    matchMedia: (q) => ({ matches: q.includes("dark") && systemDark }),
    addEventListener(type, fn) { (listeners[type] ||= []).push(fn); },
    MutationObserver: class {
      constructor(fn) { this.fn = fn; observers.push(this); }
      observe() {}
    },
  };
  return {
    window, document, sheets, toggle,
    locked: () => head.children.some((c) => c.attrs.name === "darkreader-lock"),
    fire: (type) => (listeners[type] || []).forEach((fn) => fn()),
    setBodyClass(c) { classes.clear(); classes.add(c); observers.forEach((o) => o.fn()); },
  };
}

function run(p) {
  vm.runInNewContext(SCRIPT, { window: p.window, document: p.document });
  return p;
}

test("Quarto's rule: the stored choice wins, otherwise the system setting", () => {
  const { sombreChoisi } = run(page()).window.pvThemeSombre;
  assert.equal(sombreChoisi("alternate", false), true);
  assert.equal(sombreChoisi("default", true), false);
  assert.equal(sombreChoisi(null, true), true);
  assert.equal(sombreChoisi(null, false), false);
});

test("a dark system locks Dark Reader out from the <head> on", () => {
  assert.equal(run(page({ systemDark: true, readyState: "loading" })).locked(), true);
});

test("a light page leaves Dark Reader at work", () => {
  assert.equal(run(page({ readyState: "loading" })).locked(), false);
  assert.equal(run(page({ systemDark: true, stored: "default", readyState: "loading" })).locked(), false);
});

test("the choice on the switch wins over a light system", () => {
  assert.equal(run(page({ stored: "alternate", readyState: "loading" })).locked(), true);
});

test("on a local file Quarto keeps no choice: the system decides", () => {
  assert.equal(run(page({ stored: "alternate", protocol: "file:", readyState: "loading" })).locked(), false);
});

test("the lock follows the switch once the page is there", () => {
  const p = run(page({ bodyClass: "quarto-light" }));
  assert.equal(p.locked(), false);
  p.setBodyClass("quarto-dark");
  assert.equal(p.locked(), true);
  assert.equal(p.toggle.attrs["aria-pressed"], "true");
  p.setBodyClass("quarto-light");
  assert.equal(p.locked(), false);
  assert.equal(p.toggle.attrs["aria-pressed"], "false");
});

test("the switch is a named toggle button", () => {
  const p = run(page({ bodyClass: "quarto-light" }));
  assert.equal(p.toggle.attrs.role, "button");
  assert.equal(p.toggle.attrs["aria-label"], "Thème sombre");
});

test("the page waits for the DOM before reading the body", () => {
  const p = run(page({ systemDark: true, bodyClass: "quarto-dark", readyState: "loading" }));
  assert.equal(p.toggle.attrs.role, undefined);
  p.fire("DOMContentLoaded");
  assert.equal(p.toggle.attrs["aria-pressed"], "true");
});

test("printing sets the dark stylesheet aside, then puts it back", () => {
  const p = run(page({ systemDark: true, bodyClass: "quarto-dark" }));
  const dark = p.sheets.find((s) => s.alternate);
  p.fire("beforeprint");
  assert.equal(dark.rel, "disabled-stylesheet");
  p.fire("afterprint");
  assert.equal(dark.rel, "stylesheet");
});

test("printing a light page leaves the disabled dark stylesheet alone", () => {
  const p = run(page({ bodyClass: "quarto-light" }));
  const dark = p.sheets.find((s) => s.alternate);
  p.fire("beforeprint");
  p.fire("afterprint");
  assert.equal(dark.rel, "disabled-stylesheet");
});
