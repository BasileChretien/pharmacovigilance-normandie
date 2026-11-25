# Pharmacovigilance Normandie — prototype

Prototype non officiel du site d'information des centres régionaux de pharmacovigilance
(CRPV) de Caen et de Rouen, construit d'après le plan « Projet de site web
Pharmacovigilance Normandie ». Tous les contenus sont des brouillons à relire par un
pharmacologue avant toute mise en ligne. Le site demande aux moteurs de recherche de ne pas
l'indexer.

Les logos de `assets/img/logos/` (CRPV Normandie Caen, CHU de Caen Normandie, CHU de Rouen
Normandie) ont été repris des sites des CHU le 25/11/2026. Ils doivent être validés, et si
possible remplacés par les fichiers officiels, par les directions de la communication avant
toute mise en ligne.

## Construire et prévisualiser

Prérequis : [Quarto](https://quarto.org) 1.5 ou plus, [uv](https://docs.astral.sh/uv/)
pour les contrôles Python, Node.js pour les contrôles HTML.

```bash
quarto preview            # prévisualisation avec rechargement automatique
quarto render             # site complet dans _site/
```

## Contrôles automatiques

```bash
uv run pytest                                   # tests des contrôles
uv run python tools/checks/check_content.py     # règles de rédaction et en-têtes
uv run python tools/checks/check_contrast.py    # contrastes des couleurs (WCAG AA)
npm install && npm run check:html               # validité du HTML rendu
```

- `check_content.py` lit les règles de `docs/regles-redaction.md` : en-tête complet,
  sources, dates de relecture ; dans les blocs `.texte-patient`, longueur des phrases,
  pourcentages, termes médicaux non expliqués (`data/jargon.yml`), sigles, encadrés
  « À retenir » et « Quand consulter », phrase « Ne modifiez pas votre traitement… »,
  indice de lisibilité. Sur un brouillon, ces règles donnent des avertissements ; sur une
  page relue ou publiée, les règles bloquantes donnent des erreurs. `--strict` montre ce
  qui bloquerait la publication d'un brouillon.
- `check_contrast.py` vérifie chaque paire texte/fond déclarée dans
  `tools/checks/contrast_pairs.yml` à partir des couleurs de `assets/theme.scss`.
- L'accessibilité des pages rendues se vérifie aussi avec axe-core (voir
  `.github/workflows/ci.yml`). Les outils automatiques ne remplacent pas un audit RGAA.

## Organisation

| Dossier | Contenu |
|---|---|
| `medicaments/` | fiches par classe, maux courants, situations particulières |
| `bon-usage/` | quand prendre, écraser ou couper, interactions, cytochromes |
| `comprendre/` | notice, RCP, fréquences (grilles interactives), triangle noir… |
| `vigiking/`, `actualites/` | bulletin et actualités (listes automatiques) |
| `normandie/` | qui contacter, carte, chiffres, décryptages, page en anglais |
| `crpv/` | missions, équipes, accès et contacts |
| `a-propos/` | politique éditoriale, mentions légales, accessibilité |
| `_templates/` | gabarits de fiche (non publiés) |
| `assets/` | thème, filtre Lua des encadrés et des sources, scripts, images |
| `tools/checks/`, `tests/` | contrôles automatiques et leurs tests |

## À faire avant une mise en ligne

Voir la liste des décisions du plan : accord des deux CRPV, hébergement et nom de
domaine, relecture de chaque page, audit RGAA, consentement des membres des équipes,
outil d'envoi de Vigiking validé par les DPO, branchement du fil des alertes officielles.
