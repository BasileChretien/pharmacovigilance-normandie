# Points à vérifier en relecture

Points signalés pendant la rédaction des brouillons (25/11/2026). Chaque page garde aussi ses
marques `[à compléter : source]` et ses `<!-- FIGURE À FAIRE -->`.
`uv run python tools/checks/check_content.py --strict` liste ce qui bloquerait la publication.

## Valables pour tout le site

- **Portail de déclaration** : l'ancienne adresse signalement-sante.gouv.fr renvoie une erreur
  de certificat. Le site utilise signalement.social-sante.gouv.fr, comme les RCP et l'ANSM.
- **Thésaurus de l'ANSM** : la version du 15/09/2023 est la dernière ; il reste en ligne sans
  mise à jour jusqu'au 15/06/2027. Les RCP et notices font foi. Les pages le disent.
- **CRAT (lecrat.fr)** : un rédacteur y a signalé une page de type « crypto casinos » ; rien de
  tel sur la page d'accueil ni le plan du site au 25/11/2026. À regarder avant publication.
- **CEIP-A de Caen** : d'après l'ANSM, il couvre les cinq départements normands.
- **Signes d'alerte** : plusieurs encadrés « Quand consulter » contiennent des signes ajoutés par
  les rédacteurs sans source littérale (voir par page).

## Par page

| Page | À vérifier |
|---|---|
| comprendre/frequences | Ordre des effets : notice (graves d'abord, puis par fréquence) et RCP (par organe) |
| comprendre/triangle-noir | Règlement d'exécution du symbole ; critères facultatifs |
| comprendre/benefice-risque | Source sur PSUR, PGR, études post-AMM ; benfluorex : retrait après « cas observés », pas forcément des déclarations |
| comprendre/generiques-biosimilaires | Définition légale (art. L5121-1 CSP), critères de bioéquivalence, listes MTE et groupes biosimilaires substituables (arrêtés 2026), remboursement en cas de refus du générique |
| comprendre/pourquoi-declarer | Article du CSP sur l'obligation de déclarer ; conseils « marque et numéro de lot » et « confusion de boîtes » non sourcés |
| classes/anticoagulants-oraux | Fiche HAS AOD de 2018 (statut de l'édoxaban) ; « un arrêt, même bref, expose au risque de caillot » et AOD contre-indiqués à l'allaitement sont des déductions |
| classes/ains | Chiffres de cas d'infections graves : ce sont des comptes de déclarations, pas des fréquences |
| classes/statines | Chiffres SAMSON tirés du rapport complet JACC 2021 (NEJM non accessible) |
| classes/antidiabetiques | Metformine et produits de contraste iodés : contre-indication (Thésaurus) ou association déconseillée (RCP) |
| classes/antihypertenseurs | Bêtabloquants et diltiazem/vérapamil lus dans un tableau PDF mal aligné ; phrase « une tension bien contrôlée protège… » non sourcée |
| classes/antidepresseurs | Fréquence du contrôle de la natrémie chez le sujet âgé ; délivrance des tricycliques |
| classes/ipp | « Appelez le 15 » pour sang dans les vomissements ou selles noires ; oméprazole et clopidogrel (RCP seulement) |
| classes/fluoroquinolones | Fluoroquinolones et corticoïdes : « à prendre en compte » (Thésaurus) ou à éviter (RCP) |
| classes/valproate-teratogenes | Topiramate : réévaluation semestrielle (tableau ANSM 2023) ou annuelle (guide 2024) ; doses en insuffisance rénale ou hépatique |
| classes/isotretinoine | Accord de soins toujours décrit par l'ANSM ; avertissement ANSM sur le risque neurodéveloppemental non repris |
| classes/methotrexate | Signe d'alerte « pris plusieurs jours de suite par erreur → 15 » |
| classes/levothyroxine | Doses en insuffisance rénale ou hépatique |
| classes/corticoides-oraux | Seuils d'ostéodensitométrie (texte SFR/GRIO 2014 non ouvert) ; signes d'alerte « soif », « selles noires », « fatigue après l'arrêt » |
| maux-courants/migraine | Recommandation SFEMC 2021 lue en résumé ; seuil du traitement de fond tiré de VIDAL ; niveaux du Thésaurus pour les triptans |
| maux-courants/diarrhee-aigue | Âge minimum du lopéramide (6 ou 8 ans selon la spécialité) ; recommandation française pour l'antibiothérapie de l'adulte |
| maux-courants/angine-mal-de-gorge | Signes d'alerte locaux (phlegmon, abcès) |
| maux-courants/rhume-toux | Issue de la réévaluation européenne de la pholcodine ; effets de la codéine à signaler |
| maux-courants/cystite | Pivmécillinam : 3 jours (HAS) ou 5 jours (RCP Selexid) |
| maux-courants/brulures-estomac | Délai entre antiacides et autres médicaments ; douleur thoracique d'origine cardiaque dans « Quand consulter » |
| maux-courants/constipation | Délai d'action du macrogol |
| maux-courants/rhinite-allergique | Gonflement du visage ou de la gorge dans « Quand consulter » |
| situations/sujet-age | Conditions exactes du bilan partagé de médication |
| situations/conduite | Date d'entrée en vigueur du pictogramme ; liste actuelle sur Légifrance |
| situations/grossesse-allaitement | AINS en gel ou crème ; état de la réforme du pictogramme grossesse |
| bon-usage/quand-prendre | IPP : « le matin » (Mopral) ou « avant un repas » (Inipomp) ; raisons non sourcées pour quatre médicaments |
| bon-usage/ecraser-couper | Liste OMéDIT : page « mise à jour octobre 2026 », fichier daté du 01/12/2025 ; mesures pour les médicaments CMR |
| bon-usage/cytochromes | Base : carte des cytochromes des HUG de mars 2020, lue par script ; vérifier chaque ligne ; statut de commercialisation en France vérifié de mémoire |
