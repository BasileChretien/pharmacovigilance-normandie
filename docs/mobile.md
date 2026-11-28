# Mise en page sur téléphone

Le site se lit surtout sur téléphone. Un audit de toutes les pages (novembre 2026) a trouvé
un menu ouvert hors de l'écran, le bouton de recherche coupé à 320 px, 40 pages qui
défilaient de côté, des tableaux coupés, un en-tête trop haut et de petites cibles
tactiles. `npm run check:mobile` (`tools/checks/check_mobile.mjs`) mesure ces défauts sur
chaque page à chaque pull request, pour qu'ils ne reviennent pas.

## Règles

Toute modification de la mise en page (CSS, gabarit, composant, tableau, figure) est
vérifiée à 320 et à 390 px avec `npm run check:mobile`, après `quarto render`.

- **Rien ne dépasse de l'écran.** Pas de largeur fixe au-delà de 288 px (un écran de 320 px
  moins les marges) : `max-width: 100%`. Dans une boîte `flex`, un élément qui contient du
  texte reçoit `min-width: 0`, et les mots longs (adresses, noms de molécules) se coupent
  (`overflow-wrap: anywhere`).
- **Les pseudo-éléments comptent.** Une étiquette en `::after` dans un titre `flex` pousse
  la page de côté quand le titre est long : permettre le retour à la ligne
  (`flex-wrap: wrap`) ou passer l'étiquette sous le titre en dessous de 576 px.
- **Un tableau large défile dans sa propre boîte** (`main table` sous 768 px dans
  `assets/theme.scss`), jamais dans la page ; ne pas le couper par un `overflow: hidden`.
- **Les éléments fixes ne défilent pas** : un bouton de l'en-tête qui sort de l'écran est
  perdu, même si la page, elle, ne défile pas.
- **L'en-tête fixe, bandeau compris, couvre 20 % au plus** d'un premier écran de
  390×844 px.
- **Le menu ouvert tient dans l'écran** : chaque lien visible, ou atteint en faisant défiler
  le menu, et touchable.
- **Cibles tactiles de 24×24 px au moins** (WCAG 2.5.8), 44 px de préférence, sauf un lien
  dans une phrase. Un bouton radio dans son `<label>` se touche par le libellé entier.
  L'exception d'espacement du WCAG n'est pas retenue : une cible trop petite s'agrandit.
- **Texte de 12 px au moins.** Le texte des figures : 12 px au moins à partir de 375 px
  (`docs/regles-redaction.md` §5) ; à 320 px il rétrécit avec la figure.

## Ce que mesure le contrôle

Chaque page de `_site/` est servie en HTTP sous `/pharmacovigilance-normandie/`, comme sur
GitHub Pages, puis ouverte dans six profils : WebKit iPhone SE (320×568) et iPhone 13
(390×844), Chromium Pixel 7 (412×839), chacun en thème clair et en thème sombre, sans
animation (`prefers-reduced-motion`). Le contrôle échoue (code de sortie 1) quand :

| Règle (`regle`) | Échoue quand |
|---|---|
| `defilement` | la page défile de côté (`scrollWidth` > `clientWidth`) ; la cause est nommée : boîte trop large, contenu plus large que sa boîte (pseudo-élément ou mot sans coupure), sinon l'élément dont le retrait supprime le défilement |
| `hors-ecran` | un élément visible sort de l'écran à gauche ou à droite sans ancêtre qui le coupe ou le fait défiler (éléments fixes compris) |
| `coupe` | une boîte en `overflow-x: hidden` ou `clip` coupe du texte sur un côté : le lecteur ne peut pas défiler jusqu'à lui (un `text-overflow: ellipsis` est un choix, pas une coupure) |
| `entete` | à 390×844, les bandes fixes du haut couvrent plus de 20 % de l'écran |
| `menu` | après un toucher sur `.navbar-toggler`, un lien du menu reste hors de l'écran, est caché par un autre élément ou fait moins de 24×24 px |
| `chevauchement` | deux textes se recouvrent (le contenu d'un `<details>` fermé est ignoré) |
| `cible-tactile` | une cible fait moins de 24×24 px, hors lien dans une phrase |
| `texte-petit` | un texte fait moins de 12 px |

Le rapport regroupe les constats par règle et par élément, avec les profils, les pages et
les tailles. Une capture de l'écran (pas de la page entière : WebKit refuse les images de
plus de 32 767 px) est enregistrée pour chaque page en échec dans `_captures-mobile/`,
élément entouré en rose ; la CI la joint au run (artefact `captures-mobile`).

En local : `npm install --no-save playwright`, `npx playwright install webkit chromium`,
puis par exemple `npm run check:mobile -- bon-usage/ecraser-couper.html --profils iphone-se`.
Les tests : `tests/js/check-mobile.test.mjs` (calculs, rapport, serveur) et
`tests/js/check-mobile-browser.test.mjs` (mesures sur de petites pages, dans les deux
moteurs).

## Exceptions

Une exception ne s'écrit que pour un écart voulu, jamais pour faire passer la CI.
Elle va dans `tools/checks/mobile_allowlist.json` avec sa raison :

```json
{ "regle": "cible-tactile", "selecteur": ".carte h3 a", "pages": ["normandie/*.html"],
  "profils": ["iphone-se"], "raison": "Le lien couvre la carte entière par son ::after." }
```

`selecteur` est un sélecteur CSS (l'élément ou un de ses ancêtres) ; `pages` (motifs,
`*` dans un dossier, `**` partout) et `profils` (`iphone-se`, `iphone-13`, `pixel-7`, avec
`-clair` ou `-sombre` au besoin) sont facultatifs. Une exception qui ne sert plus est
signalée à la fin du rapport : la retirer.

## Ce que le contrôle ne voit pas

- Les défauts purement visuels : espacements serrés, alignements, coupures de ligne
  malheureuses, hiérarchie confuse, image floue ou trop petite.
- Un texte recouvert par une image, une icône ou un fond (seuls les textes entre eux sont
  comparés) ; un contenu coupé par un `overflow: hidden` voulu.
- Les états qu'il n'ouvre pas : recherche, `<details>` ouverts, onglets, info-bulles,
  orientation paysage, texte agrandi par le lecteur (zoom 200 %).
- Les vrais navigateurs : barre d'outils de Safari (le premier écran de l'iPhone 13 y fait
  plutôt 664 px de haut), encoche, clavier ouvert.

Un passage à la main sur un vrai téléphone reste nécessaire avant une mise en ligne.
