// trouver-crpv.js — "Trouver votre centre": a postal code gives the regional
// pharmacovigilance centre of its department (Paris: of its arrondissement).
// Data: the JSON block #crpv-donnees written by tools/build/make_crpv_page.py from the
// ANSM list. Everything runs in the browser: the postal code is sent nowhere. Without
// JavaScript the form stays hidden and the full table of centres remains.
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

  // Department of a postal code: two digits, three overseas (971…976), and Corsica split
  // between Corse-du-Sud (20000-20199) and Haute-Corse (20200-20699).
  function departement(codePostal) {
    var cp = String(codePostal || "").replace(/\s+/g, "");
    if (!/^\d{5}$/.test(cp)) return null;
    if (cp.slice(0, 2) === "97") return cp.slice(0, 3);
    if (cp.slice(0, 2) === "20") return Number(cp) < 20200 ? "2A" : "2B";
    return cp.slice(0, 2);
  }

  // Arrondissement of a Paris postal code: 75001-75020, and 75116 for the 16th.
  function arrondissement(codePostal) {
    var cp = String(codePostal || "").replace(/\s+/g, "");
    if (cp === "75116") return 16;
    var m = /^750(\d{2})$/.exec(cp);
    if (!m) return null;
    var n = Number(m[1]);
    return n >= 1 && n <= 20 ? n : null;
  }

  // Centres covering a postal code, each with the part of the department it covers
  // (the Yvelines are split between two Paris centres).
  function trouver(codePostal, centres) {
    var dep = departement(codePostal);
    if (!dep) return [];
    var arr = dep === "75" ? arrondissement(codePostal) : null;
    var results = [];
    centres.forEach(function (centre) {
      centre.departements.forEach(function (d) {
        if (d.code !== dep) return;
        if (dep === "75" && !(d.arrondissements || []).includes(arr)) return;
        results.push({ centre: centre, precision: d.precision || null, departement: d });
      });
    });
    return results;
  }

  function element(doc, tag, text, attributes) {
    var node = doc.createElement(tag);
    if (text) node.textContent = text;
    Object.keys(attributes || {}).forEach(function (k) { node.setAttribute(k, attributes[k]); });
    return node;
  }

  function telLink(doc, telephone) {
    var link = element(doc, "a", telephone.replace(/ /g, " "), { href: "tel:+33" + telephone.replace(/\D/g, "").slice(1) });
    return link;
  }

  function carte(doc, result) {
    var c = result.centre;
    var box = element(doc, "div", null, { class: "crpv-resultat" });
    box.appendChild(element(doc, "p", c.nom, { class: "crpv-resultat-nom" }));
    if (result.precision) {
      var part = { Nord: "le nord", Sud: "le sud", Est: "l'est", Ouest: "l'ouest" }[result.precision] || result.precision;
      box.appendChild(element(doc, "p", "Si vous habitez dans " + part + " du département (" + result.departement.nom + ").", { class: "crpv-resultat-precision" }));
    }
    var contacts = element(doc, "p");
    if (c.telephone) {
      contacts.appendChild(doc.createTextNode("Téléphone : "));
      contacts.appendChild(telLink(doc, c.telephone));
    }
    if (c.courriel) {
      contacts.appendChild(element(doc, "br"));
      contacts.appendChild(doc.createTextNode("Courriel : "));
      contacts.appendChild(element(doc, "a", c.courriel, { href: "mailto:" + c.courriel }));
    }
    if (c.site) {
      contacts.appendChild(element(doc, "br"));
      // Named by its domain, as in the table: two cards never show two identical link texts.
      contacts.appendChild(element(doc, "a", c.site.replace(/^https?:\/\/(www\.)?/, "").split("/")[0], { href: c.site }));
    }
    box.appendChild(contacts);
    return box;
  }

  function init(doc) {
    var form = doc.getElementById("trouver-crpv");
    var donnees = doc.getElementById("crpv-donnees");
    if (!form || !donnees) return;
    var centres = JSON.parse(donnees.textContent).centres;
    var input = form.querySelector("input");
    var sortie = doc.getElementById("trouver-crpv-resultat");
    form.hidden = false;

    form.addEventListener("submit", function (event) {
      event.preventDefault();
      sortie.textContent = "";
      if (!departement(input.value)) {
        sortie.appendChild(element(doc, "p", "Saisissez les cinq chiffres de votre code postal, par exemple 14000."));
        return;
      }
      var results = trouver(input.value, centres);
      if (!results.length) {
        sortie.appendChild(element(doc, "p", "Aucun centre français ne couvre ce code postal. Consultez la liste ci-dessous, ou demandez à votre pharmacien."));
        return;
      }
      sortie.appendChild(element(doc, "p", results.length > 1 ? "Votre département est partagé entre deux centres :" : "Votre centre :", { class: "crpv-resultat-titre" }));
      results.forEach(function (r) { sortie.appendChild(carte(doc, r)); });
    });
  }

  return { departement: departement, arrondissement: arrondissement, trouver: trouver, init: init };
});
