# Tableaux sur téléphone

Comment les tableaux du site s'affichent sur un petit écran, et ce qu'il faut faire en
écrivant un nouveau tableau. Aucun tableau ne doit faire défiler toute la page de côté, ni
couper des colonnes sans le montrer.

## Ce que fait le site, sans rien écrire de plus

Le filtre `assets/filters/tableaux.lua` place chaque tableau dans une boîte :

```html
<div class="tableau-defile [tableau-cartes | tableau-large]">
  <div class="tableau-defile-cadre"><table>…</table></div>
</div>
```

Selon le tableau, quand sa boîte fait moins de 36rem de large (environ 650 px avec la police
de 18 px du site, davantage si le lecteur agrandit le texte) : sur un téléphone, mais aussi
sur une tablette, où la colonne de texte fait de 500 à 600 px. Un tableau redevient un
tableau à partir d'un écran d'environ 1 100 px.

| Tableau | Dans une boîte étroite |
|---|---|
| Deux colonnes | Le texte passe à la ligne ; un mot trop long pour sa colonne est coupé, à un trait d'union si possible. Le tableau tient dans l'écran. |
| Trois colonnes ou plus | Une carte par ligne (`tableau-cartes`) : la première cellule en titre, chaque autre cellule précédée de l'intitulé de sa colonne. |
| Classe `tableau-large` (grilles des cytochromes) | Les colonnes restent ; la boîte défile de côté, la première colonne et la ligne d'en-tête restent visibles. |

La largeur de la boîte est lue par une requête de conteneur (`@container`) ; un navigateur
qui ne la connaît pas (iOS 15 et avant) passe aux cartes sous 576 px d'écran.

Dans tous les cas, si un tableau est encore plus large que l'écran (une adresse très
longue, par exemple), seule sa boîte défile. `assets/js/tableaux.js` affiche alors un fondu
avec une ombre sur le bord qui cache des colonnes, et fait de la boîte une région nommée,
atteignable au clavier (flèches gauche et droite).

Les cartes gardent la structure du tableau pour les lecteurs d'écran : la ligne d'en-tête
reste dans la page, hors de la vue, et le script rend aux lignes et aux cellules leurs
rôles de tableau, que certains navigateurs perdent quand les cellules s'affichent en blocs.
L'intitulé affiché avant chaque valeur n'est pas relu une seconde fois.

## En écrivant un tableau

- Donnez un en-tête à chaque colonne : c'est lui que la carte affiche. Une première colonne
  sans en-tête (la ligne qu'on décrit) convient, elle devient le titre de la carte.
- La première colonne doit pouvoir servir de titre : le nom du médicament, de
  l'association, du centre.
- Pas de titre (`##`) dans un bloc `:::` autour d'un tableau : il sortirait de la table des
  matières (`check_toc.py`). Utilisez une légende.
- Un tableau généré en HTML brut (`tools/build/`) passe aussi par le filtre. Pour des
  valeurs courtes (des chiffres), la classe `cartes-en-ligne` met l'intitulé et la valeur
  sur une même ligne de la carte (`make_openmedic.py`).
- Une grille qu'il faut lire en colonnes prend la classe `tableau-large`. Si son
  générateur écrit lui-même sa boîte (pour qu'elle soit une région nommée même sans
  JavaScript), le tableau prend aussi `tableau-encadre`, et le filtre le laisse tel quel
  (`make_cytochromes.py`).
- Les liens d'un tableau font au moins 24 px de haut (WCAG 2.2, critère 2.5.8) : la marge
  est dans `theme.scss`, rien à faire.

## Les tableaux du site (relevé du 29/11/2026)

Mesuré avec Playwright dans WebKit et Chromium, à 320, 390, 412, 768, 992 et 1 280 px, en
thème clair et sombre. Captures avant et après : `docs/captures/tableaux/`.

| Page | Tableau | Colonnes | Sur téléphone |
|---|---|---|---|
| bon-usage/cytochromes | Grilles des substrats, inhibiteurs, inducteurs | 9 | Défile dans sa boîte, colonne des médicaments et ligne des enzymes fixes, fondu à droite |
| bon-usage/cytochromes | HUG et FDA comparés | 3 | Cartes |
| bon-usage/cytochromes | Résultat du vérificateur (`cyp-roles`, écrit par le script) | 4 courtes | Tient dans l'écran dès 320 px (inchangé) |
| bon-usage/ecraser-couper | Raison, exemple, source | 3 | Cartes |
| bon-usage/interactions-ville | Les seize associations (avec filtre) | 4 | Cartes ; le filtre masque des cartes |
| bon-usage/interactions | Niveaux du Thésaurus | 3 | Cartes |
| bon-usage/quand-prendre | Moment de prise | 4 | Cartes |
| comprendre/frequences | Mots de la notice | 2 | Passe à la ligne |
| comprendre/lire-un-rcp | Où chercher quoi ? ; catégories de fréquence | 2 | Passe à la ligne |
| comprendre/lire-une-notice | Formules de la notice | 2 | Passe à la ligne |
| crpv/enseignement | Caen et Rouen comparés | 3 | Cartes |
| crpv/partenaires | Structure, rôle | 2 | Passe à la ligne |
| crpv/trouver-mon-crpv | Liste des centres (`make_crpv_page.py`) | 5 | Cartes |
| declarer | Centres de Caen et Rouen | 4 | Cartes |
| medicaments/classes (AINS, anticoagulants, benzodiazépines, opioïdes, statines) | Interactions majeures | 2 | Passe à la ligne |
| medicaments/classes/methotrexate | Interactions selon la dose | 3 | Cartes |
| medicaments/maux-courants/fievre-douleur-enfant | Posologies | 3 | Cartes |
| medicaments/situations/conduite | Pictogrammes de conduite | 4 | Cartes |
| normandie/carte | Départements et centres | 3 | Cartes |
| normandie/en/index | Centres ; vocabulaire | 4 ; 2 | Cartes ; passe à la ligne |
| normandie/medicaments-rembourses | Chiffres en détail (`make_openmedic.py`) | 5 | Cartes, chiffres sur la ligne de leur intitulé |
| normandie/qui-contacter | Situations ; professionnels | 3 ; 2 | Cartes ; passe à la ligne |
| poser-une-question | Centres | 2 | Passe à la ligne |
| vigiking/archives | Numéros (`make_vigiking_page.py`, avec filtre) | 3 | Cartes |

Dans Playwright sous Windows, ni WebKit ni Chromium ne coupent les mots français aux traits
d'union (pas de dictionnaire) : les mots longs des tableaux à deux colonnes y sont coupés
n'importe où. Safari sur iPhone et Chrome sur Android, qui ont ces dictionnaires, devraient
couper aux traits d'union (`hyphens: auto`) ; pas encore vérifié sur un appareil.
