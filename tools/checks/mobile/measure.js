// In-page measurements of the phone-layout check (tools/checks/check_mobile.mjs,
// docs/mobile.md). The check loads geometry.js then this file in each page and calls
// CheckMobile.measure(window, options), then CheckMobile.menu(window, options) once the
// menu is open. Each returns plain findings {rule, element, text, detail} and marks the
// elements it reports with data-check-mobile="<rule>" for the screenshots.
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory(require("./geometry.js"));
  else root.CheckMobile = factory(root.CheckMobileGeometry);
})(typeof self !== "undefined" ? self : this, function (G) {
  "use strict";

  const MARK = "data-check-mobile";
  const PSEUDO = "data-check-mobile-pseudo";
  const SVG_NS = "http://www.w3.org/2000/svg";
  const SKIP_TAGS = new Set(["SCRIPT", "STYLE", "NOSCRIPT", "TEMPLATE", "LINK", "META"]);
  // What a finger can tap (WCAG 2.5.8 targets).
  const TARGETS = [
    "a[href]", "button", "input:not([type=hidden])", "select", "textarea", "summary",
    "[role=button]", "[role=link]", "[role=tab]", "[role=checkbox]", "[role=switch]", "[role=menuitem]",
  ].join(", ");
  const RULES = ["defilement", "hors-ecran", "coupe", "entete", "menu", "chevauchement", "cible-tactile", "texte-petit"];

  // ---------- Report labels ----------

  function excerpt(text, max = 40) {
    const t = String(text || "").replace(/\s+/g, " ").trim();
    return t.length > max ? `${t.slice(0, max - 1)}…` : t;
  }

  function label(el) {
    if (!el || !el.tagName) return "?";
    let s = el.tagName.toLowerCase();
    if (el.id) s += `#${el.id}`;
    for (const c of Array.from(el.classList || []).slice(0, 2)) s += `.${c}`;
    return s;
  }

  // "parent > element::pseudo": stable from one page to the next, so findings group.
  function describe(el, pseudo) {
    const parent = el && el.parentElement;
    const context = parent && parent.tagName !== "BODY" && parent.tagName !== "HTML" ? `${label(parent)} > ` : "";
    return context + label(el) + (pseudo ? `::${pseudo}` : "");
  }

  function textOf(el) {
    if (!el || el.tagName === "HTML" || el.tagName === "BODY") return "";
    const get = (name) => (el.getAttribute ? el.getAttribute(name) : null);
    return get("aria-label") || el.textContent || get("alt") || get("title") || el.value || "";
  }

  // ---------- Context: viewport, style cache, allowlist ----------

  function context(win, options) {
    const doc = win.document;
    const styles = new Map();
    const rects = new Map();
    const ctx = {
      win, doc, options, vw: options.width, vh: options.height,
      visible: new Map(), hidden: new Map(), used: new Set(), errors: [], allow: {},
      style: (el) => styles.get(el) || styles.set(el, win.getComputedStyle(el)).get(el),
      rect: (el) => rects.get(el) || rects.set(el, G.fromRect(el.getBoundingClientRect())).get(el),
    };
    for (const entry of options.allow || []) {
      try {
        doc.querySelector(entry.selector);
        (ctx.allow[entry.rule] = ctx.allow[entry.rule] || []).push(entry);
      } catch (e) {
        ctx.errors.push(`exception n° ${entry.index + 1} : sélecteur CSS invalide « ${entry.selector} »`);
      }
    }
    if (!doc.getElementById("check-mobile-style")) {
      const style = doc.createElement("style");
      style.id = "check-mobile-style";
      style.textContent = `[${PSEUDO}="after"]::after, [${PSEUDO}="before"]::before { display: none !important; }`;
      doc.head.appendChild(style);
    }
    return ctx;
  }

  function allowed(ctx, rule, el) {
    for (const entry of ctx.allow[rule] || []) {
      if (el.closest && el.closest(entry.selector)) {
        ctx.used.add(entry.index);
        return true;
      }
    }
    return false;
  }

  function finding(ctx, rule, el, detail, extra = {}) {
    if (el && el.setAttribute) {
      const marks = (el.getAttribute(MARK) || "").split(" ").filter(Boolean);
      if (!marks.includes(rule)) el.setAttribute(MARK, marks.concat(rule).join(" "));
    }
    const text = extra.text != null ? extra.text : textOf(el);
    return { rule, element: describe(el, extra.pseudo), text: excerpt(text), detail };
  }

  // ---------- What is shown ----------

  function inSvg(el) {
    return el.namespaceURI === SVG_NS && el.ownerSVGElement != null;
  }

  // Content of a closed <details> is not shown, except its <summary>.
  function inClosedDetails(el) {
    const details = el && el.closest ? el.closest("details:not([open])") : null;
    if (!details) return false;
    const summary = Array.from(details.children).find((c) => c.tagName === "SUMMARY");
    if (el === details || (summary && summary.contains(el))) return inClosedDetails(details.parentElement);
    return true;
  }

  // Screen-reader-only text: clipped to nothing (Bootstrap's .visually-hidden and the like).
  function clippedAway(el, ctx) {
    if (!el || el.tagName === "BODY") return false;
    if (ctx.hidden.has(el)) return ctx.hidden.get(el);
    const s = ctx.style(el);
    const r = ctx.rect(el);
    const own = (s.clip && s.clip !== "auto")
      || /inset\(\s*50%|circle\(\s*0/.test(s.clipPath || "")
      || ((r.width <= 1 || r.height <= 1) && s.overflow !== "visible");
    const result = Boolean(own) || clippedAway(el.parentElement, ctx);
    ctx.hidden.set(el, result);
    return result;
  }

  function visible(el, ctx) {
    if (ctx.visible.has(el)) return ctx.visible.get(el);
    let result = !SKIP_TAGS.has(el.tagName) && el.getClientRects().length > 0;
    if (result && el.checkVisibility) result = el.checkVisibility({ opacityProperty: true, visibilityProperty: true });
    else if (result) result = ctx.style(el).visibility === "visible";
    result = result && !inClosedDetails(el) && !clippedAway(el, ctx);
    ctx.visible.set(el, result);
    return result;
  }

  // ---------- Which ancestors clip or scroll an element ----------

  function fixedContainer(s) {
    const backdrop = s.backdropFilter || s.webkitBackdropFilter || "none";
    return s.transform !== "none" || s.filter !== "none" || s.perspective !== "none" || backdrop !== "none"
      || /paint|layout|strict|content/.test(s.contain || "") || /transform|filter|perspective/.test(s.willChange || "");
  }

  // Ancestors whose overflow cuts or scrolls `el`, following containing blocks: an
  // absolute box escapes its static ancestors, a fixed box all but a transformed one.
  // <html> and <body> are left out: what they cut is lost, not scrollable.
  function clippers(el, ctx) {
    const out = [];
    let position = ctx.style(el).position;
    for (let node = el.parentElement; node && node !== ctx.doc.body && node !== ctx.doc.documentElement; node = node.parentElement) {
      const s = ctx.style(node);
      const contains = position === "fixed" ? fixedContainer(s)
        : position === "absolute" ? s.position !== "static" || fixedContainer(s) : true;
      if (!contains) continue;
      position = s.position;
      const x = s.overflowX !== "visible";
      const y = s.overflowY !== "visible";
      if (x || y) out.push({ node, x, y });
    }
    return out;
  }

  // The part of box `b` of `el` left visible by the ancestors that clip it, or null.
  function visibleBox(el, b, ctx) {
    let out = b;
    for (const c of clippers(el, ctx)) {
      const r = ctx.rect(c.node);
      const left = c.x ? r.left + c.node.clientLeft : -1e9;
      const top = c.y ? r.top + c.node.clientTop : -1e9;
      const right = c.x ? left + c.node.clientWidth : 1e9;
      const bottom = c.y ? top + c.node.clientHeight : 1e9;
      out = G.intersect(out, { left, top, right, bottom });
      if (!out) return null;
    }
    return out;
  }

  function hasAncestorIn(el, set) {
    for (let node = el.parentElement; node; node = node.parentElement) if (set.has(node)) return true;
    return false;
  }

  function outermost(list) {
    return list.filter((a) => !list.some((b) => b !== a && b.el.contains(a.el)));
  }

  function deepest(list) {
    return list.filter((a) => !list.some((b) => b !== a && a.el.contains(b.el)));
  }

  // ---------- Elements past the edges of the screen ----------

  function edgeOffenders(ctx) {
    const offenders = [];
    const set = new Set();
    for (const el of ctx.doc.body.querySelectorAll("*")) {
      if (inSvg(el) || !visible(el, ctx)) continue;
      const b = ctx.rect(el);
      if (b.width < 1 || b.height < 1) continue;
      const edges = G.pastEdges(b, ctx.vw);
      if (!edges.any || clippers(el, ctx).some((c) => c.x) || hasAncestorIn(el, set)) continue;
      set.add(el);
      offenders.push({ el, box: b, edges, fixed: inFixed(ctx, el) });
    }
    return offenders;
  }

  function edgeFinding(ctx, o) {
    const sides = [];
    if (o.edges.left) sides.push(`${G.px(o.edges.left)} à gauche`);
    if (o.edges.right) sides.push(`${G.px(o.edges.right)} à droite`);
    const fixed = o.fixed ? " (fixe, hors du défilement)" : "";
    return finding(ctx, "hors-ecran", o.el, `${G.size(o.box)}${fixed}, dépasse de ${sides.join(" et ")}`);
  }

  // ---------- Sideways scrolling and its cause ----------

  // Boxes whose content (pseudo-elements included) is wider than the box and reaches past
  // the right edge of the screen without an ancestor to clip it.
  function contentSpills(ctx) {
    const out = [];
    for (const el of ctx.doc.body.querySelectorAll("*")) {
      if (el.clientWidth === 0 || inSvg(el) || !visible(el, ctx) || inFixed(ctx, el)) continue;
      if (ctx.style(el).overflowX !== "visible" || el.scrollWidth <= el.clientWidth + G.TOLERANCE) continue;
      const r = ctx.rect(el);
      if (r.left + el.clientLeft + el.scrollWidth <= ctx.vw + G.TOLERANCE) continue;
      if (clippers(el, ctx).some((c) => c.x)) continue;
      out.push({ el, content: el.scrollWidth, inner: el.clientWidth });
    }
    return out;
  }

  // The ::before or ::after whose removal makes the content fit, if any.
  function spillingPseudo(ctx, el) {
    for (const which of ["after", "before"]) {
      const content = ctx.win.getComputedStyle(el, `::${which}`).content;
      if (!content || content === "none" || content === "normal") continue;
      el.setAttribute(PSEUDO, which);
      const fits = el.scrollWidth <= el.clientWidth + G.TOLERANCE;
      el.removeAttribute(PSEUDO);
      if (fits) return { which, content: content.replace(/^"|"$/g, "") };
    }
    return null;
  }

  // A text of `el` that runs past the edge (a long word or address that cannot wrap).
  function spillingText(ctx, el) {
    const range = ctx.doc.createRange();
    for (const node of el.childNodes) {
      if (node.nodeType !== 3 || !/\S/.test(node.data)) continue;
      range.selectNodeContents(node);
      if (range.getBoundingClientRect().right > ctx.vw + G.TOLERANCE) return node.data;
    }
    return null;
  }

  // A child that runs past the edge while not counted as shown (an anchor link at
  // opacity 0 still takes its place).
  function spillingChild(ctx, el) {
    return Array.from(el.children).find((child) => ctx.rect(child).right > ctx.vw + G.TOLERANCE) || null;
  }

  function explainSpill(ctx, s) {
    const detail = `contenu de ${G.px(s.content)} dans une boîte de ${G.px(s.inner)}`;
    const pseudo = spillingPseudo(ctx, s.el);
    if (pseudo) return { el: s.el, pseudo: pseudo.which, text: pseudo.content, detail };
    const text = spillingText(ctx, s.el);
    if (text) return { el: s.el, text, detail: `${detail}, texte sans coupure` };
    const child = spillingChild(ctx, s.el);
    const shown = child && visible(child, ctx) ? "" : " invisible";
    return child ? { el: s.el, detail: `${detail}, par l'enfant${shown} ${label(child)}` } : { el: s.el, detail };
  }

  // Last resort: hide children one at a time and follow the one whose removal stops the
  // sideways scroll, down to the element that alone causes it.
  function bisect(ctx) {
    const root = ctx.doc.documentElement;
    const scrolls = () => root.scrollWidth > root.clientWidth;
    let node = ctx.doc.body;
    for (let found = true; found;) {
      found = false;
      for (const child of node.children) {
        if (!visible(child, ctx)) continue;
        const before = child.style.getPropertyValue("display");
        const priority = child.style.getPropertyPriority("display");
        child.style.setProperty("display", "none", "important");
        const fixes = !scrolls();
        if (before) child.style.setProperty("display", before, priority);
        else child.style.removeProperty("display");
        if (fixes) { node = child; found = true; break; }
      }
    }
    return node === ctx.doc.body ? null : node;
  }

  // A fixed box (and what it holds) is outside the page: it cannot make the page scroll.
  function inFixed(ctx, el) {
    for (let node = el; node && node !== ctx.doc.body; node = node.parentElement) {
      if (ctx.style(node).position === "fixed") return true;
    }
    return false;
  }

  function overflowCauses(ctx, offenders) {
    const boxes = offenders.filter((o) => o.edges.right > 0 && !inFixed(ctx, o.el))
      .map((o) => ({ el: o.el, detail: `boîte de ${G.size(o.box)} qui dépasse de ${G.px(o.edges.right)} à droite` }));
    const spills = deepest(contentSpills(ctx)).filter((s) => !boxes.some((b) => s.el.contains(b.el)));
    const causes = boxes.concat(spills.map((s) => explainSpill(ctx, s)));
    if (causes.length) return causes;
    const el = bisect(ctx);
    return el ? [{ el, detail: "trouvé en masquant les éléments un à un" }] : [];
  }

  function sideScroll(ctx, offenders) {
    const root = ctx.doc.documentElement;
    if (root.scrollWidth <= root.clientWidth) return [];
    const page = `page de ${G.px(root.scrollWidth)} pour ${G.px(root.clientWidth)} d'écran`;
    const causes = overflowCauses(ctx, offenders);
    const kept = causes.filter((c) => !allowed(ctx, "defilement", c.el));
    if (causes.length && !kept.length) return [];
    if (!kept.length) return [finding(ctx, "defilement", root, `${page}, cause non trouvée`)];
    return kept.map((c) => finding(ctx, "defilement", c.el, `${c.detail} (${page})`, c));
  }

  // ---------- Fixed header ----------

  function headerFindings(ctx) {
    const bands = [];
    for (const el of ctx.doc.body.querySelectorAll("*")) {
      const position = ctx.style(el).position;
      if ((position !== "fixed" && position !== "sticky") || !visible(el, ctx)) continue;
      const b = ctx.rect(el);
      if (b.top > G.TOLERANCE || b.bottom <= 0 || b.width < ctx.vw / 2) continue;
      bands.push({ el, box: b });
    }
    const top = outermost(bands);
    const share = G.coverage(top.map((b) => [b.box.top, b.box.bottom]), ctx.vh);
    if (share <= G.HEADER_MAX || !top.length || top.every((b) => allowed(ctx, "entete", b.el))) return [];
    const detail = `couvre ${G.px(share * ctx.vh)} sur ${G.px(ctx.vh)} (${Math.round(share * 100)} %, 20 % au plus)`;
    return [finding(ctx, "entete", top[0].el, detail, { text: "" })];
  }

  // ---------- Text: overlaps and size ----------

  function textItems(ctx) {
    const items = [];
    const walker = ctx.doc.createTreeWalker(ctx.doc.body, ctx.win.NodeFilter.SHOW_TEXT);
    const range = ctx.doc.createRange();
    for (let node = walker.nextNode(); node; node = walker.nextNode()) {
      const el = node.parentElement;
      if (!el || !/\S/.test(node.data) || !visible(el, ctx)) continue;
      range.selectNodeContents(node);
      for (const r of range.getClientRects()) {
        if (r.width < 1 || r.height < 1) continue;
        const raw = G.fromRect(r);
        const b = visibleBox(el, raw, ctx);
        if (b) items.push({ el, node, box: b, raw });
      }
    }
    return items;
  }

  // ---------- Content cut by a box that does not scroll ----------

  // A box with overflow-x hidden or clip whose text runs past its sides: the reader cannot
  // scroll to it (a table at overflow: hidden). An ellipsis is a choice, not a cut.
  function cutFindings(ctx, items) {
    const out = [];
    for (const el of ctx.doc.body.querySelectorAll("*")) {
      const s = ctx.style(el);
      if ((s.overflowX !== "hidden" && s.overflowX !== "clip") || s.textOverflow === "ellipsis") continue;
      if (el.scrollWidth <= el.clientWidth + G.TOLERANCE || !visible(el, ctx)) continue;
      const r = ctx.rect(el);
      const left = r.left + el.clientLeft;
      const right = left + el.clientWidth;
      const cut = items.find((i) => el.contains(i.el) && (i.raw.right > right + G.TOLERANCE || i.raw.left < left - G.TOLERANCE));
      if (!cut || allowed(ctx, "coupe", el)) continue;
      const detail = `contenu de ${G.px(el.scrollWidth)} coupé à ${G.px(el.clientWidth)}, sans défilement (overflow-x: ${s.overflowX})`;
      out.push(finding(ctx, "coupe", el, detail, { text: cut.node.data }));
    }
    return out;
  }

  // Figure text is left out: an SVG scales as a whole, and check_figures.py checks its layout.
  function overlapFindings(ctx, items) {
    const related = (a, b) => a.el === b.el || a.el.contains(b.el) || b.el.contains(a.el);
    const pairs = G.overlappingPairs(items.filter((i) => !inSvg(i.el)), related);
    const seen = new Set();
    const out = [];
    for (const [a, b, common] of pairs) {
      if (seen.has(a.el) || allowed(ctx, "chevauchement", a.el) || allowed(ctx, "chevauchement", b.el)) continue;
      seen.add(a.el);
      const detail = `chevauche ${describe(b.el)} « ${excerpt(b.node.data, 30)} » sur ${G.size(common)}`;
      out.push(finding(ctx, "chevauchement", a.el, detail, { text: a.node.data }));
      finding(ctx, "chevauchement", b.el, detail);
    }
    return out;
  }

  // Rendered size of the text of `el`; SVG text scales with its figure. Figure text is
  // measured only where docs/regles-redaction.md §5 promises 12 px (375 px and wider).
  function fontSize(ctx, el) {
    const size = parseFloat(ctx.style(el).fontSize);
    if (!inSvg(el)) return size;
    if (!ctx.options.svgText) return null;
    const text = el.closest("text") || el;
    const m = text.getScreenCTM ? text.getScreenCTM() : null;
    return m ? size * Math.hypot(m.a, m.b) : size;
  }

  function smallTextFindings(ctx, items) {
    const seen = new Set();
    const out = [];
    for (const item of items) {
      if (seen.has(item.el)) continue;
      seen.add(item.el);
      const size = fontSize(ctx, item.el);
      if (size == null || size >= G.TEXT_MIN - 0.01 || allowed(ctx, "texte-petit", item.el)) continue;
      out.push(finding(ctx, "texte-petit", item.el, `texte de ${size.toFixed(1)} px (12 px au moins)`, { text: item.node.data }));
    }
    return out;
  }

  // ---------- Tap targets (WCAG 2.5.8) ----------

  function blockOf(ctx, el) {
    for (let node = el; node; node = node.parentElement) {
      const display = ctx.style(node).display;
      if (display !== "inline" && display !== "contents") return node;
    }
    return null;
  }

  // Inline exception: a link inside a sentence, its height set by the line of text.
  function inSentence(ctx, el) {
    if (ctx.style(el).display !== "inline") return false;
    const block = blockOf(ctx, el.parentElement);
    if (!block) return false;
    const walker = ctx.doc.createTreeWalker(block, ctx.win.NodeFilter.SHOW_TEXT);
    for (let node = walker.nextNode(); node; node = walker.nextNode()) {
      const parent = node.parentElement;
      if (!/[\p{L}\p{N}]/u.test(node.data) || parent.closest(TARGETS)) continue;
      if (blockOf(ctx, parent) === block && visible(parent, ctx)) return true;
    }
    return false;
  }

  // A box or radio button inside its <label> is tapped through the whole label.
  function tapBox(ctx, el) {
    const wrapper = el.tagName === "INPUT" && /^(checkbox|radio)$/.test(el.type) ? el.closest("label") : null;
    return ctx.rect(wrapper && visible(wrapper, ctx) ? wrapper : el);
  }

  // Stricter than WCAG 2.5.8 on purpose: its spacing exception is not applied, only the
  // inline one (docs/mobile.md).
  function targetFindings(ctx) {
    const out = [];
    for (const el of ctx.doc.body.querySelectorAll(TARGETS)) {
      if (el.disabled || el.closest("[inert]") || !visible(el, ctx)) continue;
      const b = tapBox(ctx, el);
      if (b.width < 1 || b.height < 1 || !G.tooSmall(b)) continue;
      if (inSentence(ctx, el) || allowed(ctx, "cible-tactile", el)) continue;
      out.push(finding(ctx, "cible-tactile", el, `${G.size(b)} (24×24 px au moins)`));
    }
    return out;
  }

  // ---------- Entry points ----------

  function measure(win, options) {
    const ctx = context(win, options);
    if (ctx.errors.length) return { errors: ctx.errors };
    const offenders = edgeOffenders(ctx);
    const items = textItems(ctx);
    const findings = [
      ...sideScroll(ctx, offenders),
      ...offenders.filter((o) => !allowed(ctx, "hors-ecran", o.el)).map((o) => edgeFinding(ctx, o)),
      ...cutFindings(ctx, items),
      ...(options.header ? headerFindings(ctx) : []),
      ...overlapFindings(ctx, items),
      ...targetFindings(ctx),
      ...smallTextFindings(ctx, items),
    ];
    return { findings, used: Array.from(ctx.used), dark: win.document.body.classList.contains("quarto-dark") };
  }

  function menuProblem(ctx, link, b) {
    if (!G.insideViewport(b, ctx.vw, ctx.vh)) {
      return `${G.size(b)} hors de l'écran (de x ${Math.round(b.left)} à ${Math.round(b.right)}, de y ${Math.round(b.top)} à ${Math.round(b.bottom)})`;
    }
    const c = G.center(b);
    const hit = ctx.doc.elementFromPoint(c.x, c.y);
    if (!hit || !(hit === link || link.contains(hit))) return `caché par ${hit ? describe(hit) : "rien"} à l'endroit du doigt`;
    if (G.tooSmall(b)) return `${G.size(b)} (24×24 px au moins)`;
    return null;
  }

  // Each link of the opened menu, brought into view, must be on screen and on top.
  function menu(win, options) {
    const ctx = context(win, options);
    const panel = ctx.doc.querySelector(options.panel);
    const links = panel ? Array.from(panel.querySelectorAll(TARGETS)).filter((el) => visible(el, ctx)) : [];
    if (!links.length) return { findings: [finding(ctx, "menu", panel || ctx.doc.documentElement, "le menu ouvert ne montre aucun lien")], used: [] };
    const findings = [];
    for (const link of links) {
      link.scrollIntoView({ block: "nearest", inline: "nearest" });
      const problem = menuProblem(ctx, link, G.fromRect(link.getBoundingClientRect()));
      if (problem && !allowed(ctx, "menu", link)) findings.push(finding(ctx, "menu", link, problem));
    }
    return { findings, used: Array.from(ctx.used) };
  }

  return { RULES, TARGETS, MARK, excerpt, label, describe, inClosedDetails, measure, menu };
});
