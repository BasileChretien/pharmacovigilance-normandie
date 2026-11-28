# Bulletin Vigiking Normand

Prototype (28/11/2026). Le bulletin s'écrit dans Word (ou en texte) ; sa mise en page, ses
références et ses vérifications se font toutes seules, et donnent deux versions du même
numéro :

- **le PDF** à joindre au courriel, en pages 16:9 pour la lecture à l'écran ;
- **une page web**, lisible sur téléphone, avec un lien vers le PDF.

## En bref, pour les auteurs

1. **Une fois par ordinateur** : double-cliquez sur `Installer.bat`. Il installe Quarto
   (la mise en page) et uv (qui lance les scripts et installe Python), pour l'utilisateur,
   et pose l'icône **Fabriquer le Vigiking** sur le bureau.
2. **Écrivez le numéro dans Word** à partir de `word/modele-vigiking.docx` (styles ci-dessous).
3. **Déposez le fichier Word sur l'icône.** Une à deux minutes plus tard, à côté du fichier
   Word : le PDF (qui s'ouvre), la page web, et `vigiking-AAAA-MM - à vérifier.txt`, la
   liste de ce qui reste à corriger.

Le mode d'emploi illustré est dans `guide/index.html` : un double-clic l'ouvre dans le
navigateur.

## Ce qui se fait tout seul

- Le mois, lu dans le sous-titre du document (« Octobre 2025 »).
- Le sommaire, les numéros et les couleurs des articles, la pagination.
- La taille du texte : chaque article remplit sa page ; les images rétrécissent avec le
  texte ; un article trop long, même en petits caractères, est signalé.
- La couverture : la première image du document, ou à défaut la carte du réseau.
- Le dos avec les coordonnées des deux centres et la carte du réseau.
- Les références : `[PMID 14999113]` ou `[DOI 10.1136/…]` dans le texte devient un appel
  numéroté dans l'ordre de citation, et la référence complète (format Vancouver, trouvée
  sur PubMed ou Crossref) va sur une page « Références » avant le dos. Une source sans
  identifiant s'écrit `[Réf : texte libre]`. Les références trouvées sont gardées dans
  `.cache/`, pour refaire un numéro sans connexion.
- Les vérifications, dans la liste « à vérifier » :
  - couleur mise à la main (perdue) ;
  - image sans texte de remplacement, trop petite, ou dans un format illisible ;
  - nom d'auteur à compléter ;
  - « [à compléter] » oublié ;
  - article trop long ;
  - lien mort ;
  - référence introuvable.

## La mise en page

Même identité que le site (polices Atkinson Hyperlegible Next pour le texte, conçue pour
les lecteurs malvoyants, et Bricolage Grotesque pour les titres ; texte encre sur blanc).
La couverture met le thème du numéro sur le bleu Manche, à côté de la photo ; les logos et
le bandeau Vigiking restent en tête. Chaque article porte un grand numéro et une couleur
tirée de sa place dans le numéro, du bleu au vert du logo des CRPV ; une ligne de points
en haut de page situe l'article dans le numéro (chaque point mène à son article). Le code
des listes de médicaments ne repose pas sur la couleur seule : rouge **et gras** pour une
contre-indication, orange *et italique* pour CredibleMeds. Contrastes vérifiés (WCAG AA)
par `tests/test_bulletin_couleurs.py`.

## Écrire dans Word

Le modèle `word/modele-vigiking.docx` explique chaque style. Ses styles sont les éléments du
bulletin :

| Dans Word | Dans le bulletin |
|---|---|
| « Titre » / « Sous-titre » | le thème du numéro / son mois |
| une image avant le premier article | la couverture |
| « Éditorial », avant le premier article | un encadré sur la page du sommaire |
| « Titre 1 », puis une ligne « Auteur : Initiale. Nom » | un article, sur sa page |
| une ligne « Rubrique : Littérature » sous le titre | la rubrique au-dessus du titre ; le sommaire regroupe les articles par rubrique |
| une ligne « Relecture : Initiale. Nom » | le relecteur, après l'auteur |
| « Titre 2 » | un intertitre dans l'article (plusieurs brèves sous un même titre) |
| un paragraphe « [saut de colonne] » | deux colonnes, coupées à cet endroit |
| « Encadré » | un encadré |
| « Bloc Cas clinique », « Bloc À retenir », « Bloc En pratique », « Bloc Le saviez-vous ? », « Bloc Mécanisme », « Bloc Attention », « Bloc Pour les patients », « Bloc Pour les pharmaciens », « Bloc Pour les prescripteurs », « Bloc Annonce » | un bloc titré dans sa couleur (voir plus bas) |
| « Chiffre clé » (un paragraphe par chiffre) | une rangée de tuiles : le nombre en grand, puis ce qu'il compte |
| un tableau (Insertion › Tableau), avec une ligne d'en-tête | un tableau à en-tête bleu, une ligne sur deux teintée |
| « Source » | la source officielle de l'article, en petits caractères |
| « Intertitre en ligne » (caractères) | quelques mots en couleur qui ouvrent un paragraphe |
| « Catégorie rouge » (verte, bleue, jaune) | une étiquette de catégorie ; l'article devient une liste |
| « Contre-indication », « CredibleMeds » (caractères) | rouge et gras / orange et italique |
| « Légende », « Références » | petits caractères |
| image, puis paragraphe « Légende de figure » | une figure et sa légende |
| clic droit sur l'image → Modifier le texte de remplacement | le texte lu par les lecteurs d'écran |

Les couleurs se mettent par ces styles : une couleur appliquée à la main se perd (la liste
« à vérifier » le signale).

### Les types de blocs, et en créer un

Les dix types du modèle viennent d'un relevé des 25 numéros parus de 2017 à 2025 (cas
cliniques, messages à retenir, conduites à tenir, encadrés « Le saviez-vous ? », conseils par
public, annonces…). Chacun est un style de paragraphe dont le nom commence par « Bloc » ;
sa couleur de police dans Word devient la couleur du bloc.

Un auteur crée son propre type de la même façon : dans Word, volet Styles, « Nouveau
style », nom « Bloc » suivi du titre (par exemple « Bloc Interaction »), type Paragraphe,
basé sur Normal, avec la couleur de police de son choix. Le bulletin en fait un bloc titré
« Interaction » dans cette couleur, assombrie si besoin pour que le titre reste lisible
(contraste WCAG AA) ; sans couleur, le bloc prend celle de l'article. La liste à vérifier ne
signale jamais un style « Bloc … ». Pour qu'un nouveau type serve à tous, ajoutez-le à
`BLOCS` dans `word/faire_modele.py` et à `word/modele.md`, puis refaites le modèle.

## Écrire en texte

Un numéro est aussi un fichier texte `numeros/AAAA-MM/vigiking-AAAA-MM.qmd` (voir
`exemple/exemple.qmd`), avec ses images dans `numeros/AAAA-MM/images/` :

| Ce qu'on écrit | Ce que ça donne |
|---|---|
| `## Titre {auteur="Initiale. Nom"}` | un article sur sa page ; la taille du texte remplit la page |
| `## Titre {auteur="…" rubrique="Littérature" relecture="…"}` | sa rubrique au-dessus du titre, et le relecteur |
| `## Titre {auteur="…" taille=14}` | la taille du texte fixée à la main |
| `### Intertitre` | un intertitre dans l'article |
| `::: {.editorial}` avant le premier article | l'éditorial, sur la page du sommaire |
| `::: {.bloc titre="Cas clinique" couleur="#0d4a5e"}` | un bloc titré (couleur facultative) |
| `::: {.chiffres}` (un paragraphe par chiffre : `66 % des cas…`) | des tuiles de chiffres clés |
| `::: {.source}` | la source officielle de l'article |
| `[En pratique]{.intertitre}` | un intertitre en ligne |
| `::: {.saut-colonne}` | l'article passe sur deux colonnes, coupées à cet endroit |
| `::: {.encadre}` | un encadré |
| `::: {.pastille couleur=rouge}` | une étiquette de catégorie (rouge, vert, bleu, jaune) |
| `[texte]{.ci}` / `[texte]{.cm}` | contre-indiqué (rouge, gras) / CredibleMeds (orange, italique) |
| `::: {.legende}`, `::: {.references}` | légende, références en petits caractères |
| `## Titre {.dos}` | le dos, ses `###` en intertitres |
| `![Légende](images/x.png){fig-alt="…"}` | une figure, avec son texte pour les lecteurs d'écran |

## Commandes

Depuis la racine du dépôt :

```
uv run python bulletin/fabriquer.py numero.docx         # tout : import, références, PDF, page web, vérifications
uv run python bulletin/fabriquer.py bulletin/numeros/AAAA-MM/vigiking-AAAA-MM.qmd
uv run python bulletin/word/importer.py numero.docx AAAA-MM   # l'import seul
uv run python bulletin/word/faire_modele.py               # refaire le modèle Word (source : word/modele.md)
uv run python tools/design/make_bulletin_reseau.py        # refaire la carte du réseau
```

Options de `fabriquer.py` : `--mois AAAA-MM` (si le sous-titre ne le donne pas),
`--sans-liens` (pas de vérification des liens), `--sans-ouvrir`. Depuis `bulletin/`,
`quarto render numeros/AAAA-MM/vigiking-AAAA-MM.qmd` fait le PDF et la page web seuls, dans
`_output/numeros/AAAA-MM/`.

## Fichiers

- `fabriquer.py`, `Fabriquer le Vigiking.bat`, `Installer.bat` + `installer.ps1` : la
  fabrication en une étape et l'installation.
- `word/` : le modèle Word, l'import (`importer.py`, `word-vers-vigiking.lua`), les
  références (`references.py`) et les vérifications (`verifier.py`).
- `_extensions/vigiking/` : la mise en page (`typst-template.typ` pour le PDF, `vigiking.css`
  pour le web, `vigiking.lua` commun), les polices (`fonts/`, licence OFL) et la carte
  (`reseau.svg`, `reseau.typ`, générés).
- `guide/` : le mode d'emploi illustré pour les auteurs. Il se modifie dans `source.html`,
  puis `uv run python bulletin/guide/construire.py` écrit `index.html` (qui reprend les polices
  de `_extensions/vigiking/fonts/`) ; `--en-ligne DOSSIER` écrit la version publiée en ligne.
  Images : pages de `exemple/exemple.qmd` et d'un numéro d'essai fait depuis Word (pages des
  références et du dos).
- `commun/` (local, hors du dépôt) : logos, bandeau et dos repris dans chaque numéro.

## À décider avant d'aller plus loin

- **Les numéros restent hors du dépôt public** (`numeros/` est ignoré par git) tant que les
  CRPV n'ont pas donné leur accord pour les héberger sur le site.
- **Noms des auteurs** : affichés seulement avec leur accord écrit ; le prototype met
  « [auteur] ».
- **Figures** : celles tirées d'articles ou de banques d'images demandent leur source et un
  droit de reproduction.
- **Installation sur les postes des CHU** : `Installer.bat` passe par winget, pour
  l'utilisateur ; à essayer sur un poste hospitalier, où les installations peuvent être
  bloquées.
