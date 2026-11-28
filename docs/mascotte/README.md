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

Sur toutes les pages (décision du 28/11/2026, pages sérieuses comprises, avec une animation
plus douce ; l'animation se joue à chaque ouverture de page). Une variante par contexte, dans
`assets/img/mascotte/`, écrite par `tools/design/make_mascotte.py` à partir du dessin
`assets/img/mascotte.svg` (on modifie le dessin ou le script, puis on le relance ; on ne
modifie pas les variantes). Même personnage, une pose et une courte animation propres à
chaque endroit.

Dans le bandeau de titre de chaque page, à droite du titre : la variante de la rubrique,
donnée par la clé `mascotte:` du `_metadata.yml` de son dossier, ou de l'en-tête de la page
pour une page qui fait exception. Le filtre `assets/filters/mascotte.lua` en fait une image
que `_includes/title-block.html` (le bandeau de Quarto, une ligne ajoutée) place à côté du
titre. Une page qui montre déjà la mascotte dans son corps (accueil, 404, Vigiking, liste des
publications vide) n'en a pas dans son bandeau.

| Contexte | Où | Pose (aussi sans animation) | Animation |
|---|---|---|---|
| `accueil` | accueil, à côté de « Déclarer », tournée vers lui ; page Déclarer | cor aux lèvres, trois ondes | il lève le cor et sonne l'alerte, trois fois |
| `vigiking` | rubrique Vigiking | cor aux lèvres, trois ondes | un petit saut, puis le cor annonce le numéro |
| `404` | page introuvable | cor écarté, bouche en « o », point d'interrogation | il regarde à gauche, à droite, la tête penchée ; le « ? » surgit |
| `recherche` | recherche du site sans résultat ; Chercher un médicament | cor écarté, bouche « hmm » | il cherche des yeux, la tête penchée |
| `attente` | liste des publications pas encore remplie | cor écarté, sourire, trois points | les points s'allument l'un après l'autre ; il respire, cligne des yeux |
| `comprendre` | rubrique Comprendre | sourire, ampoule allumée | il réfléchit, tête penchée ; l'ampoule surgit et rayonne ; il hoche la tête |
| `bon-usage` | rubrique Bon usage | sourire, coche verte | la coche se trace ; il hoche la tête |
| `normandie` | rubrique En Normandie | sourire, deux vagues de la Manche sous les pieds | il tangue comme sur un drakkar, la mer ondule |
| `crpv` | rubrique Les CRPV | sourire | il salue avec son cor, deux fois |
| `question` | Poser une question | sourire, point d'interrogation | tête penchée, le « ? » surgit |
| `actualites` (douce) | rubrique Actualités, alertes officielles comprises | cor aux lèvres, trois ondes | il lève le cor, qui sonne une seule fois |
| `medicaments` (douce) | rubrique Médicaments : fiches, maux courants, situations | sourire | il lève un peu son bouclier-comprimé, hoche la tête, cligne des yeux |
| `sobre` (douce) | Cas marquants, Vous pensez avoir un effet indésirable ?, À propos | bouche calme, sans sourire | une respiration, un clignement |

- Pages sur des risques, des doses ou des effets graves (`medicaments/`, `actualites/`, cas
  marquants, que faire en cas d'effet indésirable) : seulement une variante douce
  (`DOUX` du script) : clignement, respiration, hochement, regard, bouclier levé, cor qui
  sonne une fois. Ni saut, ni tangage, rien qui surgit.
- Les ondes du cor ne sortent que là où il annonce quelque chose (accueil, Vigiking, Actualités).
- Chaque animation se joue une fois et s'arrête d'elle-même en 5 secondes au plus : une image
  ne peut pas être mise en pause depuis la page, et au-delà de 5 secondes il faudrait un bouton
  pause (WCAG 2.2.2). Aucune ne se joue si le lecteur a demandé moins d'animations
  (`prefers-reduced-motion`) : il voit la pose. Sur l'accueil, la mascotte bascule aussi quand
  on survole ou qu'on atteint le bouton « Déclarer » au clavier, sous la même condition.
- Toujours décorative (`alt=""` et `aria-hidden`), cachée à l'impression.
- Fixé par les tests : les pages, la variante de chaque rubrique et les variantes douces par
  `tests/test_mascotte.py` ; le bandeau par `tests/test_mascotte_bandeau.py` ; les règles des
  variantes (jetons, durée, mouvement réduit, ondes, douceur) par
  `tests/test_mascotte_animations.py`.
- Nouvelle rubrique : lui donner un `_metadata.yml` avec sa clé `mascotte:` (le test le
  demande), d'une variante qu'aucune autre rubrique n'a.
- Bulletin Vigiking (PDF) : la mascotte, fixe, à gauche du bandeau « VIGIKING NORMAND » de la
  couverture, tournée vers lui (branche du bulletin, `tools/design/make_bulletin_mascotte.py`).

## Ce qui existait déjà (Vigiking)

- Bandeau des numéros : le mot « VIGIKING NORMAND », capitales arrondies en bleu, le G remplacé
  par un petit signe ; en 2017, « VIGIKING » en capitales à empattements. Ni personnage, ni
  casque, ni cornes.
- Logo du CRPV de Rouen : un drakkar bordé de boucliers ronds, en bleu marine. Le bouclier
  rond de la mascotte s'y accorde.
- Modèle Word du bulletin (`modele-vigiking.docx`) : styles et couleurs seulement, aucune image.
