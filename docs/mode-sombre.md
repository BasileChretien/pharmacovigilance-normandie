# Mode sombre et Dark Reader

Pourquoi le site a un thème sombre, et pourquoi les figures sont dessinées comme elles le
sont. Règles de dessin : `docs/regles-redaction.md`, section 5.

## Ce que fait Dark Reader

Constaté le 28/11/2026 sur la version 4.9.135 (extension et paquet npm `darkreader`, même
code), en lisant ses sources et en l'appliquant aux pages du site.

- **Mode dynamique** (le mode par défaut) : il réécrit les couleurs des feuilles de style
  (fonds assombris, textes éclaircis) et les attributs `fill`, `stroke` et `stop-color` des
  SVG insérés dans la page
  ([inline-style.ts](https://github.com/darkreader/darkreader/blob/main/src/inject/dynamic-theme/inline-style.ts)) :
  - le `fill` d'un `<text>` est traité comme une couleur de texte : éclairci ;
  - le `fill` de toute autre forme dépend de sa taille à l'écran, mesurée une fois la page
    chargée : plus de 32 px de large ou de haut, c'est un fond (assombri) ; sinon une
    couleur de texte (éclaircie). Le `<svg>` lui-même est une forme comme une autre ;
  - un `<tspan>` n'est pas un `<text>` pour lui : il est mesuré comme une forme ;
  - `fill="none"` et `fill="currentColor"` ne sont pas touchés ; `currentColor` suit la
    propriété CSS `color`, que Dark Reader éclaircit comme tout texte ;
  - `stroke` est une couleur de texte, sauf sur `<line>` et `<text>` (couleur de bordure) ;
    `stop-color` est toujours un fond.
- **Dans une feuille de style**, `fill` et `stroke` sont toujours traités comme du texte,
  quelle que soit la forme
  ([modify-css.ts](https://github.com/darkreader/darkreader/blob/main/src/inject/dynamic-theme/modify-css.ts)).
  C'est pourquoi les figures gardent leurs couleurs dans leurs attributs : passées en
  classes CSS, leurs grandes zones claires seraient éclaircies au lieu d'assombries, et le
  texte, éclairci aussi, deviendrait illisible.
- **Sites qui ont leur propre thème sombre** : une balise `<meta name="darkreader-lock">`
  dans `<head>`, écrite dans la page ou ajoutée par JavaScript, lui demande de se retirer
  (il surveille `<head>`)
  ([CONTRIBUTING.md](https://github.com/darkreader/darkreader/blob/main/CONTRIBUTING.md#disabling-dark-reader-on-your-site)).
  Sa détection des thèmes sombres, active par défaut, lit aussi
  `<meta name="color-scheme">`, la propriété `color-scheme: dark` de `<html>` et la clarté
  des fonds ([detector.ts](https://github.com/darkreader/darkreader/blob/main/src/inject/detector.ts)).

## Ce qui n'allait pas

Captures avant et après : `docs/captures/mode-sombre/` (Dark Reader 4.9.135, thème clair).

- Chaque figure avait `fill="#10283a"` sur `<svg>`. Dark Reader l'assombrissait comme un
  fond, et tout texte qui en héritait (la plupart) devenait sombre sur sombre : invisible.
- Les pastilles numérotées (32 unités) étaient éclaircies avec leur chiffre blanc.
- La teinte des zones hachurées, dessinée dans la tuile du motif, échappait à la mesure :
  sur la carte des départements, le territoire de Rouen restait clair, celui de Caen
  devenait sombre.
- Les mots colorés par un `<tspan>` et les textes colorés par leur groupe s'assombrissaient.

## Ce qui a été fait

1. **Un thème sombre du site** (thèmes `light` et `dark` de Quarto dans `_quarto.yml`) :
   `assets/theme-sombre.scss` donne une valeur sombre aux mêmes jetons. Il suit le réglage
   du système (`prefers-color-scheme`) ; le bouton de la barre de navigation permet de
   choisir, et le choix est gardé d'une page à l'autre. `check_contrast.py` vérifie chaque
   paire de `contrast_pairs.yml` dans les deux thèmes.
2. **Quand le thème sombre est actif**, `_includes/theme-sombre.html` ajoute
   `<meta name="darkreader-lock">` (et le thème déclare `color-scheme: dark`) : Dark Reader
   se retire et le lecteur voit le thème du site, dont les contrastes sont vérifiés.
3. **Quand le thème clair est actif** (système clair, ou choix du lecteur) et que Dark
   Reader réécrit la page, les figures restent lisibles : `fill="currentColor"` sur
   `<svg>`, couleur portée par chaque texte, pastilles numérotées à bord seul, motifs
   séparés de leur teinte, cases de légende assez larges. `check_figures.py` le vérifie.
4. Les figures gardent les jetons clairs dans leurs attributs ; le thème sombre donne à
   chaque couleur sa valeur sombre (`$pv-figures-sombre`), y compris pour la carte
   d'accueil et les grilles de fréquences. `check_figures.py` vérifie qu'aucune couleur n'y
   manque.
5. Une page s'imprime toujours dans le thème clair.
6. Le bandeau « Prototype » prend enfin ses couleurs ambre (la règle visait une classe que
   Quarto ne pose pas : `#quarto-announcement`).

## Tester

- Thème sombre : passer le système en sombre, ou cliquer sur le bouton de la barre de
  navigation. Dans Chrome, DevTools > Rendering > « Emulate CSS media feature
  prefers-color-scheme ».
- Dark Reader, système sombre : le site doit afficher son propre thème, et la page contenir
  `<meta name="darkreader-lock">`.
- Dark Reader, système clair (ou bouton sur « clair ») : Dark Reader réécrit la page ; les
  figures doivent rester lisibles.
- Sans l'extension, avec le paquet npm (même moteur), après l'événement `load` de la page
  (avant, il ne traite pas les `fill` des SVG) :
  `DarkReader.enable({brightness: 100, contrast: 100, sepia: 0})`.
- Contrôles : `check_figures.py`, `check_contrast.py`, `npm run test:js`.

## Limites connues

- Dark Reader mesure les formes une fois la page chargée : une figure cachée à ce moment-là
  (onglet fermé, bloc replié) aurait toutes ses formes éclaircies. Aucune figure n'est
  dans un onglet ou un bloc replié aujourd'hui.
- Les modes « Filtre » de Dark Reader inversent toute la page, figures comprises ; seul le
  mode dynamique, par défaut, est traité ici.
- Les cases de légende ne sont pas vérifiées automatiquement.
- Grilles de fréquences sous Dark Reader : il éclaircit toutes les petites formes, si bien
  que la personne « qui a l'effet » (bleu) et celles « qui ne l'ont pas » (gris) ont presque
  la même clarté (1,25:1 contre 4,6:1 dans le thème clair) ; elles restent distinctes par la
  teinte, les anneaux vides par leur forme, et la phrase sous la grille donne les chiffres.
  Dans le thème sombre du site, l'écart est conservé.
- Le HTML du bouton de thème de Quarto est corrigé après chaque rendu
  (`tools/build/theme_postprocess.py`, identifiants en double, bouton sans nom) ; une mise
  à jour de Quarto qui change ce balisage arrête le rendu jusqu'à adaptation du script.
