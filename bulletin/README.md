# Bulletin Vigiking Normand

Prototype (28/11/2026) : le bulletin s'écrit en texte, et sa mise en page sort toute seule du
modèle, en deux versions tirées du même fichier :

- **le PDF** à joindre au courriel, en pages 16:9 comme la version PowerPoint ;
- **une page web**, lisible sur téléphone, avec un lien vers le PDF.

Le modèle reprend la mise en page habituelle : logos, bandeau Vigiking, titres bleus, texte
justifié sur deux colonnes, encadrés, sommaire cliquable, dos avec les coordonnées des
centres. Deux corrections : le code rouge/orange des listes de médicaments a aussi le gras
et l'italique (pas la couleur seule), et l'orange est assez foncé pour être lu.

## Écrire un numéro

Un numéro est un fichier texte `numeros/AAAA-MM/vigiking-AAAA-MM.qmd` (voir
`exemple/exemple.qmd`), avec ses images dans `numeros/AAAA-MM/images/` :

| Ce qu'on écrit | Ce que ça donne |
|---|---|
| `## Titre {auteur="Initiale. Nom"}` | un article sur sa page ; la taille du texte remplit la page |
| `## Titre {auteur="…" taille=14}` | la taille du texte fixée à la main |
| `## Titre {auteur="…" .liste}` | texte aligné à gauche (listes de médicaments) |
| `::: {.saut-colonne}` | l'article passe sur deux colonnes, coupées à cet endroit |
| `::: {.encadre}` | un encadré bleu |
| `::: {.pastille couleur=rouge}` | une étiquette de catégorie (rouge, vert, bleu, jaune) |
| `[texte]{.ci}` / `[texte]{.cm}` | contre-indiqué (rouge, gras) / CredibleMeds (orange, italique) |
| `::: {.legende}`, `::: {.references}` | légende, références en petits caractères |
| `## Titre {.dos}` | le dos, ses `###` en bandeaux bleus |
| `![Légende](images/x.png){fig-alt="…"}` | une figure, avec son texte pour les lecteurs d'écran |

## Écrire dans Word

Les auteurs peuvent garder Word : ils partent du modèle `word/modele-vigiking.docx`, dont les
styles sont les éléments du bulletin (« Titre 1 » pour chaque article, puis une ligne
« Auteur : … » ; styles « Encadré », « Catégorie rouge » (verte, bleue, jaune), « Légende »,
« Références » ; « Contre-indication » et « CredibleMeds » pour les médicaments ; un
paragraphe « [saut de colonne] » pour deux colonnes ; une image avant le premier article
pour la couverture). Les couleurs se mettent par ces styles : une couleur appliquée à la main
se perd. Puis, depuis la racine du dépôt :

```
uv run python bulletin/word/importer.py numero.docx AAAA-MM
```

Le fichier texte et ses images sont écrits dans `numeros/AAAA-MM/`. Les logos, le bandeau et
le dos du bulletin sont repris de `commun/` (`logo-rouen.png`, `logo-caen.png`,
`bandeau.png`, `dos.md`), dossier local lui aussi. Le modèle se refait avec
`uv run python bulletin/word/faire_modele.py` (source : `word/modele.md`).

## Produire le PDF et la page web

Depuis ce dossier :

```
quarto render numeros/AAAA-MM/vigiking-AAAA-MM.qmd
```

Les fichiers sont dans `_output/numeros/AAAA-MM/`. Polices : Calibri (Windows), sinon
Carlito, libre et de mêmes dimensions.

## À décider avant d'aller plus loin

- **Les numéros restent hors du dépôt public** (`numeros/` est ignoré par git) tant que les
  CRPV n'ont pas donné leur accord pour les héberger sur le site.
- **Noms des auteurs** : affichés seulement avec leur accord écrit ; le prototype met
  « [auteur] ».
- **Figures** : celles tirées d'articles ou de banques d'images demandent leur source et un
  droit de reproduction.
