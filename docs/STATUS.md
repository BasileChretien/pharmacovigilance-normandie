# État du projet

Mis à jour le 28/11/2026. Prototype non officiel, publié depuis la branche `main`.

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
- [ ] Figures qui attendent des documents des centres : pictogrammes officiels de conduite
      (fichiers et droits de reproduction de l'ANSM, medicaments/situations/conduite) ;
      déclarations par département et par année (rapports d'activité, normandie/chiffres) ;
      plan d'accès de chaque centre (image libre de droits ou plan du CHU autorisé, crpv/acces).

## À faire côté technique

Prochaines pull requests, dans l'ordre (décidé le 27/11/2026) :

- [x] Liens simples : EudraVigilance (fréquences), OMS–UMC (pourquoi déclarer), Thériaque
      (interactions, cytochromes), ARS et CPias Normandie (En Normandie).
- [ ] ameli.fr et vaccination-info-service.fr : répondent par une vérification anti-robot, y
      compris dans Chrome (27/11/2026) ; à vérifier à la main avant de les lier. Pages
      candidates : ameli, « Quel est le rôle du pharmacien dans la délivrance d'un médicament
      générique ? » (comprendre/generiques-biosimilaires) ; vaccination-info-service
      (professionnels), « Patient traité par immunosuppresseurs » (corticoïdes oraux,
      méthotrexate).
- [x] GPR (adaptation des doses au rein) : sitegpr.com héberge un casino en ligne ; le GPR est
      désormais sur vidal.fr/gpr.html (outils sur connexion), lié depuis les fiches sujet âgé
      et méthotrexate (27/11/2026).
- [x] Trouver son CRPV par code postal (crpv/trouver-mon-crpv.qmd) : liste ANSM mise à jour le
      14/09/2026, 30 centres ; à rafraîchir avec `tools/build/fetch_crpv.py` quand l'ANSM la change.
- [x] Fil des alertes officielles : informations de sécurité de l'ANSM (« risques
      médicamenteux ») et résumés du PRAC de l'EMA, relevés à la construction et chaque lundi
      (titre, date, lien, sans réécriture), date de relevé visible. Les flux RSS de l'ANSM ne
      contiennent que les actualités du jour : la liste est lue sur la page elle-même.
- [ ] Nommer le responsable du fil des alertes (CRPV et personne qui le vérifie chaque semaine).
- [x] Liens « notice officielle » et « RCP » sur les 15 fiches de classe (`substances:`),
      générés depuis les fichiers ouverts de la base de données publique des médicaments
      (fichiers du 20/11/2026), avec contrôle des médicaments cités encore commercialisés
      (`FM-BDPM`). Premier contrôle : IMODIUM 2 mg n'est plus commercialisé, remplacé par
      IMODIUMCAPS 2 mg sur la fiche diarrhée (à relire).
- [x] `substances:` sur 10 fiches « maux courants » (27/11/2026) : 76 substances avec une
      notice officielle. Pas sur la rhinite allergique ni sur les fiches « situations », qui
      parlent de familles de médicaments.
- [x] Recherche par nom de médicament (marque ou substance) : medicaments/chercher.qmd,
      12 175 médicaments commercialisés (BDPM du 20/11/2026, hors homéopathie : enregistrements homéopathiques et substances « pour préparations homéopathiques » ou « dynamisées »), chacun
      vers sa page officielle, et vers la fiche du site quand elle existe ; la recherche reste
      dans le navigateur. Index : `tools/build/make_bdpm_recherche.py`, à relancer chaque mois.
- [x] Lien « Signaler une correction » : adresse retenue pharmacovigilance@chu-caen.fr.
- [x] Médicaments remboursés en Normandie (normandie/medicaments-rembourses.qmd) : Open Medic 2025
      et estimations INSEE, 12 familles liées aux fiches, standardisation directe sur l'âge
      (3 tranches) et le sexe ; à faire valider par les CRPV (méthode et commentaire).
- [x] Archive des numéros de Vigiking (vigiking/archives.qmd) : 25 numéros depuis 2017, sommaires
      du site du réseau, filtrables ; liens seulement vers les PDF de rfcrpv.fr.
- [ ] Bulletin Vigiking produit depuis le site (prototype du 28/11/2026, `bulletin/`) : un
      fichier Word fait sur le modèle, déposé sur l'icône « Fabriquer le Vigiking », donne le PDF 16:9,
      la page web et la liste des points à vérifier ; mise en page éditoriale aux couleurs du site,
      références depuis PMID/DOI. Numéro d'octobre 2025 refait en local pour comparaison. À faire :
      essayer `Installer.bat` sur un poste des CHU ; à la fusion, faire pointer les liens de téléchargement du guide (`BRANCHE` dans `bulletin/guide/construire.py`, puis relancer ce script) vers `main`. À décider avec les CRPV : adoption, hébergement
      des numéros, accord des auteurs pour leur nom.
- [ ] Index de Vigiking par thème et hébergement des PDF sur le site : inventaire des numéros et
      accord des CRPV à obtenir ; sommaires de juillet 2017 à février 2019 à fournir.
- [x] Liste des publications générée depuis ORCID et OpenAlex (28/11/2026) : crpv/recherche.qmd,
      relevée chaque semaine pour les membres dont la carte (pages des équipes) donne
      l'identifiant ORCID ; trois dernières années, articles, revues, lettres, éditoriaux
      et chapitres, sans nom d'auteur. Vide tant qu'aucune carte n'est publiée. À décider
      avec les CRPV : afficher les auteurs, et la période.
- [x] Les 52 figures marquées `FIGURE À FAIRE` (28/11/2026) : 48 dessinées (comprendre 5, bon
      usage 5, fiches de classe 23, maux courants 11, situations 3, carte des départements
      générée depuis les contours officiels), style et contrôle dans `docs/regles-redaction.md`
      section 5 et `tools/checks/check_figures.py`. Quatre repères restent, inscrits plus haut
      (À faire par les CRPV) ou ci-dessous.
- [ ] RCP annoté interactif (comprendre/lire-un-rcp) : le tableau « Où chercher quoi ? » en donne
      déjà le contenu ; choisir avec les relecteurs un médicament dont annoter le RCP réel.
- [ ] Contrôles automatiques : mode « site » dans manuscript-guard ou script séparé (décision).
- [ ] Refaire le test avec de vrais utilisateurs normands après la relecture.
