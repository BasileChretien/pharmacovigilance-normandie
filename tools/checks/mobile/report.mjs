// Exceptions and report of the phone-layout check (tools/checks/check_mobile.mjs).
// Pure functions: tests/js/check-mobile.test.mjs.

export const RULE_LABELS = {
  defilement: "La page défile de côté",
  "hors-ecran": "Élément qui sort de l'écran, sans défilement pour l'atteindre",
  coupe: "Contenu coupé par une boîte qui ne défile pas",
  entete: "En-tête fixe trop haut sur le premier écran",
  menu: "Menu ouvert : lien hors de l'écran ou impossible à toucher",
  chevauchement: "Textes qui se chevauchent",
  "cible-tactile": "Cible tactile trop petite (WCAG 2.5.8)",
  "texte-petit": "Texte de moins de 12 px",
};

export const RULES = Object.keys(RULE_LABELS);
const KEYS = new Set(["regle", "selecteur", "pages", "profils", "raison"]);

/** "bon-usage/*.html" → RegExp; "*" stays within a folder, "**" crosses folders. */
export function globToRegExp(glob) {
  let out = "";
  for (let i = 0; i < glob.length; i += 1) {
    const c = glob[i];
    if (c === "*" && glob[i + 1] === "*") {
      out += ".*";
      i += 1;
    } else if (c === "*") out += "[^/]*";
    else if (c === "?") out += "[^/]";
    else out += c.replace(/[.+^${}()|[\]\\]/g, "\\$&");
  }
  return new RegExp(`^${out}$`);
}

function entryErrors(raw, n) {
  const where = `exception n° ${n}`;
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) return [`${where} : un objet est attendu`];
  const errors = Object.keys(raw).filter((k) => !KEYS.has(k)).map((k) => `${where} : clé inconnue « ${k} »`);
  if (!RULES.includes(raw.regle)) errors.push(`${where} : regle « ${raw.regle} » inconnue (${RULES.join(", ")})`);
  if (typeof raw.selecteur !== "string" || !raw.selecteur.trim()) errors.push(`${where} : selecteur CSS manquant`);
  if (typeof raw.raison !== "string" || raw.raison.trim().length < 10) errors.push(`${where} : raison manquante (une phrase)`);
  for (const key of ["pages", "profils"]) {
    const list = raw[key];
    if (list !== undefined && (!Array.isArray(list) || !list.length || list.some((s) => typeof s !== "string" || !s))) {
      errors.push(`${where} : ${key} doit être une liste de textes`);
    }
  }
  return errors;
}

/**
 * Reads the exceptions file: {"exceptions": [{regle, selecteur, raison, pages?, profils?}]}.
 * @returns {{entries: object[], errors: string[]}}
 */
export function parseAllowlist(data) {
  const list = data && Array.isArray(data.exceptions) ? data.exceptions : null;
  if (!list) return { entries: [], errors: ["le fichier d'exceptions doit contenir une liste « exceptions »"] };
  const errors = list.flatMap((raw, i) => entryErrors(raw, i + 1));
  if (errors.length) return { entries: [], errors };
  const entries = list.map((raw, index) => ({
    index,
    rule: raw.regle,
    selector: raw.selecteur.trim(),
    reason: raw.raison.trim(),
    pages: (raw.pages || ["**"]).map(globToRegExp),
    profiles: raw.profils || null,
  }));
  return { entries, errors: [] };
}

/** Exceptions that apply to a page (path in _site/, with "/") and a profile id. */
export function entriesFor(entries, page, profile) {
  return entries
    .filter((e) => e.pages.some((re) => re.test(page)))
    .filter((e) => !e.profiles || e.profiles.some((p) => profile === p || profile.startsWith(`${p}-`)))
    .map(({ index, rule, selector }) => ({ index, rule, selector }));
}

/**
 * Groups findings by rule and element across pages and profiles.
 * @param {{page: string, profile: string, findings: object[]}[]} results
 */
export function groupFindings(results) {
  const groups = new Map();
  for (const { page, profile, findings } of results) {
    for (const f of findings) {
      const key = `${f.rule}\u0000${f.element}`;
      if (!groups.has(key)) {
        groups.set(key, { rule: f.rule, element: f.element, texts: new Set(), details: new Set(), profiles: new Set(), pages: new Set(), count: 0 });
      }
      const g = groups.get(key);
      if (f.text) g.texts.add(f.text);
      g.details.add(f.detail);
      g.profiles.add(profile);
      g.pages.add(page);
      g.count += 1;
    }
  }
  return [...groups.values()].sort((a, b) => RULES.indexOf(a.rule) - RULES.indexOf(b.rule) || b.pages.size - a.pages.size);
}

function some(set, max, sep = " ; ") {
  const items = [...set];
  const shown = items.slice(0, max).join(sep);
  return items.length > max ? `${shown}${sep}(+ ${items.length - max})` : shown;
}

// "prefix a, b, c" cut into lines of `width` characters, aligned under the first item.
export function wrap(prefix, items, width = 100) {
  const indent = " ".repeat(prefix.length);
  const lines = [];
  let line = prefix;
  items.forEach((item, i) => {
    const piece = i < items.length - 1 ? `${item}, ` : item;
    if (line.length + piece.length > width && line !== prefix && line !== indent) {
      lines.push(line.trimEnd());
      line = indent;
    }
    line += piece;
  });
  lines.push(line);
  return lines.join("\n");
}

function quoted(set, max) {
  const items = [...set];
  if (!items.length) return "";
  const more = items.length > max ? ` (+ ${items.length - max})` : "";
  return ` « ${items.slice(0, max).join(" », « ")} »${more}`;
}

function formatGroup(g) {
  return [
    `  • ${g.element}${quoted(g.texts, 3)}`,
    `    ${some(g.details, 2)}`,
    `    profils : ${[...g.profiles].sort().join(", ")}`,
    wrap(`    pages (${g.pages.size}) : `, [...g.pages].sort()),
  ].join("\n");
}

/** The report printed at the end of the check. */
export function formatReport(groups) {
  const out = [];
  for (const rule of RULES) {
    const mine = groups.filter((g) => g.rule === rule);
    if (!mine.length) continue;
    const count = mine.reduce((n, g) => n + g.count, 0);
    const pages = new Set(mine.flatMap((g) => [...g.pages]));
    out.push(`\n${RULE_LABELS[rule]} — ${count} constat(s) sur ${pages.size} page(s)`);
    out.push(...mine.map(formatGroup));
  }
  return out.join("\n");
}
