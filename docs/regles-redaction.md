# Règles de rédaction

Ces règles s'appliquent à toute page du site, qu'elle soit écrite par une personne ou
rédigée avec l'aide d'une IA. Les règles mesurables sont vérifiées par
`tools/checks/check_content.py` (voir le README).

## 1. En-tête de chaque page (front matter)

```yaml
---
title: "Les anticoagulants oraux"
description: "Une phrase qui dit ce que la page apporte (utilisée par les moteurs de recherche)."
public: [patients, professionnels]   # patients, professionnels, etudiants
statut: brouillon                    # brouillon | relu | publie
relu_par: null                       # nom du relecteur, une fois relu
relu_le: null                        # AAAA-MM-JJ
prochaine_relecture: null            # AAAA-MM-JJ
substances: [warfarine, apixaban]    # fiches de classe et « maux courants » : substances, telles qu'écrites sur la page
sources:
  - titre: "ANSM, Thésaurus des interactions médicamenteuses"
    url: "https://ansm.sante.fr/documents/reference/thesaurus-des-interactions-medicamenteuses-1"
    consulte_le: 2026-11-25
pour_aller_plus_loin:                # facultatif : lectures complémentaires
  - titre: "Je prends un anticoagulant oral, quels sont les risques ?"
    url: "https://www.rfcrpv.fr/prends-anticoagulant-oral-risques/"
    site: rfcrpv                     # rfcrpv | cnpm, ou le nom du site en clair
---
```

- `sources` : au moins une source officielle par page de contenu (RCP ou notice de la
  base de données publique des médicaments, ANSM, HAS, EMA, recommandation d'une société
  savante, article publié). Pas de source secondaire quand la source primaire existe.
- Le filtre `assets/filters/page-meta.lua` affiche automatiquement le bandeau
  « Brouillon », les sources et les dates de relecture : ne pas les réécrire à la main.
- `substances` (fiches de classe et « maux courants ») : les substances dont parle la fiche, six
  au plus ; pour un mal courant, celles du traitement. Pas sur les fiches « situations », qui
  parlent de familles de médicaments. Le filtre
  ajoute « Notices et RCP officiels » : pour chacune, la page de la base de données publique
  des médicaments d'un médicament commercialisé qui la contient seule (forme orale, puis
  médicament de référence en premier), choisi par `tools/build/make_bdpm_liens.py`. Si la
  page cite dans ses sources (`sources:`, pas un lien dans le texte) un médicament
  commercialisé qui contient la substance seule, c'est lui l'exemple de cette page (la
  fiche enfant cite une suspension buvable). Après
  avoir ajouté une substance, relancer ce script ; `check_content.py` signale une substance
  sans lien.
- Un médicament de la base de données publique cité en source doit être encore
  commercialisé : `check_content.py` le vérifie (erreur `FM-BDPM`) d'après
  `data/bdpm-liens.json`, mis à jour chaque mois avec `fetch_bdpm.py` puis
  `make_bdpm_liens.py`.
- `pour_aller_plus_loin` : liens vers des contenus qui prolongent la page, d'abord ceux du
  réseau des CRPV ([rfcrpv.fr](https://www.rfcrpv.fr), `site: rfcrpv`) et du Collège national de
  pharmacologie médicale ([pharmacomedicale.org](https://pharmacomedicale.org), `site: cnpm`,
  écrit pour les professionnels et les étudiants). Trois liens au plus, en https, vérifiés
  avant d'être ajoutés ; le filtre les affiche dans « Pour aller plus loin », avant les
  sources. Ce ne sont pas des sources : ce que la page affirme reste sourcé dans `sources`.

## 2. Texte destiné aux patients

Tout texte pour les patients est placé dans un bloc :

```markdown
::: {.texte-patient}
...
:::
```

Les contrôles automatiques ne lisent que ces blocs pour les règles de vulgarisation.

Règles (d'après les guides de la HAS sur l'information écrite des patients, 2008 et 2012,
et les principes du FALC) :

1. Phrases courtes : 15 mots en moyenne, 25 au plus. Une idée par phrase.
2. Mots courants. Un terme médical est remplacé, ou expliqué entre parenthèses à sa
   première apparition (liste dans `data/jargon.yml`).
3. Pas de sigle sans sa forme développée à la première apparition.
4. Risques en fréquences naturelles : « 1 personne sur 100 », pas « 1 % » ni « 0,01 ».
   Même dénominateur pour comparer deux risques.
5. On s'adresse au lecteur : « vous ». Voix active.
6. Le message principal d'abord, dans un encadré :

   ```markdown
   ::: {.a-retenir}
   - trois points au plus
   :::
   ```

7. Sur chaque fiche médicament et chaque page « maux courants », un encadré
   `::: {.quand-consulter}` qui liste les signes qui doivent faire consulter. Il vient
   en tête de la partie patient pour les maux courants.
8. Des intertitres fréquents, de préférence sous forme de questions (un intertitre au
   moins tous les 150 mots).
9. Toujours : « Ne modifiez pas votre traitement sans en parler à votre médecin ou à votre
   pharmacien. »
10. Pas de tournures creuses ou typiques des textes générés : « il est important de
    noter », « en effet », « jouer un rôle clé », « dans un monde où », etc.

## 3. Texte destiné aux professionnels

Placé dans un bloc `::: {.texte-pro}`. Style d'une fiche de pharmacologie clinique :
précis, sourcé, chiffré. Les niveaux d'interaction suivent le Thésaurus de l'ANSM
(contre-indication, association déconseillée, précaution d'emploi, à prendre en compte).

### Dire le niveau de preuve d'un effet

Un effet signalé n'est pas un effet établi. Écrire ce que la source permet d'affirmer,
dans les textes patients comme professionnels :

| Ce que dit la source | Formulation |
|---|---|
| Effet indésirable listé à la rubrique 4.8 du RCP | « X peut provoquer Y », avec la fréquence du RCP |
| Signal en cours d'évaluation (ANSM, PRAC) | Pas de commentaire (voir section 4) ; au plus, renvoyer à la communication officielle |
| Association observée dans une étude | « Une étude a observé plus de Y chez les personnes traitées par X », avec le type d'étude |
| Cas rapportés (notifications, publications de cas) | « Des cas de Y ont été rapportés avec X » |

Ne jamais écrire « X provoque Y » sur la seule base de cas rapportés ou d'une
association observée. Rappeler, quand c'est utile, qu'une déclaration ne prouve pas
que le médicament est en cause.

## 4. Ce que le site ne fait pas

- Pas de conseil individuel. Renvoyer vers le CRPV, le médecin ou le pharmacien.
- Pas de commentaire sur un signal ou une enquête en cours d'évaluation.
- Pas d'information tirée des dossiers des centres (secret médical).
- Pas de chiffre inventé : un chiffre sans source est retiré ou remplacé par
  « [à compléter : source] ».
- Pas de nom de personne réelle sans son accord (équipes : gabarits seulement).

## 5. Figures

- Au moins une figure par page patient quand elle aide à comprendre (schéma, grille de
  personnages, frise du moment de prise).
- **Ce qu'on dessine** : seulement ce que dit le texte de la page (ou la consigne de la
  figure), sans nouvelle affirmation médicale ni chiffre absent de la page ; un chiffre sans
  source devient « [à compléter : source] » dans la page, pas dans la figure. Personnes,
  organes et objets sont des schémas sans échelle. Une figure qui demanderait de
  l'interaction (un clic) devient statique, ou son repère reste, inscrit dans `docs/STATUS.md`.
- **Sections à ouvrir** (le RCP annoté de comprendre/lire-un-rcp) : un bloc `::: {.rcp-annote}`
  contient un bloc `::: {.rcp-section numero="4.8" titre="Effets indésirables"}` par section,
  qui devient une ligne à ouvrir (`<details>`, sans JavaScript ; `assets/filters/rcp-annote.lua`).
  Chaque section commence par « **À y chercher.** » puis « **Dans ce RCP.** »
  (`tests/test_rcp_annote.py`).
- **Fichier** : SVG écrit à la main, `assets/img/figures/<page>-<n>.svg`, placé dans la page
  par le raccourci
  `{{< figure-svg <page>-<n> alt="…" legende="…" >}}` (`assets/filters/figure-svg.lua`).
  Le SVG est inséré dans la page, ce qui lui donne les polices du site (une image `<img>` ne
  le peut pas). `alt` dit ce que la figure montre ; `legende` est la phrase visible sous la
  figure ; `description="…"` (facultatif) détaille, pour les lecteurs d'écran, un schéma
  que le texte alternatif ne peut pas résumer (arbre de décision, frise). Dans un bloc
  patient, `check_content.py` relit `alt` et `legende` comme le reste du texte.
- **Format** : 440 unités de large au plus, dessiné à 1 unité = 1 px (`width` et `height`
  égaux au `viewBox`) : la figure garde sa taille sur ordinateur et rétrécit sur téléphone.
  Texte de 16 unités au moins, 17 ou 18 pour les libellés principaux (12 px au moins sur un
  téléphone de 375 px). Mise en page en hauteur : les frises et les parcours se lisent de
  haut en bas.
- **Police et texte** : Atkinson Hyperlegible Next (`font-family` sur `<svg>`), libellés en
  français, courts, sans sigle qui n'ait pas été développé dans la page avant la figure.
  Pas de flèche « → » dans le texte (absente des polices du site) : la dessiner.
- **Couleurs** : seulement les jetons de `assets/theme.scss`, écrits en hexadécimal ; ni
  `style`, ni opacité.
  - Texte : `pv-ink` ; `pv-ink-quiet` (secondaire, sur `pv-paper` ou `pv-mist`) ;
    `pv-signal-dark`, `pv-alert`, `pv-green-ink`, `pv-amber` (libellés de niveau, sur
    `pv-paper` ou sur leur teinte) ; `pv-paper` sur un fond foncé (`pv-ink`,
    `pv-signal-dark`, `pv-alert`).
  - Fonds de zones : `pv-paper`, `pv-mist`, `pv-mist-deep`, `pv-green-tint`,
    `pv-alert-tint`, `pv-amber-tint`.
  - Décor seulement, jamais du texte ni seul porteur d'un sens : `pv-cyan`, `pv-green`,
    `pv-or`, `pv-rule`, `pv-eau` (l'eau, un liquide).
  - Toute nouvelle paire texte/fond va dans `tools/checks/contrast_pairs.yml`
    (`check_contrast.py`, qui la vérifie dans les deux thèmes).
- **Lisible dans le noir** (thème sombre du site et extensions comme Dark Reader ; le
  pourquoi : `docs/mode-sombre.md`). Le SVG garde les jetons clairs ; le thème sombre
  donne à chacun sa valeur sombre (`$pv-figures-sombre` dans `assets/theme-sombre.scss`).
  Dark Reader, lui, assombrit le `fill` d'une grande forme comme un fond et éclaircit celui
  d'un texte, ou d'une forme de 32 px ou moins, comme une couleur de texte. D'où :
  - `fill="currentColor"` sur `<svg>` : un texte sans couleur propre prend celle du texte
    de la page ;
  - un texte porte sa couleur lui-même, pas celle d'un groupe `<g fill>` ; pas de couleur
    sur un `<tspan>` (colorer le `<text>` entier, garder le mot en gras) ;
  - pas de texte sur une forme pleine de 46 unités ou moins de côté (32 px sur un
    téléphone de 320 px) : une pastille numérotée a un bord seul (`fill="none"`), un badge
    fait plus de 46 unités de large ;
  - un motif (`<pattern>`) ne garde que ses traits, en `<path>` ; la teinte de la zone est
    une forme à part, dessous ;
  - une case de légende qui reprend une zone fait plus de 46 unités de large (sinon Dark
    Reader l'éclaircit quand il assombrit la zone) ;
  - une couleur nouvelle (carte d'accueil, grilles de fréquences comprises) a sa ligne
    dans `$pv-figures-sombre`.
- **Jamais la couleur seule** : `pv-signal`, `pv-signal-dark`, `pv-alert`, `pv-green-ink` et
  `pv-amber` ont presque la même clarté et se confondent en niveaux de gris ; leurs teintes
  aussi. Un niveau se lit à son mot (« Interdit », « À éviter », « Précaution ») et à sa
  forme : fond foncé plein pour « interdit », fond clair à bord plein pour « à éviter »,
  bord pointillé pour « précaution ». Deux courbes se distinguent par leur trait (plein,
  pointillé) ; dans une grille de personnages, les personnes concernées sont pleines,
  les autres vides.
- **Accessibilité** : le raccourci ajoute `role="img"`, le titre (`alt`) et la description ;
  les `id` du SVG commencent par son nom (plusieurs figures par page).
- `tools/checks/check_figures.py` vérifie les règles mesurables (taille, couleurs, police,
  `id`, raccourcis, lisibilité dans le noir sauf les cases de légende).
