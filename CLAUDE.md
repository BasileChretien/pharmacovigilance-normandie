# pharmacovigilance-normandie

Quarto website prototype for the regional pharmacovigilance centres (CRPV) of Caen and
Rouen. Content is in French; every medical page is a draft until a named pharmacologist
reviews it.

## Commands

- `quarto preview` / `quarto render` — build the site into `_site/`.
- `uv run pytest` — tests of the checks.
- `uv run python tools/checks/check_content.py [--strict] [files]` — writing and front-matter rules.
- `uv run python tools/checks/check_contrast.py` — WCAG contrast of the colour tokens.
- `uv run python tools/checks/check_figures.py` — figures: SVG size, colours, font, ids, and their shortcodes.
- `npm run check:html` — validate rendered HTML (after `quarto render`).
- `uv run python tools/checks/check_toc.py` — every section heading is in its page's table of contents (after `quarto render`).

- `uv run python tools/design/make_carte_departements.py` — regenerate the department map of normandie/carte.qmd (`assets/img/figures/carte-1.svg`, data `data/normandie-carte.json`).
- `uv run python tools/build/make_cyp_index.py` — regenerate the per-drug index of the cytochrome table.
- `uv run python tools/build/fetch_crpv.py` then `make_crpv_page.py` — refresh the list of the French CRPV (ANSM) for crpv/trouver-mon-crpv.qmd.
- `uv run python tools/build/fetch_bdpm.py` then `make_bdpm_liens.py` and `make_bdpm_recherche.py` (index of medicaments/chercher.qmd, `assets/data/medicaments.json`) — monthly: official notice/SmPC links of the class sheets (front matter `substances:`) and marketing status of cited BDPM products (cache `data/bdpm/`, gitignored).
- `uv run python tools/build/fetch_openmedic.py` then `make_openmedic.py` — yearly: reimbursed medicines in Normandy vs France (Open Medic + INSEE, cache `data/openmedic/`, gitignored) for normandie/medicaments-rembourses.qmd.
- `uv run python tools/build/fetch_vigiking.py` then `make_vigiking_page.py` — at each new issue: archive of Vigiking issues (links to rfcrpv.fr) for vigiking/archives.qmd.
- `uv run python tools/build/fetch_alertes.py` then `make_alertes_page.py` — refresh the official alerts feed (ANSM, EMA); the Pages build also runs both every Monday, stdlib only (runner's python3).
- `uv run python tools/build/fetch_publications.py` then `make_publications_page.py` — teams' recent publications (crpv/recherche.qmd): ORCID iDs of the member cards on crpv/equipe-*.qmd, then ORCID and OpenAlex; also run by the Pages build. No author names on the page.
- `uv run python bulletin/word/importer.py numero.docx <AAAA-MM>` then `cd bulletin && quarto render numeros/<AAAA-MM>/vigiking-<AAAA-MM>.qmd` — Vigiking bulletin (from Word, template `bulletin/word/modele-vigiking.docx`), PDF (16:9) and web page from one file; its own Quarto project, out of the site build; issues stay local (gitignored) until the CRPV agree to host them (`bulletin/README.md`).

Status and open tasks: `docs/STATUS.md`. Points for medical reviewers: `docs/relecture.md`.

## Conventions

- Writing rules and front-matter schema: `docs/regles-redaction.md`. Templates: `_templates/`.
- Patient text goes in `::: {.texte-patient}`, professional text in `::: {.texte-pro}` (source-only markers: the filter drops them so their headings reach the table of contents);
  boxes are `::: {.a-retenir}` (3 points max) and `::: {.quand-consulter}`.
- Never write sources, review dates or the draft banner by hand: `assets/filters/page-meta.lua`
  builds them from the front matter.
- Further reading goes in `pour_aller_plus_loin:` (titre, url, site: rfcrpv | cnpm), 3 links at most, each checked to answer before adding.
- Colours live only in `assets/theme.scss`; add every new text/background pair to
  `tools/checks/contrast_pairs.yml`. `pv-cyan`, `pv-green` and `pv-or` (Normandy gold) are decorative, never text; Normandy motifs (colombages, Channel wave) are inline SVG in `theme.scss`.
- Figures are hand-authored SVG in `assets/img/figures/`, placed with `{{< figure-svg name alt="…" legende="…" >}}` (inlined for the site fonts); style rules in `docs/regles-redaction.md` §5.
- Fonts are self-hosted in `assets/fonts/` (OFL, from @fontsource-variable); never load fonts from a third-party server.
- The home-page map is generated: edit `tools/design/make_signal.py` (data: `data/normandie-carte.json`, refreshed by `tools/design/fetch_normandie.py`), not `_includes/signal.md`. Its motion needs the pause button (WCAG 2.2.2): keep animations gated by `.signal-anime` (added by `assets/js/accueil.js`).
- Search synonyms and the accent-free index copy: `tools/build/search_postprocess.py` (post-render).
- Long tables get a filter field: wrap them in `::: {.tableau-filtrable}` and load `assets/js/table-filter.js` (see `bon-usage/cytochromes.qmd`); JS tests: `npm run test:js`.
- `[à compléter …]`-style brackets render as badges (page-meta.lua); in Lua use `pandoc.text.lower`, not `string.lower` (breaks UTF-8 on Windows).
- Pushing to `main` deploys GitHub Pages (`.github/workflows/pages.yml`); keep links relative (site lives under a subpath).
- No invented figures: an unsourced number becomes `[à compléter : source]`.
- No real person's name or photo without written consent; keep `noindex` until launch.
- Logos in `assets/img/logos/` come from the CHU websites; communication departments must approve them before release.
- Medical terms to explain for patients: `data/jargon.yml`.
