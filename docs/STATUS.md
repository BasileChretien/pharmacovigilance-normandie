# État du projet

Mis à jour le 26/11/2026. Prototype non officiel, branche `feat/prototype-site`.

## Où on en est

- 78 pages construites, toutes au statut « brouillon ».
- En ligne sur <https://basilechretien.github.io/pharmacovigilance-normandie/> (dépôt public
  `BasileChretien/pharmacovigilance-normandie`, reconstruit à chaque push sur `main`).
- Design refait, puis corrigé d'après deux tours d'un panel de 10 utilisateurs simulés
  (`docs/panel/synthese.md`, `docs/panel/synthese-tour2.md`) : 11 puis 22 tâches réussies
  sur 30.
- Recherche tolérante aux accents, avec synonymes (`tools/build/search_postprocess.py`).
- Les marques « [à compléter] » s'affichent comme des étiquettes (101 à ce jour).
- Champ de filtre au-dessus des longs tableaux (interactions en ville, cytochromes et leur
  index par médicament) : `assets/js/table-filter.js`.
- Liens « Pour aller plus loin » vers rfcrpv.fr et pharmacomedicale.org sur 46 pages
  (`pour_aller_plus_loin` dans l'en-tête des pages).
- Design rafraîchi (26/11/2026) : en-tête sur deux lignes dès 1 200 px, cartes, pied de page
  « Manche », colombages, bandeau des deux centres, page 404.
- Contrôles automatiques en place : règles de rédaction, contrastes, HTML, accessibilité
  (axe-core), tests.

## Prochaine étape

Présenter le prototype aux CRPV de Caen et de Rouen, puis lancer la relecture médicale page
par page (`docs/relecture.md`).

## À faire par les CRPV ou les CHU

- [ ] Accord des deux CRPV et des CHU (directions de la communication, DSI, DPO).
- [ ] Relecture médicale de chaque page : passer `statut` à `relu`, remplir `relu_par` et
      `relu_le`, puis `check_content.py --strict` doit passer.
- [ ] Horaires des deux centres (`crpv/acces.qmd`).
- [ ] Stages : publics, durées, périodes, missions, modalités de candidature
      (`crpv/enseignement.qmd`).
- [ ] Recevoir Vigiking : confirmer l'adresse provisoire, puis choisir l'outil d'envoi.
- [ ] Logos : validation, et fichiers officiels (logo propre au CRPV de Rouen s'il existe).
- [ ] Membres des équipes : accord écrit, photo, biographie, lien SigmaCV.
- [ ] Rubriques à remplir : chiffres de la région, cas marquants, priorités régionales,
      formations, liens d'intérêts.
- [ ] Réponse des centres en anglais (page *Medicines safety in Normandy*).
- [ ] Usage du DSFR ou de la charte des CHU.

## À faire côté technique

Prochaines pull requests, dans l'ordre (décidé le 27/11/2026) :

- [ ] Liens simples : EudraVigilance (adrreports.eu, avec l'avertissement « un nombre de
      déclarations n'est pas un risque »), Thériaque (lien seulement), OMS–UMC, ARS et CPias
      Normandie, ameli.fr et vaccination-info-service.fr, GPR (après vérification du site).
- [ ] Fil des alertes officielles : flux RSS de l'ANSM (filtrables par domaine médical) et de
      l'EMA, récupérés à la construction (titre, date, lien, sans réécriture), reconstruit
      chaque semaine ; date de mise à jour visible et responsable nommé.
- [ ] Liens « notice officielle » et « RCP » sur chaque fiche, générés depuis les fichiers
      ouverts de la base de données publique des médicaments, avec contrôle des noms encore
      commercialisés.
- [ ] Recherche par nom de médicament (marque et DCI) depuis la même base, présentée comme
      pages officielles externes.
- [ ] Lien « Signaler une correction » : adresse retenue pharmacovigilance@chu-caen.fr (fait).
- [ ] Liste des publications générée depuis ORCID et OpenAlex.
- [ ] Les 52 figures marquées `FIGURE À FAIRE`.
- [ ] Contrôles automatiques : mode « site » dans manuscript-guard ou script séparé (décision).
- [ ] Refaire le test avec de vrais utilisateurs normands après la relecture.
