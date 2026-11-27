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
| Fiches de classe | Les substances listées (`substances:`) : six au plus, celles dont parle la fiche. L'exemple de notice est choisi automatiquement : le médicament que la fiche cite en source s'il contient la substance seule (14 cas au 27/11/2026, par exemple DETENSIEL au lieu de CARDENSIEL 1,25 mg sur l'hypertension), sinon substance seule, forme orale, médicament de référence : le garder, ou demander une autre spécialité |
| Maux courants | Listes `substances:` sur 10 des 11 fiches (27/11/2026) : les substances du traitement, pas celles citées pour une interaction ou à éviter. La rhinite allergique n'en a pas (la fiche parle de familles). Écartés car l'exemple ne convient pas : séné (préparation à la coloscopie), aspirine (100 mg antiagrégant), azélastine (collyre) |
| maux-courants/rhume-toux | Pseudoéphédrine : les 8 médicaments oraux qui en contiennent (ACTIFED RHUME, DOLIRHUME, HUMEX RHUME, NUROFEN RHUME, RHINADVIL…) sont « non commercialisés » dans la BDPM du 20/11/2026. La fiche met encore en garde contre ces comprimés : garder, ou dire qu'ils ne sont plus vendus ? |
| maux-courants/diarrhee-aigue | Racécadotril : l'exemple est TIORFAN 10 mg NOURRISSONS ; une forme adulte conviendrait mieux |
| maux-courants/fievre-douleur-enfant | Paracétamol : l'exemple est la suspension que la fiche cite (DOLIPRANE 2,4 %). Ibuprofène : la fiche ne cite aucun médicament à l'ibuprofène, l'exemple reste ADVIL 200 mg comprimé, qui ne convient pas au jeune enfant. Citer en source la suspension pédiatrique de référence, ou retirer l'ibuprofène de la liste ? |
| maux-courants/lombalgie | Liste limitée au paracétamol et à l'ibuprofène : le tramadol et la codéine (deuxième intention) n'y sont pas, l'exemple de la codéine étant un sirop contre la toux. Les ajouter ? |
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

## Figures (28/11/2026)

Schémas dessinés d'après le texte de chaque page (`assets/img/figures/`, règles en section 5 de
`docs/regles-redaction.md`). À relire comme le texte : le dessin, le texte alternatif et la
légende (dans la page, raccourci `figure-svg`).

| Page | Figure | À vérifier |
|---|---|---|
| comprendre/benefice-risque | Balance bénéfices/risques, puis avant et après l'autorisation | La balance penche du côté des bénéfices (« autorisé quand ses bénéfices dépassent ses risques ») ; « interactions » côté risques vient de la consigne de la figure, pas du texte patient |
| comprendre/generiques-biosimilaires | Deux boîtes, ce qui est identique et ce qui peut changer, deux courbes superposées | Les courbes sont exactement superposées, comme le dit le texte (« en même quantité et à la même vitesse ») ; faut-il montrer que la bioéquivalence admet un écart ? |
| comprendre/lire-une-notice | Notice dépliée, six rubriques | Les rubriques 2 et 4 sont marquées « à lire en priorité » (consigne de la figure) ; le texte ne le dit que de la rubrique 2. Libellé « Composition » pour la rubrique 6 |
| comprendre/pourquoi-declarer | Parcours d'une déclaration en cinq étapes, retour vers les mesures | « Le CRPV enregistre le cas » (étape 3) ; mesures citées : notice modifiée, restriction, retrait du marché |
| comprendre/triangle-noir | Haut d'une notice inventée (« Médicament X ») et boîte sans triangle | Seule la première phrase de la mention est reproduite |
| bon-usage/cytochromes | Entérocyte et hépatocyte, CYP3A4 et P-gp ; inhibiteur, inducteur, prodrogue | La P-gp n'est dessinée que dans l'entérocyte ; la prodrogue reprend l'exemple de la page (codéine, CYP2D6, fluoxétine) |
| bon-usage/ecraser-couper | Trois comprimés en coupe, entier et écrasé | Le schéma de la gélule à grains enrobés (ouverte, grains à ne pas écraser) |
| bon-usage/ecraser-couper | Arbre de décision avant d'écraser (soignants) | Fidèle aux trois recommandations de la liste OMéDIT reprises dans la page |
| bon-usage/interactions | Associations à éviter avec un anti-inflammatoire, le millepertuis, le pamplemousse, l'alcool | Liste par produit ajouté plutôt que tableau à double entrée (illisible sur téléphone à 4 colonnes) ; 13 exemples choisis parmi ceux de la page ; niveaux Interdit, À éviter, Précaution = contre-indication, association déconseillée, précaution d'emploi |
| bon-usage/quand-prendre | Frise d'une journée, médicaments du tableau | Oméprazole et hydrochlorothiazide (« le matin ») placés au petit-déjeuner ; la metformine à chaque repas, avec la mention « 2 ou 3 prises par jour » ; l'alendronate « jamais au coucher » ; le furosémide et le pantoprazole, sans moment fixe dans la page, ne figurent pas |
| medicaments/classes/ains | Semaine : 3 jours pour la fièvre, 5 pour la douleur, puis « Consultez » | Durées « sans avis médical », comme le texte |
| medicaments/classes/ains | Frise des 9 mois de grossesse | « Seulement si le médecin l'a prescrit » jusqu'à la fin du 5e mois, « interdit, même une seule prise » dès le début du 6e (24 semaines d'aménorrhée) ; le célécoxib, interdit toute la grossesse, est rappelé sous la frise d'après le texte |
| medicaments/classes/anticoagulants-oraux | Schéma de la coagulation | Simplifié : foie et vitamine K, facteur Xa, thrombine, caillot. Les AOD « bloquent le facteur Xa ou la thrombine », sans dire lequel, la page ne le précisant pas |
| medicaments/classes/anticoagulants-oraux | Moment de prise | AVK « plutôt le soir » (« de préférence » dans le texte) ; rivaroxaban « au repas », sans dire lequel ; l'édoxaban (une fois par jour) n'est pas dessiné, la consigne ne le citant pas |
| medicaments/classes/antidepresseurs | Frise du traitement | Durées de la page (2 à 4 semaines, au moins 6 mois après la guérison) ; « effets indésirables possibles, pas encore d'effet » pour les semaines 1 à 2 vient de la consigne |
| medicaments/classes/antidepresseurs | Deux grilles de 100 personnes (sertraline) | 23 et 12 sur 100, chiffres de la page |
| medicaments/classes/antidiabetiques | Semaine du sémaglutide | Exemple d'une injection le lundi : rattrapage possible jusqu'au samedi (« dans les 5 jours »), attente le dimanche |
| medicaments/classes/antidiabetiques | Signes de l'hypoglycémie, que prendre | Signes de la page ; « Oui » au sucre et à la boisson sucrée, « Non » à l'édulcorant |
| medicaments/classes/antihypertenseurs | Tension mesurée couché, assis, debout | La personne debout se lève en se tenant à une chaise (consigne) |
| medicaments/classes/antihypertenseurs | Trois médicaments, un rein | « Ensemble, ils peuvent bloquer les reins » (consigne) ; « surtout si vous êtes âgé ou buvez peu » (texte) |
| medicaments/classes/benzodiazepines-apparentes | Escalier de la baisse des doses | Ni durée ni dose chiffrées ; le palier plus long « en cas de gêne » vient de la consigne et du texte professionnel (« revenir au palier précédent, puis réduire plus lentement ») |
| medicaments/classes/corticoides-oraux | Frise d'une journée | Une prise le matin, au petit-déjeuner ; la note « forte dose au début : deux prises possibles » reprend le texte |
| medicaments/classes/fluoroquinolones | Prise de la lévofloxacine, 2 heures avant et après | La règle des 2 heures est donnée pour la lévofloxacine seule, comme dans la page (le RCP de la ciprofloxacine donne 1 à 2 heures avant ou au moins 4 heures après). Le lait n'est pas dans les zones de 2 heures, où la consigne le plaçait : la page dit seulement d'éviter le lait ou le yaourt pris seuls, en dehors d'un repas, avec la ciprofloxacine. Il est donc à part, sous la frise |
| medicaments/classes/fluoroquinolones | Grilles de 10 000 et de 1 000 points | Même taille de point pour les deux grilles ; « jusqu'à » 1 sur 10 000 (effets qui durent) et 1 sur 1 000 (tendons, lévofloxacine) |
| medicaments/classes/ipp | 1 Français sur 4, et plus de la moitié | La partie « pas justifiés » dépasse un repère « la moitié », sans proportion chiffrée : la page dit « plus de la moitié » |
| medicaments/classes/ipp | Arbre de décision après 4 semaines | « Demandez à votre médecin » avant tout arrêt (texte patient) ; « examen, plus petite dose efficace » vient de la consigne et du texte professionnel |
| medicaments/classes/isotretinoine | Prévention des grossesses en trois temps | La délivrance dans les 7 jours n'est pas dessinée (absente de la consigne) |
| medicaments/classes/levothyroxine | Frise d'une matinée | « 30 minutes » (consigne) pour « une demi-heure » (texte) ; fer ou calcium au moins 2 heures après le comprimé |
| medicaments/classes/methotrexate | Calendrier d'une semaine | Exemple : méthotrexate le lundi, acide folique le jeudi. La page ne fixe pas le jour de l'acide folique, seulement « jamais le même jour » |
| medicaments/classes/opioides | Trajet du message de la douleur | L'opioïde bloque le message dans la moelle épinière et dans le cerveau, comme le dit le texte |
| medicaments/classes/statines | Foie et artères | Deux artères comparées (beaucoup ou moins de cholestérol dans le sang) pour dire « moins encombrée » (consigne) ; « l'artère reste plus libre » est à relire |
| medicaments/classes/statines | Étude SAMSON, trois barres | Scores 8,0, 15,4 et 16,3 sur 100 du texte professionnel ; axe coupé à 20, signalé ; « 49 personnes jusqu'au bout » |
| medicaments/classes/valproate-teratogenes | Trois grilles de 100 enfants | Les fourchettes (2 à 3, 30 à 40) : personnages pleins jusqu'au bas de la fourchette, rayés jusqu'au haut |
| medicaments/classes/fluoroquinolones | Ligne de la ciprofloxacine (revue de #26) | La figure, comme le texte patient, ne donne pour la ciprofloxacine que le lait ou le yaourt pris seuls ; le délai avec le fer, le zinc, le calcium et les antiacides n'y est pas (RCP : 1 à 2 heures avant, au moins 4 heures après). À ajouter ? |
| medicaments/maux-courants/angine-mal-de-gorge | Test rapide en trois étapes | « avec un coton-tige » vient de la consigne ; « paracétamol si besoin » reprend le conseil de la page |
| medicaments/maux-courants/brulures-estomac | Œsophage et estomac, trois familles | Schéma sans échelle : grains d'antiacide dans l'acide, couche d'alginate qui flotte, « pompes » de la paroi pour les IPP |
| medicaments/maux-courants/constipation | Quatre marches | Ordre de la page ; la quatrième, « Puis consultez », vient de la consigne |
| medicaments/maux-courants/cystite | Arbre de décision | « Fièvre, douleur dans le dos, ou grossesse » (consigne) mène à « Consultez un médecin » ; « le jour même » est gardé pour la fièvre et la douleur dans le dos, la page disant pour la grossesse « consultez toujours un médecin » |
| medicaments/maux-courants/diarrhee-aigue | Préparer un soluté de réhydratation orale | Biberon gradué rempli jusqu'à 200 ml (consigne) |
| medicaments/maux-courants/fievre-douleur-enfant | Pipette graduée en kilos, et 24 heures | Graduations sans chiffre sauf 12 kg (exemple de la page) ; horaires 8 h, 14 h, 20 h et 2 h donnés en exemple par la consigne ; « jamais de moins de 4 heures » d'après la page |
| medicaments/maux-courants/insomnie | Frise d'une journée | « Sieste de moins d'une heure, avant 16 heures » et « écrans à limiter » suivent la page (la consigne disait « écrans éteints ») |
| medicaments/maux-courants/lombalgie | 10 personnages, 9 pleins | Le dixième « ne va pas mieux dans ce délai » : la page n'en dit pas plus |
| medicaments/maux-courants/migraine | Les 30 jours d'un mois, repères 8, 10 et 15 | Les 6 jours traités sont un exemple ; « depuis plus de 3 mois » vient de la page |
| medicaments/maux-courants/rhinite-allergique | Geste du spray nasal, de face et de côté | La tête penchée en avant et l'embout vers l'extérieur viennent de la consigne ; la page ne dit que « main droite pour la narine gauche » |
| medicaments/maux-courants/rhume-toux | Quatre gestes contre le rhume | « aérer » ajouté d'après la page (« aérez souvent ») |

