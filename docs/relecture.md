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

## Ajouts après le panel d'utilisateurs (25/11/2026)

| Page | À vérifier |
|---|---|
| maux-courants/fievre-douleur-enfant | Encadré « Ce soir » : pipette du sirop graduée en kilos, 6 h entre deux prises, 4 prises par 24 h (RCP Doliprane 2,4 %) |
| classes/anticoagulants-oraux | Règle d'oubli de l'apixaban (RCP Eliquis) ; noms de marque des AVK et des AOD ; règle des autres AOD à compléter |
| maux-courants/migraine | Encadré grossesse : AINS interdits dès le début du 6e mois, déconseillés avant ; paracétamol possible |
| situations/grossesse-allaitement | Encadré « Mal de tête ou fièvre ? » |
| classes/ains, classes/fluoroquinolones | Noms de marque ajoutés |
| declarer | Obligation de déclarer pour les professionnels (art. R. 5121-161 du CSP) ; conduite en EHPAD |
| que-faire-effet-indesirable | Page nouvelle : signes d'urgence, étapes, exemples |
| normandie/en | Numéro 3237 des pharmacies de garde ; réponse des CRPV en anglais |
| vigiking/inscription | Adresses provisoires pour recevoir Vigiking, à confirmer par les CRPV |
| crpv/acces | Horaires des deux centres |
| bon-usage/ecraser-fiche | Fiche imprimable : chaque règle reprend la page « Écraser ou couper » ; mesures de protection pour les médicaments CMR à préciser |
| bon-usage/cytochromes | Index par médicament généré automatiquement depuis le tableau : il hérite des points à vérifier du tableau |
| crpv/enseignement | Modalités de candidature proposées, à valider par chaque centre |
| bon-usage/interactions-ville | Page nouvelle, 16 associations : niveaux relevés sur le Thésaurus du 15/09/2023 (pages 26, 102 et 228 lues en texte seulement) ; « triple whammy » reconstitué à partir de trois couples ; clopidogrel + oméprazole d'après le RCP de Plavix |

## Ajouts après le 2e tour du panel (26/11/2026)

Synthèse : `docs/panel/synthese-tour2.md`.

| Page | À vérifier |
|---|---|
| maux-courants/fievre-douleur-enfant | Intervalle unique « 6 h si possible, jamais moins de 4 h, 4 prises par 24 h » ; exemple 16 kg ≈ 240 mg (15 mg/kg) ; « fièvre plus de 3 jours : consultez », repris de la page « enfant » et du RCP Doliprane 2,4 % |
| maux-courants/migraine | « 24 semaines d'aménorrhée » et « même en une seule prise » (ANSM, avril 2025) |
| situations/grossesse-allaitement | Phrase sur les fiches allaitement du CRAT |
| classes/anticoagulants-oraux | Advil et Nurofen cités comme exemples d'ibuprofène |
| normandie/en | Exemple de la toux sous IEC : « jusqu'à 1 personne sur 10 » (RCP du Triatec), conduite « ne pas arrêter seul, voir son médecin » |
| normandie/qui-contacter | Numéros des deux CRPV dans la ligne « Effet indésirable » |
| interactions-ville, statines, colchicine | Proposer une conduite de remplacement pour chaque contre-indication (par exemple autre macrolide ou suspension de la statine), d'après le Thésaurus et les RCP |
| classes/fluoroquinolones, que-faire-effet-indesirable | Harmoniser « arrêtez dès la douleur au tendon » et « ne modifiez pas votre traitement sans avis » : règle générale et exception |
| bon-usage/interactions | Ajouter pour les patients la pilule et les inducteurs enzymatiques (rifampicine, certains antiépileptiques), aujourd'hui seulement côté professionnels |
| bon-usage/ecraser-fiche | Version PDF d'une page après relecture ; protocole pas à pas pour l'équipe d'EHPAD, avec l'OMéDIT |

## Liens « Pour aller plus loin » (26/11/2026)

Demandés par le CRPV de Caen : 81 liens sur 46 pages vers le réseau des CRPV (rfcrpv.fr) et
le Collège national de pharmacologie médicale (pharmacomedicale.org), dans
`pour_aller_plus_loin` de chaque page. Tous répondaient le 26/11/2026.

| À vérifier | Pourquoi |
|---|---|
| Actualité de chaque article du réseau | Beaucoup affichent « modifié le 04/05/2024 » dans le plan du site, sans date de publication visible : cette date semble être celle de la migration du site, pas celle de l'article |
| Fiches du Collège | Pas de date de mise à jour visible ; elles sont écrites pour les professionnels et les étudiants |
| Choix des liens | Un lien par sujet évident ; certaines pages (conduite, quand prendre, lire une notice) n'en ont pas, faute de contenu correspondant |

## Liens vers d'autres sites (27/11/2026)

| Page | À vérifier |
|---|---|
| comprendre/frequences | EudraVigilance (adrreports.eu) : la mise en garde « un nombre de cas n'est ni une fréquence ni un risque » suffit-elle pour un lecteur patient ? |
| comprendre/pourquoi-declarer | Uppsala Monitoring Centre : fondation indépendante, centre collaborateur de l'OMS ; site en anglais |
| bon-usage/interactions-ville, bon-usage/cytochromes | Thériaque (CNHIM) : l'inscription est-elle toujours gratuite pour les professionnels ? |
| situations/sujet-age, classes/methotrexate | GPR : l'ancien site (sitegpr.com) héberge un casino en ligne ; le lien pointe vers vidal.fr/gpr.html, distribué par VIDAL depuis mai 2023. Outils sur connexion : gratuits pour les professionnels libéraux, abonnement annuel pour les établissements depuis le 01/09/2023. Financé en partie par des partenariats avec des entreprises du médicament (bannières affichées) : garder ce lien sur un site de CRPV ? |
| normandie/index, normandie/qui-contacter | ARS et CPIAS de Normandie : sites et intitulés ; coordonnées téléphoniques du CPIAS à compléter |

## Notices et RCP officiels (27/11/2026)

| Page | À vérifier |
|---|---|
| Fiches de classe | Les substances listées (`substances:`) : six au plus, celles dont parle la fiche. L'exemple de notice est choisi automatiquement (substance seule, forme orale, médicament de référence) : le garder, ou demander une autre spécialité |
| antidiabetiques | Sémaglutide : l'exemple est WEGOVY 1,5 mg comprimé (amaigrissement), pas un médicament du diabète |
| opioides | Codéine : l'exemple est PADERYL, un sirop contre la toux (codéine seule), alors que la fiche parle surtout de la codéine contre la douleur, associée au paracétamol |
| maux-courants/diarrhee-aigue | IMODIUM 2 mg n'est plus commercialisé (BDPM du 20/11/2026). Le texte professionnel suit désormais le RCP d'IMODIUMCAPS 2 mg (sans ordonnance) : à partir de 15 ans, 6 gélules par jour au plus, 2 jours au plus. À confirmer, ainsi que la phrase patient « de 6 à 8 ans ou plus » |

## Chercher un médicament (27/11/2026)

| Page | À vérifier |
|---|---|
| medicaments/chercher | Texte d'introduction et messages (aucun résultat, trop de résultats) ; homéopathie exclue de la liste : à confirmer. Le tri repose sur la composition déclarée : HOMEOPLASMINE (teintures et acide borique, sans mention homéopathique dans la base) reste dans la liste |

## Médicaments remboursés en Normandie (27/11/2026)

| Page | À vérifier |
|---|---|
| normandie/medicaments-rembourses | Méthode : boîtes remboursées (pas de doses), standardisation directe sur 3 tranches d'âge et le sexe, France sans Mayotte, population au milieu de 2025 (moyenne des 1er janvier 2025 et 2026, INSEE provisoire) |
| normandie/medicaments-rembourses | Familles (codes ATC) : benzodiazépines N05BA + N05CD + N05CF, opioïdes N02A, antidépresseurs N06A, IPP A02BC, AINS M01A, corticoïdes H02AB, statines C10AA, anticoagulants oraux B01AA + B01AF + B01AE07, antidiabétiques A10, lévothyroxine H03AA01, fluoroquinolones J01MA, antibiotiques J01 |
| normandie/medicaments-rembourses | Périmètre des codes ATC face aux fiches : A10 comprend les insulines (la fiche traite du diabète de type 2) ; H02AB comprend les formes injectables (la fiche traite des comprimés) ; C10AA laisse de côté les statines associées (C10B) ; M01A comprend M01AX (glucosamine, chondroïtine, diacéréine), qui ne sont pas des AINS. Ajuster les codes ou les libellés ?
| normandie/medicaments-rembourses | Commentaire : la phrase sur les trois plus grands écarts est générée ; faut-il un commentaire des CRPV sur les opioïdes, les antidépresseurs et les benzodiazépines ? |

## Archive de Vigiking (27/11/2026)

| Page | À vérifier |
|---|---|
| vigiking/archives | Sommaires repris tels que le réseau des CRPV les publie (quelques fautes de frappe d'origine, par exemple « EBNTRESTO ») ; numéros de juillet 2017 à février 2019 sans sommaire ; quelques sommaires réunissent plusieurs sujets sur une ligne (janvier–février 2020, juillet 2025) ; accord pour héberger les PDF sur le site |
