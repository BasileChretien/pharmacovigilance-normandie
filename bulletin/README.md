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
| `## Titre {auteur="Initiale. Nom"}` | un article sur sa page, en deux colonnes |
| `## Titre {auteur="…" .une-colonne}` | une colonne ; la taille du texte remplit la page |
| `## Titre {auteur="…" taille=14}` | la taille du texte fixée à la main |
| `## Titre {auteur="…" .liste}` | texte aligné à gauche (listes de médicaments) |
| `::: {.saut-colonne}` | le passage à la deuxième colonne |
| `::: {.encadre}` | un encadré bleu |
| `::: {.pastille couleur=rouge}` | une étiquette de catégorie (rouge, vert, bleu, jaune) |
| `[texte]{.ci}` / `[texte]{.cm}` | contre-indiqué (rouge, gras) / CredibleMeds (orange, italique) |
| `::: {.legende}`, `::: {.references}` | légende, références en petits caractères |
| `## Titre {.dos}` | le dos, ses `###` en bandeaux bleus |
| `![Légende](images/x.png){fig-alt="…"}` | une figure, avec son texte pour les lecteurs d'écran |

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
- Une colonne remplit la page toute seule ; deux colonnes non (Typst n'équilibre pas les
  colonnes) : placer le saut de colonne et, si besoin, `taille=`.
