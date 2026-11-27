// chercher-medicament.js — "Chercher un médicament": a brand name or a substance gives the
// marketed medicines that match, each with a link to its official page (notice and SmPC)
// in the public medicines database, and to this site's sheet when there is one.
// Data: assets/data/medicaments.json (tools/build/make_bdpm_recherche.py), loaded on the
// first search. Everything runs in the browser: the search is sent nowhere. Without
// JavaScript the form stays hidden and the link to the official database remains.
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

  var BDPM = "https://base-donnees-publique.medicaments.gouv.fr/medicament/";
  var LIMITE = 25;

  function normalise(text) {
    return String(text || "")
      .normalize("NFD")
      .replace(/[̀-ͯ]/g, "")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, " ")
      .trim();
  }

  // One entry per medicine, with the words searched: those of its name and substances.
  function preparer(data) {
    return data.medicaments.map(function (m) {
      var substances = m[2].map(function (i) { return data.substances[i]; });
      // One link per sheet, even when two of its substances (two salts) point to it.
      var vues = {};
      var fiches = m[2]
        .map(function (i) { return data.fiches[String(i)]; })
        .filter(function (f) {
          if (!f || vues[f[0]]) return false;
          vues[f[0]] = true;
          return true;
        });
      var nom = normalise(m[1]);
      return {
        cis: m[0],
        nom: m[1],
        url: BDPM + m[0] + "/extrait",
        substances: substances,
        fiches: fiches,
        debut: nom.split(" ")[0],
        mots: (nom + " " + normalise(substances.join(" "))).split(" "),
      };
    });
  }

  // Medicines whose words start with every word of the search; those whose name starts
  // with the first word come first, then by name.
  function chercher(requete, entrees, limite) {
    var termes = normalise(requete).split(" ").filter(Boolean);
    if (termes.join("").length < 2) return { total: 0, resultats: [] };
    var trouves = entrees.filter(function (e) {
      return termes.every(function (t) {
        return e.mots.some(function (mot) { return mot.indexOf(t) === 0; });
      });
    });
    trouves.sort(function (a, b) {
      var ra = a.debut.indexOf(termes[0]) === 0 ? 0 : 1;
      var rb = b.debut.indexOf(termes[0]) === 0 ? 0 : 1;
      return ra - rb || (a.nom < b.nom ? -1 : a.nom > b.nom ? 1 : 0);
    });
    return { total: trouves.length, resultats: trouves.slice(0, limite || LIMITE) };
  }

  function element(doc, tag, text, attributes) {
    var node = doc.createElement(tag);
    if (text) node.textContent = text;
    Object.keys(attributes || {}).forEach(function (k) { node.setAttribute(k, attributes[k]); });
    return node;
  }

  function ligne(doc, entree, racine) {
    var li = element(doc, "li", null, { class: "medicament" });
    var titre = element(doc, "p", null, { class: "medicament-nom" });
    titre.appendChild(element(doc, "a", entree.nom, { href: entree.url }));
    li.appendChild(titre);
    if (entree.substances.length) {
      li.appendChild(element(doc, "p", "Substance" + (entree.substances.length > 1 ? "s" : "") + " : " + entree.substances.join(", "), { class: "medicament-substances" }));
    }
    entree.fiches.forEach(function (f) {
      var p = element(doc, "p", "Fiche du site : ", { class: "medicament-fiche" });
      p.appendChild(element(doc, "a", f[1], { href: racine + f[0] }));
      li.appendChild(p);
    });
    return li;
  }

  function message(total, affiches) {
    if (!total) return "Aucun médicament commercialisé ne correspond. Vérifiez l'orthographe, ou cherchez la substance (par exemple paracétamol).";
    if (total === 1) return "1 médicament.";
    if (total > affiches) return total + " médicaments : voici les " + affiches + " premiers. Précisez, par exemple avec le dosage.";
    return total + " médicaments.";
  }

  function init(doc) {
    var form = doc.getElementById("chercher-medicament");
    if (!form || typeof fetch !== "function") return;
    var input = form.querySelector("input");
    var statut = doc.getElementById("chercher-medicament-statut");
    var liste = doc.getElementById("chercher-medicament-liste");
    var racine = form.getAttribute("data-racine") || "";
    var entrees = null;
    var chargement = null;
    var minuterie = null;
    form.hidden = false;

    function charger() {
      if (!chargement) {
        chargement = fetch(form.getAttribute("data-donnees"))
          .then(function (r) {
            if (!r.ok) throw new Error(String(r.status));
            return r.json();
          })
          .then(function (data) { entrees = preparer(data); })
          .catch(function () {
            chargement = null;
            statut.textContent = "La liste des médicaments n'a pas pu être chargée. Réessayez, ou utilisez la base de données publique des médicaments.";
          });
      }
      return chargement;
    }

    function afficher() {
      liste.textContent = "";
      if (normalise(input.value).replace(/ /g, "").length < 2) {
        statut.textContent = "";
        return;
      }
      if (!entrees) {
        statut.textContent = "Chargement de la liste des médicaments…";
        charger().then(function () { if (entrees) afficher(); });
        return;
      }
      var r = chercher(input.value, entrees);
      statut.textContent = message(r.total, r.resultats.length);
      r.resultats.forEach(function (e) { liste.appendChild(ligne(doc, e, racine)); });
    }

    input.addEventListener("focus", charger, { once: true });
    input.addEventListener("input", function () {
      clearTimeout(minuterie);
      minuterie = setTimeout(afficher, 200);
    });
    form.addEventListener("submit", function (event) {
      event.preventDefault();
      clearTimeout(minuterie);
      afficher();
    });
  }

  return { normalise: normalise, preparer: preparer, chercher: chercher, init: init };
});
