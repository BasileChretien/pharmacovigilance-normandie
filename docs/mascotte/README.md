# Mascotte : esquisses

Trois esquisses d'une mascotte pour le site, à choisir avant toute intégration. Rien ici n'est
publié : Quarto ne rend pas `docs/` (`_quarto.yml`). Aperçu : ouvrir `apercu.html` dans un
navigateur ; captures dans `captures/`.

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

1. `mascotte-cor.svg` : il sonne du cor, trois ondes en sortent (comme les pulsations de la
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

## Où la placer (après choix)

- Oui : accueil (petite, à côté de l'appel « Déclarer »), archives et bandeau de Vigiking,
  page 404, états vides (aucun résultat de recherche, publications pas encore disponibles).
- Jamais : fiches médicament, fiches de classe, pages grossesse, alertes de sécurité, pages
  sur des effets graves.
- Décorative (`aria-hidden` ou `alt=""`) ; tout mouvement soumis à
  `prefers-reduced-motion`.

## Ce qui existait déjà (Vigiking)

- Bandeau des numéros : le mot « VIGIKING NORMAND », capitales arrondies en bleu, le G remplacé
  par un petit signe ; en 2017, « VIGIKING » en capitales à empattements. Ni personnage, ni
  casque, ni cornes.
- Logo du CRPV de Rouen : un drakkar bordé de boucliers ronds, en bleu marine. Le bouclier
  rond de la mascotte s'y accorde.
- Modèle Word du bulletin (`modele-vigiking.docx`) : styles et couleurs seulement, aucune image.
