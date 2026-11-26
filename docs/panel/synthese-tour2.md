# Panel d'utilisateurs, 2e tour : synthèse et décisions (26/11/2026)

Les dix mêmes participants **simulés** qu'au premier tour (`synthese.md`) ont refait leurs
trois tâches sur la version corrigée, plus une quatrième tâche nouvelle. Même méthode : liens
des pages rendues, index de recherche du site interrogé avec leurs propres mots, captures
d'écran sur ordinateur et sur téléphone. C'est une évaluation heuristique outillée, pas un test
avec de vraies personnes.

## Les trois tâches du premier tour, refaites

| Participant | Tâche 1 | Tâche 2 | Tâche 3 | Tour 1 → tour 2 (tâches réussies) |
|---|---|---|---|---|
| Martine | Oubli d'Eliquis : trouvé | Advil et anticoagulant : trouvé | Malaise, qui appeler : trouvé | 1 → 3 |
| Karim | Dose de paracétamol : partiel | Ibuprofène : trouvé | Antipoison : trouvé | 1 → 2 |
| Dr Sophie L. | Simvastatine + clarithromycine : trouvé | Déclarer : trouvé | Téléphone du CRPV : trouvé | 1 → 3 |
| Julien | Écraser un LP : trouvé | Pseudoéphédrine : trouvé | Recevoir Vigiking : partiel | 2 → 2 |
| Aïcha | Paracétamol enceinte : trouvé | Migraine enceinte : partiel | Source fiable : trouvé | 1 → 2 |
| Bernard | « Fréquent » : trouvé | Déclarer : trouvé | Grilles au clavier : partiel | 2 → 2 |
| Léa | Section 4.8 du RCP : trouvé | Stage au CRPV : partiel | Contraceptif + rifampicine : trouvé | 1 → 2 |
| Nathalie | Écraser : trouvé | Benzodiazépines et chutes : trouvé | Effet chez un résident : trouvé | 1 → 3 |
| James | Page en anglais : trouvé | Urgences : trouvé | Déclarer : partiel | 1 → 2 |
| Kevin | Talon et ciprofloxacine : trouvé | Gravité, qui appeler : partiel | Lisibilité : partiel | 0 → 1 |

**Bilan** : 22 tâches réussies sur 30, 8 partielles, aucun échec (tour 1 : 11 réussies,
17 partielles, 2 échecs).

## La quatrième tâche, nouvelle

| Participant | Tâche | Résultat |
|---|---|---|
| Martine | Téléphone du centre de sa zone | Partiel : numéro absent de l'accueil et de « Qui contacter » |
| Karim | Fièvre depuis 3 jours : quand consulter | Partiel : seuil absent de la fiche fièvre |
| Dr Sophie L. | Colchicine + clarithromycine | Trouvé (par le menu ; la recherche ratait le tableau) |
| Julien | Fiche « écraser » imprimable | Trouvé |
| Aïcha | Médicament et allaitement | Partiel : renvoi au CRAT sans dire qu'il a une rubrique allaitement |
| Bernard | Fiche médicament au clavier et au lecteur d'écran | Trouvé |
| Léa | Index des cytochromes par médicament | Trouvé |
| Nathalie | Procédure imprimable pour l'équipe | Partiel : la feuille porte « brouillon » |
| James | Toux et médicament de la tension | Non trouvé : rien en anglais |
| Kevin | « Je pense avoir un effet indésirable » | Trouvé |

Notes globales données par les participants : de 5 à 7 sur 10, moyenne 6.

## Ce qui marche

- La recherche par section : les mots du texte des fiches sont trouvés (« tendon »,
  « Eliquis », « chute »).
- Les deux parties patients et professionnels, titrées, imprimables.
- Le bandeau d'urgence, les encadrés « À retenir » et « Quand consulter », les entrées par
  public et les questions fréquentes.
- Les sources datées et les mentions de brouillon, jugées honnêtes.

## Problèmes, par fréquence, et décisions

| Problème | Participants | Décision | État |
|---|---|---|---|
| Crochets « [à compléter] », « [à vérifier] » visibles au milieu du texte | 10 | Les marquer comme éléments à compléter, sans les cacher | Fait : 101 marques transformées en étiquettes par le filtre `page-meta.lua` ; elles disparaîtront à la relecture |
| Bandeaux « prototype » et « brouillon » qui retirent la confiance | 10 | Garder jusqu'à la relecture médicale | Inchangé, volontairement |
| Recherche : accents exigés (« paracetamol », « pseudoephedrine »), synonymes absents (« newsletter », « broyer », « fausse route », « siprofloxacine », « lactation »), tableau des interactions en ville non indexé | 8 | Copie sans accents et synonymes ajoutés à l'index après chaque rendu ; titre de section avant le tableau | Fait : `tools/build/search_postprocess.py`, 312 entrées ; chaque requête des participants trouve la bonne page |
| Numéros des CRPV absents de l'accueil, de « Qui contacter » et des fiches | 5 | Numéros des deux centres dans le pied de chaque page et dans « Qui contacter » | Fait |
| Fiche fièvre : pas d'exemple pour 16 kg, 4 h ou 6 h selon le paragraphe, pas de seuil de durée | 1 (risque) | Un seul intervalle (6 h si possible, jamais moins de 4 h), exemple pour 16 kg, « fièvre plus de 3 jours : consultez » | Fait |
| Titres h1 → h3 sans h2 (fréquences, déclarer, plusieurs fiches) | 1 | Le filtre remonte les titres d'un niveau quand la page n'a pas de h2 ; h2 ajouté sur « Déclarer » | Fait : aucun saut de niveau sur les 78 pages |
| Sommaire « Sur cette page » réduit à « Sources et relecture » (44 pages sur 78) | 1 | Le filtre retire les enveloppes `texte-patient` et `texte-pro` à la sortie : Pandoc ignorait les titres placés dans un div ; contrôle `tools/checks/check_toc.py` en CI | Fait |
| Bouton de menu `role="menu"`, « Retour en haut » non focalisable, raccourcis clavier `f`, `/` et `s` en conflit avec NVDA | 2 | Retirer le rôle, retirer le lien, désactiver les raccourcis | Fait |
| Accueil sur téléphone : héros trop haut, urgences sous la ligne de flottaison ; bandeau d'urgence qui se chevauche à 1 024 px | 4 | Héros compact sous 576 px ; bandeau sur deux colonnes entre 992 et 1 199 px | Fait |
| Migraine et grossesse : « début du 6e mois » ambigu | 1 | Ajouter « 24 semaines d'aménorrhée », source ANSM, lien vers la fiche AINS | Fait |
| Allaitement : le CRAT cité sans dire qu'il a des fiches allaitement | 1 | Phrase dans la partie allaitement | Fait |
| Anglais : rien sur la toux sous IEC, pas de lien vers « Déclarer », libellés français sur la page anglaise | 1 | Exemple de la toux sous IEC (RCP du Triatec), lien vers « Déclarer », libellés générés en anglais | Fait |
| Pas de parcours pour les équipes d'EHPAD | 1 | Carte « Soignant en EHPAD ou à domicile » sur l'accueil | Fait |
| Advil absent de la fiche anticoagulants | 1 | Noms de marque dans la phrase sur les AINS | Fait |
| Pas d'alternative proposée aux contre-indications (simvastatine, colchicine + clarithromycine) | 1 | Contenu médical à rédiger d'après le Thésaurus et les RCP | Pour la relecture (`docs/relecture.md`) |
| Fluoroquinolones « arrêtez » contre « ne modifiez pas sans avis » sur « Que faire » | 1 | Harmoniser : la règle générale et son exception (tendinopathie) | Pour la relecture |
| Contraception et inducteurs absents de la page patients sur les interactions | 1 | Ligne patient à rédiger | Pour la relecture |
| Recevoir Vigiking par courriel seulement | 1 | Choix de l'outil d'envoi par les CRPV | À décider par les CRPV |
| Fiche « écraser » : pas de PDF, « brouillon » à l'impression ; protocole d'EHPAD pas à pas | 2 | PDF après relecture ; protocole à écrire avec l'OMéDIT | Après relecture |
| Page stages encore vide | 1 | Contenu à fournir par les CRPV | À faire par les CRPV |
| Tableaux longs sans filtre (interactions, cytochromes) | 2 | Champ de filtre au-dessus des tableaux, sans accents obligatoires | Fait (`assets/js/table-filter.js`) |
| Pages de démonstration dans les actualités (« format de démonstration ») | 3 | Retirer ou remplacer par de vrais billets au lancement | Au lancement |
| Version « facile à lire » (phrases courtes, pictogrammes) | 1 | Étudier le FALC pour les fiches les plus lues | Plus tard |

## Citations

> « Je cherche mon Eliquis, pas un anticoagulant oral direct… et le numéro, il est où ? » — Martine

> « Je veux juste savoir combien de millilitres je lui donne, là, tout de suite, et à quel moment j'appelle le médecin. » — Karim

> « J'ai trouvé la source en deux clics, mais pour m'abonner on m'envoie écrire un mail. » — Julien

> « J'ai tout compris à "fréquent" en deux minutes, mais j'ai cherché en vain le deuxième niveau de titre. » — Bernard

> « Le site m'a répondu vite, mais je n'imprimerai rien tant que c'est écrit "brouillon" en haut de la feuille. » — Nathalie

## Prochaine étape

La plupart des freins restants tiennent au statut de brouillon : relecture médicale, puis test
avec de vrais utilisateurs normands (patients partenaires des CHU, soignants d'EHPAD,
officinaux).
