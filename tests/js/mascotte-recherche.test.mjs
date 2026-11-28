// Tests for _includes/mascotte-recherche.html (the mascot in the empty state of the site
// search, docs/mascotte/README.md). Run: npm run test:js
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import vm from "node:vm";

const html = readFileSync(new URL("../../_includes/mascotte-recherche.html", import.meta.url), "utf8");
const SCRIPT = html.match(/<script>([\s\S]*)<\/script>/)[1];
const VIDE = ".quarto-search-no-results:not(.no-query)";

// A page with Quarto's offset <meta>, and the "no results" boxes the search draws.
function page({ path = "/pharmacovigilance-normandie/comprendre/frequences.html", offset = "../" } = {}) {
  const boxes = [];
  let observer = null;
  const document = {
    body: { tag: "body" },
    querySelector: (sel) => (sel.includes("quarto:offset") ? { getAttribute: () => offset } : null),
    querySelectorAll(sel) {
      assert.equal(sel, VIDE);
      return boxes;
    },
    createElement: (tag) => ({ tag, className: "", attrs: {}, setAttribute(k, v) { this.attrs[k] = v; } }),
  };
  const window = {
    document,
    location: { pathname: path },
    MutationObserver: class {
      constructor(fn) { this.fn = fn; observer = this; }
      observe(target, options) { this.target = target; this.options = options; }
    },
  };
  vm.runInNewContext(SCRIPT, { window, document });
  return {
    observer: () => observer,
    addBox() {
      const box = {
        children: [],
        get firstChild() { return this.children[0] || null; },
        insertBefore(el, ref) { this.children.splice(ref ? this.children.indexOf(ref) : this.children.length, 0, el); },
        querySelector(sel) { return this.children.find((c) => sel === ".mascotte" && c.className === "mascotte") || null; },
      };
      boxes.push(box);
      return box;
    },
  };
}

test("an empty search shows one decorative mascot, found from the page's offset", () => {
  const p = page();
  const obs = p.observer();
  assert.equal(obs.target.tag, "body");
  assert.deepEqual({ ...obs.options }, { childList: true, subtree: true });
  const box = p.addBox();
  box.children.push({ className: "texte" });
  obs.fn();
  obs.fn(); // the search redraws often: still one mascot
  assert.equal(box.children.length, 2);
  const img = box.children[0];
  assert.equal(img.tag, "img");
  assert.equal(img.className, "mascotte");
  assert.equal(img.attrs.src, "../assets/img/mascotte/mascotte-recherche.svg");
  assert.equal(img.attrs.alt, "");
  assert.equal(img.attrs["aria-hidden"], "true");
});

test("the 404 page, served at any address, gives an absolute offset", () => {
  const p = page({ path: "/pharmacovigilance-normandie/nimporte/ou.html", offset: "/pharmacovigilance-normandie/" });
  const box = p.addBox();
  p.observer().fn();
  assert.equal(box.children[0].attrs.src, "/pharmacovigilance-normandie/assets/img/mascotte/mascotte-recherche.svg");
});

test("no mascot on medicine, alert or serious-harm pages", () => {
  for (const path of [
    "/pharmacovigilance-normandie/medicaments/",
    "/pharmacovigilance-normandie/medicaments/classes/ains.html",
    "/pharmacovigilance-normandie/medicaments/situations/grossesse-allaitement.html",
    "/pharmacovigilance-normandie/actualites/posts/alertes-officielles.html",
    "/pharmacovigilance-normandie/normandie/cas-marquants.html",
    "/pharmacovigilance-normandie/que-faire-effet-indesirable.html",
    // GitHub Pages also serves a page at its address without ".html".
    "/pharmacovigilance-normandie/normandie/cas-marquants",
    "/pharmacovigilance-normandie/que-faire-effet-indesirable",
  ]) {
    assert.equal(page({ path }).observer(), null, path);
  }
});
