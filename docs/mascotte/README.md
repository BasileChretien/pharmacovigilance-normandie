# Mascotte

Le Normand au bouclier-comprimé qui sonne du cor : `assets/img/mascotte.svg`, choisi le
28/11/2026 parmi trois esquisses. Les deux autres restent ici pour mémoire (`docs/` n'est pas
publié). Aperçu des trois : ouvrir `apercu.html` dans un navigateur ; captures dans
`captures/`.

À faire approuver par les équipes des CRPV et les services communication des CHU avant la mise
en ligne, comme les logos.

## Le personnage

- Un Normand, pas un Viking de bande dessinée : casque arrondi à nasal, comme ceux de la
  Tapisserie de Bayeux, sans cornes (les casques à cornes sont une invention du XIXe siècle).
  Rien n'est repris des Vikings connus (Hägar, Vicky, Dragons, les Normands d'Astérix).
- Le bouclier rond est un comprimé sécable vu de dessus : la barre de sécabilité devient le
  joint des planches, l'umbo est au centre, l'épaisseur du comprimé se voit en bas.
- Clins d'œil à la broderie de Bayeux : visage laissé « en lin » (blanc), fils couchés sur la
  tunique et la barbe, bordure brodée en bas de la tunique, bandes croisées sur les jambes.
- Couleurs : seulement les jetons de `assets/theme.scss`. Traits en `pv-ink` ; `pv-or`,
  `pv-cyan` et `pv-eau` en décor seulement. Pas de texte dans le dessin.

## Les trois variantes

1. Le cor, retenu (`assets/img/mascotte.svg`) : il sonne du cor, trois ondes en sortent (comme les pulsations de la
   carte d'accueil). Dit « la pharmacovigilance veille et donne l'alerte ».
2. `mascotte-plume.svg` : il lève une plume d'oie. Dit « déclarez un effet indésirable ».
3. `mascotte-fiole.svg` : il salue avec une longue fiole tenue comme une épée (bouchon en
   pommeau, col en garde, graduations sur la lame). Dit « le médicament, avec mesure ».

## Thème sombre et Dark Reader : pourquoi pas la méthode des figures

Les figures (`docs/mode-sombre.md`) sont insérées dans la page et le thème sombre inverse
leurs couleurs claires ; Dark Reader en fait autant. Sur un personnage, le visage blanc devient
sombre avec des yeux clairs, ce qui peut se lire comme une caricature. La mascotte garde donc
ses couleurs partout :

- placée en `<img>` (avec `alt=""`, décorative), elle n'est touchée ni par le thème sombre ni
  par Dark Reader, qui ne réécrit pas le contenu d'une image ;
- un liseré blanc (la silhouette tracée large en blanc, derrière) la détache d'un fond sombre ;
  sur la page claire, il ne se voit pas.

Vérifié le 28/11/2026 : thème clair, bandeau `pv-mist`, thème sombre du site, et Dark Reader
4.9.135 (paquet npm, mode dynamique) sur le thème clair (`captures/apercu-dark-reader.jpg`).
Les SVG passent aussi les règles de `tools/checks/check_figures.py` (taille, jetons, police,
`id`).

## Où elle est, et ce qu'elle y fait

Une variante par contexte, dans `assets/img/mascotte/`, écrite par
`tools/design/make_mascotte.py` à partir du dessin `assets/img/mascotte.svg` (on modifie le
dessin ou le script, puis on le relance ; on ne modifie pas les variantes). Même personnage,
une pose et une courte animation propres à chaque endroit :

| Contexte | Page | Pose (aussi sans animation) | Animation |
|---|---|---|---|
| `accueil` | accueil, à côté de « Déclarer », tournée vers lui | cor aux lèvres, trois ondes | il lève le cor et sonne l'alerte, trois fois |
| `vigiking` | page du bulletin et anciens numéros | cor aux lèvres, trois ondes | un petit saut, puis le cor annonce le numéro |
| `404` | page introuvable | cor écarté, bouche en « o », point d'interrogation | il regarde à gauche, à droite, la tête penchée ; le « ? » surgit |
| `recherche` | recherche du site sans résultat | cor écarté, bouche « hmm » | il cherche des yeux, la tête penchée |
| `attente` | liste des publications pas encore remplie | cor écarté, sourire, trois points | les points s'allument l'un après l'autre ; il respire, cligne des yeux |

- Les ondes du cor ne sortent que là où il annonce quelque chose (accueil, Vigiking).
- Chaque animation se joue une fois et s'arrête d'elle-même en 5 secondes au plus : une image
  ne peut pas être mise en pause depuis la page, et au-delà de 5 secondes il faudrait un bouton
  pause (WCAG 2.2.2). Aucune ne se joue si le lecteur a demandé moins d'animations
  (`prefers-reduced-motion`) : il voit la pose. Sur l'accueil, la mascotte bascule aussi quand
  on survole ou qu'on atteint le bouton « Déclarer » au clavier, sous la même condition.
- Jamais : fiches médicament, fiches de classe, pages grossesse, alertes de sécurité, pages
  sur des effets graves. Sur ces pages (`medicaments/`, `actualites/`, cas marquants, que
  faire en cas d'effet indésirable), même la recherche sans résultat reste sans mascotte.
- Toujours décorative (`alt=""` et `aria-hidden`), cachée à l'impression.
- La liste des pages et la variante de chacune sont fixées par `tests/test_mascotte.py` ; les
  règles des variantes (jetons, durée, mouvement réduit, ondes) par
  `tests/test_mascotte_animations.py`.
- Bulletin Vigiking (PDF) : la mascotte, fixe, à gauche du bandeau « VIGIKING NORMAND » de la
  couverture, tournée vers lui (branche du bulletin, `tools/design/make_bulletin_mascotte.py`).

## Ce qui existait déjà (Vigiking)

- Bandeau des numéros : le mot « VIGIKING NORMAND », capitales arrondies en bleu, le G remplacé
  par un petit signe ; en 2017, « VIGIKING » en capitales à empattements. Ni personnage, ni
  casque, ni cornes.
- Logo du CRPV de Rouen : un drakkar bordé de boucliers ronds, en bleu marine. Le bouclier
  rond de la mascotte s'y accorde.
- Modèle Word du bulletin (`modele-vigiking.docx`) : styles et couleurs seulement, aucune image.
