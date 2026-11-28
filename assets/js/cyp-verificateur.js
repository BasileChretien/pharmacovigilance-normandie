// cyp-verificateur.js — "Vérifier deux médicaments" on bon-usage/cytochromes.qmd (users found
// the enzyme table hard to use: they wanted to check a pair, as on the HUG card).
// The reader types two drugs (accents optional, suggestions as they type); for each enzyme of
// the grid and for P-gp, the checker looks for one drug as substrate and the other as
// inhibitor or inducer, and says which way the exposure may go, in plain French.
// Data: the JSON that tools/build/make_cytochromes.py writes from data/cytochromes.yml, the
// source of the grid too (_includes/cyp-donnees.md). Everything runs in the browser.
// Without JavaScript the form stays hidden and the grid below gives the same information.
// Suggestions follow the ARIA editable combobox with list autocomplete pattern.
(function (factory) {
  "use strict";
  var api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api; // unit tests (tests/js/)
  } else if (typeof document !== "undefined") {
    api.init(document);
  }
})(function () {
  "use strict";

  var LIMITE = 8;
  var ANNONCE_MS = 100;
  var TYPES = ["inhibiteur", "inducteur"];
  var SANS_CORRESPONDANCE = "aucun mécanisme substrat-inhibiteur ou substrat-inducteur dans ce tableau. Cela ne veut pas dire qu'il n'y a pas d'interaction.";

  // ---------- Text ----------------------------------------------------------------

  function fold(text) {
    return String(text || "")
      .normalize("NFD")
      .replace(/[̀-ͯ]/g, "")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, " ")
      .trim();
  }

  function upperFirst(text) { return text.charAt(0).toUpperCase() + text.slice(1); }
  function lowerFirst(text) { return text.charAt(0).toLowerCase() + text.slice(1); }
  // Sentences start with the drug's name and a colon ("Codéine : …"): a French drug name
  // would need an article ("de la codéine"), and the data do not hold its gender.

  function compare(a, b) { return a < b ? -1 : a > b ? 1 : 0; }

  // ---------- Search ----------------------------------------------------------------

  // Adds to each drug the words searched: those of its name and of its précision.
  function prepare(data) {
    var medicaments = data.medicaments.map(function (m) {
      var cle = fold(m.nom);
      return Object.assign({}, m, {
        cle: cle,
        mots: (cle + " " + fold(m.precision)).split(" ").filter(Boolean),
      });
    });
    return {
      enzymes: data.enzymes,
      sources: data.sources || {},
      defaut: data.source_par_defaut || "hug",
      medicaments: medicaments,
    };
  }

  // Drugs with a word starting with every typed word; names starting with the first word first.
  function suggest(query, medicaments, limite) {
    var termes = fold(query).split(" ").filter(Boolean);
    if (!termes.length) return [];
    var trouves = medicaments.filter(function (m) {
      return termes.every(function (t) {
        return m.mots.some(function (mot) { return mot.indexOf(t) === 0; });
      });
    });
    trouves.sort(function (a, b) {
      var ra = a.cle.indexOf(termes[0]) === 0 ? 0 : 1;
      var rb = b.cle.indexOf(termes[0]) === 0 ? 0 : 1;
      return ra - rb || compare(a.cle, b.cle);
    });
    return trouves.slice(0, limite || LIMITE);
  }

  // A typed name: the drug of that name, the only one that matches, or why there is none.
  function resolve(text, medicaments) {
    var cle = fold(text);
    var saisie = String(text || "").trim();
    if (!cle) return { statut: "vide", saisie: saisie };
    var exact = medicaments.filter(function (m) { return m.cle === cle; });
    if (exact.length === 1) return { statut: "trouve", medicament: exact[0] };
    var tous = suggest(text, medicaments, Infinity);
    if (tous.length === 1) return { statut: "trouve", medicament: tous[0] };
    if (tous.length > 1) return { statut: "ambigu", saisie: saisie, candidats: tous };
    return { statut: "absent", saisie: saisie };
  }

  function nextIndex(current, key, count) {
    if (!count) return -1;
    if (key === "ArrowDown") return current < 0 || current >= count - 1 ? 0 : current + 1;
    if (key === "ArrowUp") return current <= 0 ? count - 1 : current - 1;
    return current;
  }

  // ---------- Mechanisms ----------------------------------------------------------

  // Every enzyme where one drug is a substrate and the other an inhibitor or an inducer.
  // An inhibitor raises a substrate; for a prodrug, whose active substance the enzyme forms,
  // it lowers that substance instead. An inducer does the opposite.
  function mechanisms(a, b, enzymes) {
    if (!a || !b || a === b) return [];
    var liste = [];
    enzymes.forEach(function (enzyme) {
      var trouves = [];
      [[a, b], [b, a]].forEach(function (paire) {
        var substrat = paire[0];
        var effecteur = paire[1];
        var rs = (substrat.roles[enzyme.id] || {}).substrat;
        var re = effecteur.roles[enzyme.id] || {};
        if (!rs) return;
        TYPES.forEach(function (type) {
          if (!re[type]) return;
          trouves.push({
            enzyme: enzyme,
            substrat: substrat,
            effecteur: effecteur,
            type: type,
            force: re[type].force,
            voie: rs.voie,
            prodrogue: !!rs.prodrogue,
            actif: !!rs.actif,
            sens: (type === "inhibiteur") !== !!rs.prodrogue ? "hausse" : "baisse",
            cible: rs.prodrogue ? "metabolite" : "medicament",
            sources: { substrat: rs.source, effecteur: re[type].source },
          });
        });
      });
      trouves.sort(function (x, y) {
        return compare(x.substrat.cle, y.substrat.cle) || TYPES.indexOf(x.type) - TYPES.indexOf(y.type);
      });
      liste = liste.concat(trouves);
    });
    return liste;
  }

  // ---------- Plain-French wording ------------------------------------------------

  function headline(m) {
    var quoi = m.cible === "metabolite" ? "métabolite actif" : "exposition";
    return m.substrat.nom + " : " + quoi + " en " + m.sens;
  }

  function consequence(m) {
    if (m.cible === "metabolite") {
      return m.sens === "baisse"
        ? "Moins de métabolite actif formé : son efficacité peut diminuer."
        : "Plus de métabolite actif formé : son effet peut augmenter.";
    }
    return m.sens === "hausse"
      ? "Ses concentrations peuvent augmenter : risque de surdosage ou d'effets indésirables."
      : "Ses concentrations peuvent diminuer : risque de perte d'efficacité.";
  }

  function substrateDetail(role) {
    var details = ["voie " + role.voie];
    if (role.prodrogue) details.push("prodrogue");
    if (role.actif) details.push("métabolite actif");
    return "substrat (" + details.join(", ") + ")";
  }

  function cause(m) {
    return m.effecteur.nom + " : " + m.type + " " + m.force + " " + m.enzyme.de + ". "
      + m.substrat.nom + " : " + substrateDetail(m) + ".";
  }

  function notes(m, toutes, data) {
    var liste = [];
    var defaut = (data && data.defaut) || "hug";
    var sources = (data && data.sources) || {};
    // For a prodrug the minor pathway takes part in forming the active substance: its share of
    // the elimination says nothing about the effect (codeine + paroxetine is "déconseillée").
    // "Participe à", not "forme": one enzyme need not be the only route (clopidogrel).
    var s = m.substrat.nom;
    if (m.voie === "mineure" && m.prodrogue) {
      liste.push(s + " : voie mineure de son élimination, mais elle participe à la formation de son métabolite actif.");
    } else if (m.voie === "mineure") {
      liste.push(s + " : voie mineure de son élimination ; l'effet dépend de la part de cette voie.");
    }
    if (m.actif) liste.push(s + " : métabolite actif ; l'effet dépend aussi de ce métabolite.");
    // A source's "long" carries its own article: "la liste du Thésaurus…" (data/cytochromes.yml).
    [["effecteur", m.sources.effecteur], ["substrat", m.sources.substrat]].forEach(function (p) {
      if (p[1] && p[1] !== defaut && sources[p[1]]) {
        liste.push(m[p[0]].nom + " : classé d'après " + sources[p[1]].long + ".");
      }
    });
    var oppose = (toutes || []).some(function (o) {
      return o !== m && o.enzyme === m.enzyme && o.substrat === m.substrat && o.effecteur === m.effecteur && o.type !== m.type;
    });
    if (oppose) {
      liste.push(m.effecteur.nom + " : classé à la fois inhibiteur et inducteur " + m.enzyme.de + " ; l'effet global ne se déduit pas du tableau.");
    }
    return liste;
  }

  function summary(a, b, liste) {
    var debut = upperFirst(a.nom) + " et " + lowerFirst(b.nom) + " : ";
    if (!liste.length) return debut + SANS_CORRESPONDANCE;
    var enzymes = [];
    liste.forEach(function (m) { if (enzymes.indexOf(m.enzyme.id) < 0) enzymes.push(m.enzyme.id); });
    var n = liste.length;
    return debut + n + (n === 1 ? " mécanisme possible" : " mécanismes possibles") + " dans ce tableau (" + enzymes.join(", ") + ").";
  }

  function roleLabel(roles) {
    if (!roles) return "";
    var parts = [];
    if (roles.substrat) parts.push(substrateDetail(roles.substrat));
    TYPES.forEach(function (type) { if (roles[type]) parts.push(type + " " + roles[type].force); });
    return parts.length ? upperFirst(parts.join(" ; ")) : "";
  }

  function problem(label, r) {
    if (r.statut === "vide") return "Saisissez le médicament " + label + ".";
    if (r.statut === "absent") {
      return "« " + r.saisie + " » n'est pas dans ce tableau, qui ne cite que des exemples : cela ne veut pas dire qu'il n'interagit pas.";
    }
    if (r.statut === "ambigu") {
      var noms = r.candidats.slice(0, 6).map(function (m) { return lowerFirst(m.nom); }).join(", ");
      return "Médicament " + label + " : plusieurs correspondances (" + noms + (r.candidats.length > 6 ? "…" : "")
        + "). Choisissez-en un dans la liste.";
    }
    if (r.statut === "meme") return "Choisissez deux médicaments différents.";
    return "";
  }

  // What is wrong with the two fields, both at once: the fields to flag and one message.
  function problems(ra, rb) {
    var invalides = [];
    var messages = [];
    [["A", ra], ["B", rb]].forEach(function (p) {
      if (p[1].statut !== "trouve") {
        invalides.push(p[0]);
        messages.push(problem(p[0], p[1]));
      }
    });
    if (!invalides.length && ra.medicament === rb.medicament) {
      invalides.push("B");
      messages.push(problem("B", { statut: "meme" }));
    }
    return { invalides: invalides, message: messages.join(" ") };
  }

  function rolesCaption(a, b) {
    return upperFirst(a.nom) + " et " + lowerFirst(b.nom) + " : rôles, enzyme par enzyme";
  }

  // ---------- Page ----------------------------------------------------------------

  function el(doc, tag, attributes, text) {
    var node = doc.createElement(tag);
    Object.keys(attributes || {}).forEach(function (k) { node.setAttribute(k, attributes[k]); });
    if (text) node.textContent = text;
    return node;
  }

  function optionText(m) { return m.nom + (m.precision ? " (" + m.precision + ")" : ""); }

  // One field with its list of suggestions. lire() gives the chosen or typed drug; onEdit runs
  // at every keystroke (the result of the previous pair is then out of date).
  function combobox(doc, input, data, onChoice, onEdit) {
    var listbox = doc.getElementById(input.getAttribute("aria-controls"));
    var options = [];
    var active = -1;
    var choisi = null;

    function fermer() {
      options = [];
      active = -1;
      afficher();
    }

    function afficher() {
      listbox.textContent = "";
      options.forEach(function (m, i) {
        var li = el(doc, "li", { role: "option", id: listbox.id + "-" + i, "aria-selected": String(i === active) }, optionText(m));
        li.addEventListener("click", function () { choisir(m); });
        listbox.appendChild(li);
      });
      var ouvert = options.length > 0;
      listbox.hidden = !ouvert;
      input.setAttribute("aria-expanded", String(ouvert));
      if (active >= 0) {
        input.setAttribute("aria-activedescendant", listbox.id + "-" + active);
        var courant = listbox.children[active];
        if (courant && courant.scrollIntoView) courant.scrollIntoView({ block: "nearest" });
      } else {
        input.removeAttribute("aria-activedescendant");
      }
    }

    function choisir(m) {
      input.value = m.nom;
      choisi = m;
      input.removeAttribute("aria-invalid");
      fermer();
      onChoice();
    }

    input.addEventListener("input", function () {
      choisi = null;
      input.removeAttribute("aria-invalid");
      onEdit();
      options = suggest(input.value, data.medicaments);
      active = -1;
      afficher();
    });
    input.addEventListener("keydown", function (event) {
      var key = event.key;
      if (key === "ArrowDown" || key === "ArrowUp") {
        event.preventDefault();
        if (!options.length) options = suggest(input.value, data.medicaments);
        active = nextIndex(active, key, options.length);
        afficher();
      } else if (key === "Enter" && active >= 0 && options[active]) {
        event.preventDefault();
        choisir(options[active]);
      } else if (key === "Escape" && options.length) {
        event.preventDefault();
        fermer();
      }
    });
    input.addEventListener("blur", fermer);
    // Keep the focus in the field while an option is clicked.
    listbox.addEventListener("mousedown", function (event) { event.preventDefault(); });

    return {
      input: input,
      fermer: fermer,
      choisi: function () { return choisi; },
      lire: function () {
        if (choisi && input.value === choisi.nom) return { statut: "trouve", medicament: choisi };
        return resolve(input.value, data.medicaments);
      },
    };
  }

  function carte(doc, m, toutes, data) {
    var li = el(doc, "li", { class: "cyp-mecanisme cyp-" + m.sens });
    var titre = el(doc, "p", { class: "cyp-mecanisme-titre" });
    titre.appendChild(el(doc, "span", { class: "cyp-fleche", "aria-hidden": "true" }));
    titre.appendChild(el(doc, "strong", null, headline(m)));
    titre.appendChild(el(doc, "span", { class: "cyp-mecanisme-enzyme" }, m.enzyme.id));
    li.appendChild(titre);
    li.appendChild(el(doc, "p", null, consequence(m)));
    li.appendChild(el(doc, "p", { class: "cyp-mecanisme-cause" }, cause(m)));
    var n = notes(m, toutes, data);
    if (n.length) {
      var ul = el(doc, "ul", { class: "cyp-mecanisme-notes" });
      n.forEach(function (texte) { ul.appendChild(el(doc, "li", null, texte)); });
      li.appendChild(ul);
    }
    var pour = m.enzyme.de.replace(/^du /, "le ").replace(/^de la /, "la ");
    var lien = el(doc, "p", { class: "cyp-mecanisme-lien" });
    lien.appendChild(el(doc, "a", { href: "#" + m.enzyme.ancre }, "Exemples du Thésaurus pour " + pour));
    li.appendChild(lien);
    return li;
  }

  function tableauRoles(doc, a, b, liste, enzymes) {
    var table = el(doc, "table", { class: "cyp-roles" });
    table.appendChild(el(doc, "caption", null, rolesCaption(a, b)));
    var tete = el(doc, "tr");
    ["Enzyme", a.nom, b.nom].forEach(function (t) { tete.appendChild(el(doc, "th", { scope: "col" }, t)); });
    table.appendChild(el(doc, "thead")).appendChild(tete);
    var corps = table.appendChild(el(doc, "tbody"));
    enzymes.forEach(function (enzyme) {
      var tr = el(doc, "tr");
      var concerne = liste.some(function (m) { return m.enzyme === enzyme; });
      var th = el(doc, "th", { scope: "row" }, enzyme.id);
      // The row of a mechanism says so in words, not only by its tint.
      if (concerne) {
        tr.setAttribute("class", "cyp-roles-concerne");
        th.appendChild(el(doc, "span", { class: "cyp-roles-marque" }, "mécanisme possible"));
      }
      tr.appendChild(th);
      [a, b].forEach(function (m) {
        var td = el(doc, "td");
        var texte = roleLabel(m.roles[enzyme.id]);
        if (texte) {
          td.textContent = texte;
        } else {
          td.appendChild(el(doc, "span", { "aria-hidden": "true" }, "—"));
          td.appendChild(el(doc, "span", { class: "visually-hidden" }, "aucun rôle"));
        }
        tr.appendChild(td);
      });
      corps.appendChild(tr);
    });
    return table;
  }

  function init(doc) {
    var form = doc.getElementById("cyp-verificateur");
    var source = doc.getElementById("cyp-donnees");
    if (!form || !source) return;
    var data;
    try {
      data = prepare(JSON.parse(source.textContent));
    } catch (error) {
      // The form stays hidden: the grid below still gives every entry.
      console.error("cyp-verificateur : données illisibles", error);
      return;
    }
    var statut = doc.getElementById("cyp-statut");
    var resultat = doc.getElementById("cyp-resultat");
    var champs = {};
    var minuterie = null;
    champs.A = combobox(doc, doc.getElementById("cyp-a"), data, auChoix, effacer);
    champs.B = combobox(doc, doc.getElementById("cyp-b"), data, auChoix, effacer);
    form.hidden = false;

    function auChoix() {
      if (champs.A.choisi() && champs.B.choisi()) verifier();
    }

    // Emptied first, then filled: a live region repeats a text only when it changes, and the
    // same pair checked twice gives the same text.
    function annoncer(texte) {
      clearTimeout(minuterie);
      statut.textContent = "";
      minuterie = setTimeout(function () { statut.textContent = texte; }, ANNONCE_MS);
    }

    function effacer() {
      clearTimeout(minuterie);
      statut.textContent = "";
      resultat.textContent = "";
    }

    function verifier() {
      var ra = champs.A.lire();
      var rb = champs.B.lire();
      var erreurs = problems(ra, rb);
      if (erreurs.invalides.length) {
        resultat.textContent = "";
        erreurs.invalides.forEach(function (label) { champs[label].input.setAttribute("aria-invalid", "true"); });
        annoncer(erreurs.message);
        return;
      }
      var a = ra.medicament;
      var b = rb.medicament;
      [champs.A, champs.B].forEach(function (champ, i) {
        champ.input.value = (i ? b : a).nom;
        champ.input.removeAttribute("aria-invalid");
        champ.fermer();
      });
      var liste = mechanisms(a, b, data.enzymes);
      annoncer(summary(a, b, liste));
      resultat.textContent = "";
      if (liste.length) {
        var ul = el(doc, "ul", { class: "cyp-mecanismes" });
        liste.forEach(function (m) { ul.appendChild(carte(doc, m, liste, data)); });
        resultat.appendChild(ul);
      }
      resultat.appendChild(tableauRoles(doc, a, b, liste, data.enzymes));
    }

    form.addEventListener("submit", function (event) {
      event.preventDefault();
      verifier();
    });
  }

  return {
    LIMITE: LIMITE,
    fold: fold,
    prepare: prepare,
    suggest: suggest,
    resolve: resolve,
    nextIndex: nextIndex,
    mechanisms: mechanisms,
    headline: headline,
    consequence: consequence,
    cause: cause,
    notes: notes,
    summary: summary,
    roleLabel: roleLabel,
    problem: problem,
    problems: problems,
    rolesCaption: rolesCaption,
    init: init,
  };
});
