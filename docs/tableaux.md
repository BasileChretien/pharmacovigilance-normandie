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

Selon le tableau, sur un écran de moins de 576 px :

| Tableau | Sur téléphone |
|---|---|
| Deux colonnes | Le texte passe à la ligne ; le tableau tient dans l'écran. |
| Trois colonnes ou plus | Une carte par ligne (`tableau-cartes`) : la première cellule en titre, chaque autre cellule précédée de l'intitulé de sa colonne. |
| Classe `tableau-large` (grilles des cytochromes) | Les colonnes restent ; la boîte défile de côté, la première colonne et la ligne d'en-tête restent visibles. |

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
