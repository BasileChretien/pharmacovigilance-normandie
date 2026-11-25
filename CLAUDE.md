# pharmacovigilance-normandie

Quarto website prototype for the regional pharmacovigilance centres (CRPV) of Caen and
Rouen. Content is in French; every medical page is a draft until a named pharmacologist
reviews it.

## Commands

- `quarto preview` / `quarto render` — build the site into `_site/`.
- `uv run pytest` — tests of the checks.
- `uv run python tools/checks/check_content.py [--strict] [files]` — writing and front-matter rules.
- `uv run python tools/checks/check_contrast.py` — WCAG contrast of the colour tokens.
- `npm run check:html` — validate rendered HTML (after `quarto render`).

- `uv run python tools/build/make_cyp_index.py` — regenerate the per-drug index of the cytochrome table.

Status and open tasks: `docs/STATUS.md`. Points for medical reviewers: `docs/relecture.md`.

## Conventions

- Writing rules and front-matter schema: `docs/regles-redaction.md`. Templates: `_templates/`.
- Patient text goes in `::: {.texte-patient}`, professional text in `::: {.texte-pro}`;
  boxes are `::: {.a-retenir}` (3 points max) and `::: {.quand-consulter}`.
- Never write sources, review dates or the draft banner by hand: `assets/filters/page-meta.lua`
  builds them from the front matter.
- Colours live only in `assets/theme.scss`; add every new text/background pair to
  `tools/checks/contrast_pairs.yml`. `pv-cyan` and `pv-green` are decorative, never text.
- Fonts are self-hosted in `assets/fonts/` (OFL, from @fontsource-variable); never load fonts from a third-party server.
- The home-page signal figure is generated: edit `tools/design/make_signal.py`, not `_includes/signal.md`.
- No invented figures: an unsourced number becomes `[à compléter : source]`.
- No real person's name or photo without written consent; keep `noindex` until launch.
- Logos in `assets/img/logos/` come from the CHU websites; communication departments must approve them before release.
- Medical terms to explain for patients: `data/jargon.yml`.
