// Vigiking Normand: layout of the bulletin's PDF, on 16:9 pages for reading on screen.
// The look lives here once; an issue only holds its text (bulletin/README.md).
//
// Editorial design, same identity as the website (assets/theme.scss): Atkinson Hyperlegible
// Next for text (designed for low vision), Bricolage Grotesque for titles, ink on white.
// Each article takes its colour from its place in the issue, along the blue-to-green of
// the CRPV logo darkened for text: the colour moves from blue to green as the issue goes on.
// Contrast (WCAG AA, 4.5:1; tests/test_bulletin_couleurs.py): on white, ink 15.1:1, quiet
// ink 7.3:1, blue 6.9:1, green 6.6:1 (every mix between them above 6.5:1), red 6.5:1,
// orange 5.0:1 (4.6:1 on the mist of the boxes); white on the Channel blue 9.7:1, sea foam
// on it 7.2:1. Cyan, bright green and gold are decoration only.
$reseau.typ()$
$mascotte.typ()$

#let encre = rgb("#10283a")
#let encre-douce = rgb("#46586a")
#let brume = rgb("#eef6fa")
#let filet = rgb("#d5e2ea")
#let manche = rgb("#0d4a5e")
#let ecume = rgb("#bfe3ee")
#let bleu = rgb("#0a5c9e")
#let vert = rgb("#0b6b45")
#let cyan = rgb("#19a6e3")
#let vert-vif = rgb("#2bcf8c")
#let dore = rgb("#e7b03b")
#let rouge-ci = rgb("#b3261e")   // contraindicated: bold too, never colour alone
#let orange-cm = rgb("#b45309")  // risk listed by CredibleMeds: italic too
#let degrade = gradient.linear(cyan, vert-vif)

#let texte = ("Atkinson Hyperlegible Next", "Carlito", "Calibri")
#let titres = ("Bricolage Grotesque", "Atkinson Hyperlegible Next", "Carlito")

// Colour of article i (from 1) out of n: blue, then towards green. Mixed in sRGB, as the
// web version does (vigiking.lua), so both show the same colours.
#let teinte(i, n) = if n <= 1 { bleu } else {
  let t = (i - 1) / (n - 1)
  color.mix((bleu, (1 - t) * 100%), (vert, t * 100%), space: rgb)
}
#let accent = state("vigiking-accent", bleu)
#let fond-sombre = state("vigiking-fond-sombre", false)  // back cover: links in sea foam
#let num-article = counter("vigiking-article")

#let ci(corps) = text(fill: rouge-ci, weight: "bold", corps)
#let cm(corps) = text(fill: orange-cm, style: "italic", corps)

// A small label in capitals: issue month, "Dans ce numéro", author.
#let surtitre(corps, couleur: encre-douce, taille: 9.5pt) = text(
  font: texte, size: taille, weight: 600, tracking: 0.14em, fill: couleur, upper(corps),
)
#let barre-or = box(width: 26pt, height: 3pt, fill: dore, baseline: -0.3em)

// A box: mist background, a bar in the article's colour (a grid cell, so it spans the
// whole height of the text).
#let encadre(corps) = context block(
  width: 100%, fill: brume, radius: (right: 6pt), clip: true, breakable: false,
  grid(columns: (4pt, 1fr), grid.cell(fill: accent.get())[], pad(left: 14pt, right: 12pt, y: 10pt, corps)),
)

#let legende(corps) = block(
  width: 100%, above: 12pt, inset: (top: 8pt), stroke: (top: 0.75pt + filet),
  text(size: 10pt, fill: encre-douce, corps),
)

#let references(corps) = {
  set text(size: 9pt, fill: encre-douce)
  set par(justify: false, leading: 0.4em, spacing: 0.45em)
  set enum(spacing: 0.4em, numbering: n => text(weight: "bold", fill: encre)[#n.])
  block(above: 12pt, corps)
}

#let deux-colonnes(corps) = columns(2, gutter: 1cm, corps)

#let pastilles = (rouge: (rouge-ci, white), vert: (vert, white), bleu: (bleu, white), jaune: (dore, encre))

#let pastille(couleur: "bleu", corps) = {
  let (fond, encre-p) = pastilles.at(couleur, default: pastilles.bleu)
  block(above: 14pt, below: 7pt, box(
    fill: fond, radius: 20pt, inset: (x: 11pt, y: 4.5pt),
    text(font: texte, fill: encre-p, weight: "bold", size: 10pt, tracking: 0.1em, upper(corps)),
  ))
}

// A titled block, one type of content (clinical case, take-home points, did you know…):
// a Word style "Bloc <title>", the template's or one an author created. Its colour comes
// from that style, made readable by vigiking.lua; without one, the article's colour.
#let bloc(titre: none, couleur: auto, fond: auto, corps) = context {
  let c = if couleur == auto { accent.get() } else { couleur }
  let f = if fond == auto { brume } else { fond }
  block(
    width: 100%, breakable: false, fill: f, radius: (bottom: 6pt),
    stroke: (top: 2.5pt + c), inset: (x: 14pt, top: 9pt, bottom: 11pt),
    {
      if titre != none {
        block(below: 0.5em, text(font: texte, size: 0.72em, weight: "bold", tracking: 0.12em, fill: c, upper(titre)))
      }
      corps
    },
  )
}

// The official source of an article (an ANSM letter and its date), on one small line.
#let source(corps) = block(above: 10pt, text(size: 9.5pt, style: "italic", fill: encre-douce, corps))

// A heading run into its paragraph ("En pratique", "Mécanisme"…), in the article's colour.
#let intertitre(corps) = context text(font: titres, weight: 700, fill: accent.get(), corps)

// Key figures: a row of tiles, each a large number and what it counts.
#let chiffres(..items) = context {
  let c = accent.get()
  let liste = items.pos()
  grid(
    columns: (1fr,) * calc.min(calc.max(liste.len(), 1), 4), column-gutter: 10pt, row-gutter: 10pt,
    ..liste.map(((nombre, libelle)) => block(width: 100%, fill: brume, radius: 6pt, inset: (x: 12pt, y: 10pt), {
      if nombre != "" {
        block(below: 0.3em, text(font: titres, weight: 800, size: 2.1em, fill: c, nombre))
      }
      text(size: 0.82em, libelle)
    })),
  )
}

// The editorial, written before the first article: shown on the contents page.
#let editorial-etat = state("vigiking-editorial", none)
#let editorial(corps) = editorial-etat.update(corps)

// The issue as a line of dots, one per article, the current one large and coloured; each
// dot links to its article. It echoes the network of the CRPV logo.
#let piste(i, n) = context {
  let cibles = query(<vigiking-article>)
  let r = 3pt
  box(width: 100%, height: 12pt, {
    place(left + horizon, line(length: 100%, stroke: 1pt + degrade))
    for k in range(n) {
      let x = if n == 1 { 0pt } else { (100% - 12pt) * (k / (n - 1)) }
      let point = if k + 1 == i {
        circle(radius: 6pt, fill: teinte(i, n), stroke: 2pt + white)
      } else {
        box(inset: 3pt, circle(radius: r, fill: white, stroke: 1.2pt + teinte(k + 1, n)))
      }
      let point = if k < cibles.len() { link(cibles.at(k).location(), point) } else { point }
      place(left + horizon, dx: x, point)
    }
  })
}

// Title of an article: its number, large, in the article's colour; its rubric above the
// title ("Cas d'ici et d'ailleurs", "Littérature"…); the author and the reviewer under it.
#let entete(i, n, auteur, titre, rubrique: none, relecture: none) = {
  piste(i, n)
  v(10pt)
  grid(
    columns: (auto, 1fr), column-gutter: 16pt, align: (left + top, left + top),
    text(
      font: titres, weight: 800, size: 46pt, fill: teinte(i, n),
      top-edge: "cap-height", bottom-edge: "baseline",
      if i < 10 [0#i] else [#i],
    ),
    {
      if rubrique != none and rubrique != "" {
        block(below: 6pt, surtitre(rubrique, couleur: teinte(i, n), taille: 9pt))
      }
      heading(level: 2, titre)
      let signe = ()
      if auteur != none and auteur != "" { signe.push([Par #auteur]) }
      if relecture != none and relecture != "" { signe.push([Relecture : #relecture]) }
      if signe.len() > 0 {
        v(5pt)
        surtitre(signe.join[#h(6pt) · #h(6pt)])
      }
    },
  )
  v(14pt)
}

// Body text at a size; figures shrink with it (full width at 20pt, 55% at 11pt), or a
// large picture would keep the text from fitting whatever its size.
#let mise-en-forme(taille, contenu, justifier: false) = {
  set text(size: taille)
  set par(justify: justifier, leading: 0.58em, spacing: 0.8em)
  set list(spacing: 0.7em)
  let echelle = 55% + 45% * calc.clamp((taille.pt() - 11) / 9, 0, 1)
  show figure: it => align(center, block(width: echelle, it))
  contenu
}

// Text sizes tried, largest first, to fill an article's page.
#let tailles = (20pt, 19pt, 18pt, 17pt, 16pt, 15pt, 14pt, 13pt, 12pt, 11pt)
#let gouttiere = 1.1cm

// An article on its own page, in one column or two (the issue's column break splits it;
// vigiking.lua passes each column as its own block). The text gets the largest size at
// which every column fits the page, so nobody resizes text by hand; taille: sets it.
// Each article leaves a measure (size, overflow) that the build's checks read.
#let article(
  auteur: none, rubrique: none, relecture: none, taille: auto, justifier: false,
  titre-texte: "", titre, ..colonnes,
) = {
  pagebreak(weak: true)
  num-article.step()
  context {
    let i = num-article.get().first()
    let n = num-article.final().first()
    accent.update(teinte(i, n))
    let blocs = colonnes.pos()
    let nb = calc.max(blocs.len(), 1)
    // The whole page at a text size: title block, then the columns side by side.
    let page-a(t) = {
      entete(i, n, auteur, titre, rubrique: rubrique, relecture: relecture)
      grid(
        columns: (1fr,) * nb, column-gutter: gouttiere,
        ..blocs.map(c => mise-en-forme(t, c, justifier: justifier)),
      )
    }
    // layout() gives the page's text area; the page is measured whole against it.
    layout(zone => {
      let hauteur(t) = measure(width: zone.width, page-a(t)).height
      // The size is chosen with a safety margin; overflow is reported past the page only.
      let tient(t) = hauteur(t) <= zone.height - 0.3cm
      let t = if taille != auto { taille } else {
        tailles.filter(tient).at(0, default: tailles.last())
      }
      [#metadata((titre: titre, auteur: auteur, rubrique: rubrique)) <vigiking-article>]
      [#metadata((titre: titre-texte, page: here().page(), taille: t.pt(), deborde: hauteur(t) > zone.height)) <vigiking-mesure>]
      page-a(t)
    })
  }
}

// Sources at the end of the issue (references found from their DOI or PMID).
#let annexe(titre, contenu) = {
  pagebreak(weak: true)
  barre-or
  h(8pt)
  surtitre(titre, couleur: encre)
  v(12pt)
  set text(size: 9.5pt)
  columns(2, gutter: 1.1cm, contenu)
}

// Back cover: the centres' details, on the Channel blue, beside the network map.
#let bande(corps) = block(above: 1.1em, below: 0.5em, {
  box(width: 22pt, height: 3pt, fill: dore)
  v(5pt, weak: true)
  text(font: titres, weight: 700, size: 1.2em, fill: white, corps)
})

#let dos(titre, contenu) = {
  let corps(t) = {
    set text(size: t, fill: white)
    set par(justify: false, leading: 0.55em, spacing: 0.7em)
    show strong: set text(fill: white)
    text(font: titres, weight: 800, size: 2.1 * t, titre)
    v(0.4em)
    contenu
  }
  fond-sombre.update(true)
  page(fill: manche, footer: none, margin: (x: 1.6cm, y: 1.3cm), grid(
    columns: (1.75fr, 1fr), column-gutter: 1.2cm, align: (left + top, center + horizon),
    layout(zone => {
      let essais = (14pt, 13pt, 12pt, 11.5pt, 11pt, 10.5pt, 10pt, 9.5pt, 9pt)
      let t = essais.filter(t => measure(width: zone.width, corps(t)).height <= zone.height)
      corps(t.at(0, default: essais.last()))
    }),
    {
      image(reseau-svg, format: "svg", width: 100%, alt: "Carte de la Normandie : les villes reliées aux centres de pharmacovigilance de Caen et de Rouen")
      v(6pt)
      text(size: 9pt, fill: ecume)[Le réseau régional : chaque ville reliée à son centre, Caen ou Rouen.]
    },
  ))
}

// Contents: the articles, numbered in their colour, with their page, grouped under their
// rubric when they have one; the editorial, when the issue has one, beside the list.
#let sommaire(numero, title) = context {
  let arts = query(<vigiking-article>)
  let n = arts.len()
  let edito = editorial-etat.final()
  let serre = edito != none  // a shorter list, beside the editorial
  [#metadata("sommaire") <sommaire>]
  barre-or
  h(8pt)
  surtitre[Dans ce numéro]
  v(6pt)
  text(font: titres, weight: 700, size: 22pt, fill: encre, title)
  v(if serre { 12pt } else { 18pt })
  let entree(k, a) = link(a.location(), grid(
    columns: (if serre { 1.5cm } else { 2.2cm }, 1fr, auto), column-gutter: 10pt,
    align: (left + top, left + top, right + top),
    text(font: titres, weight: 800, size: if serre { 17pt } else { 24pt }, fill: teinte(k + 1, n),
      top-edge: "cap-height", if k < 9 [0#(k + 1)] else [#(k + 1)]),
    {
      text(size: if serre { 11.5pt } else { 14pt }, weight: 600, fill: encre, a.value.titre)
      if a.value.auteur != none and a.value.auteur != "" {
        linebreak()
        text(size: 9pt, fill: encre-douce, a.value.auteur)
      }
    },
    text(size: 10pt, fill: encre-douce)[p. #a.location().page()],
  ))
  // One row per article, and the rubric's name before the first article of each rubric.
  let lignes = ()
  let precedente = none
  for (k, a) in arts.enumerate() {
    let r = a.value.at("rubrique", default: none)
    if r != none and r != "" and r != precedente {
      lignes.push(block(width: 100%, inset: (top: 10pt, bottom: 5pt),
        surtitre(r, couleur: teinte(k + 1, n), taille: 8.5pt)))
    }
    precedente = r
    lignes.push(block(width: 100%, inset: (y: if serre { 5pt } else { 7pt }),
      stroke: (top: 0.75pt + filet), entree(k, a)))
  }
  let liste = if serre or n <= 5 { stack(..lignes) } else {
    let moitie = calc.ceil(lignes.len() / 2)
    grid(columns: (1fr, 1fr), column-gutter: 1.2cm,
      stack(..lignes.slice(0, moitie)), stack(..lignes.slice(moitie)))
  }
  if edito == none { liste } else {
    grid(
      columns: (1fr, 1.3fr), column-gutter: 1.2cm,
      block(width: 100%, fill: manche, radius: 8pt, inset: 16pt, {
        set text(size: 11pt, fill: white)
        set par(leading: 0.55em, spacing: 0.75em)
        show strong: set text(fill: white)
        block(below: 10pt, surtitre([Éditorial], couleur: ecume, taille: 9pt))
        // Links in sea foam on the dark box, as on the back cover.
        fond-sombre.update(true)
        edito
        fond-sombre.update(false)
      }),
      liste,
    )
  }
}

// Cover: the logos, the mascot and the Vigiking banner in a white band, then the theme of the
// issue on the Channel blue, beside the cover picture (or the network map when there is none).
#let une(title, numero, couverture, couverture-alt, logo-gauche, logo-droite, bandeau) = {
  let haut-bande = 2.9cm
  let haut-visuel = 19.05cm - haut-bande - 4pt
  block(width: 100%, height: haut-bande, inset: (x: 1.5cm, y: 0.45cm), below: 0pt, align(horizon, grid(
    columns: (1fr, auto, 1fr), align: (left + horizon, center + horizon, right + horizon),
    if logo-gauche != none { image(logo-gauche, height: 1.7cm, alt: "CRPV de Rouen") },
    box({
      // The site's mascot, left of the banner and turned to sound its horn towards it.
      // Placed outside the cell, so the banner stays centred between the logos.
      place(left + horizon, dx: -2.15cm,
        scale(x: -100%, image(mascotte-svg, format: "svg", height: 2cm, alt: "")))
      if bandeau != none { image(bandeau, height: 2cm, alt: "Vigiking Normand") } else {
        text(font: titres, size: 34pt, weight: 800, fill: bleu, tracking: 0.04em)[VIGIKING NORMAND]
      }
    }),
    if logo-droite != none { image(logo-droite, height: 1.7cm, alt: "CRPV de Caen") },
  )))
  block(width: 100%, height: 4pt, fill: degrade, above: 0pt, below: 0pt)
  block(width: 100%, height: haut-visuel, fill: manche, above: 0pt, clip: true, {
    if couverture != none {
      place(right, box(width: 57%, height: 100%,
        image(couverture, width: 100%, height: 100%, fit: "cover", alt: couverture-alt)))
      // The shade starts a little left of the picture, so no edge of it shows.
      place(right, box(width: 59%, height: 100%, fill: gradient.linear(
        (manche, 0%), (manche, 4%), (manche.transparentize(35%), 25%),
        (manche.transparentize(100%), 50%), (manche.transparentize(100%), 100%),
      )))
    } else {
      place(right + horizon, dx: -1cm, box(width: 46%,
        image(reseau-svg, format: "svg", width: 100%, alt: "")))
    }
    place(left + horizon, dx: 1.5cm, block(width: 39%, {
      barre-or
      h(10pt)
      surtitre(numero, couleur: ecume, taille: 12pt)
      v(14pt)
      layout(zone => {
        let essais = (46pt, 42pt, 38pt, 34pt, 31pt, 28pt)
        let t-titre(t) = {
          set par(leading: 0.22em, justify: false)
          text(font: titres, weight: 800, size: t, fill: white, tracking: -0.01em, title)
        }
        let t = essais.filter(t => measure(width: zone.width, t-titre(t)).height <= 9cm)
        t-titre(t.at(0, default: essais.last()))
      })
      v(18pt)
      link(<sommaire>, text(size: 12pt, fill: ecume)[Au sommaire #sym.arrow.r])
    }))
  })
}

#let vigiking(
  title: none,
  numero: none,
  couverture: none,
  couverture-alt: "",
  logo-gauche: none,
  logo-droite: none,
  bandeau: none,
  doc,
) = {
  set document(title: if title != none { [Vigiking Normand, #numero : #title] })
  // No hyphenation: a drug name is never split across lines.
  set text(lang: "fr", font: texte, size: 15pt, fill: encre, hyphenate: false)
  set page(
    width: 33.867cm, height: 19.05cm,
    margin: (x: 1.6cm, top: 1.0cm, bottom: 1.5cm),
    footer: context {
      if counter(page).get().first() > 2 {
        set text(size: 8.5pt)
        grid(
          columns: (1fr, auto, auto), column-gutter: 16pt, align: horizon,
          surtitre(taille: 8pt)[Vigiking Normand #h(5pt) · #h(5pt) #numero],
          link(<sommaire>, text(fill: bleu)[Sommaire #sym.arrow.t]),
          text(font: titres, weight: 700, size: 11pt, fill: encre, counter(page).display()),
        )
      }
    },
  )
  show heading.where(level: 2): it => block({
    set par(leading: 0.3em, justify: false)
    text(font: titres, size: 25pt, weight: 700, fill: encre, tracking: -0.01em, it.body)
  })
  show heading.where(level: 3): it => block(
    above: 14pt, below: 7pt,
    text(font: titres, size: 1.05em, weight: 700, fill: encre, it.body),
  )
  show strong: set text(weight: "bold")
  // Tables: a header row on the Channel blue, light banding, smaller text (real tables
  // pasted from Word, not pictures of tables).
  set table(
    stroke: none, inset: (x: 8pt, y: 5pt),
    fill: (_, y) => if y == 0 { manche } else if calc.even(y) { brume } else { none },
  )
  show table.cell.where(y: 0): set text(fill: white, weight: "bold")
  show table: set text(size: 0.85em)
  show table: set par(justify: false)
  show figure.caption: it => text(size: 10pt, fill: encre-douce, it.body)
  show figure: set block(above: 10pt, below: 12pt)
  show figure: it => {
    show image: im => box(radius: 5pt, clip: true, im)
    it
  }
  // Web addresses underlined; links inside the document (contents, dots) stay plain.
  show link: it => if type(it.dest) == str {
    context text(fill: if fond-sombre.get() { ecume } else { bleu }, underline(offset: 2pt, stroke: 0.6pt, it))
  } else { it }
  set list(marker: context text(fill: accent.get(), sym.square.filled.small))

  page(margin: 0pt, footer: none, une(title, numero, couverture, couverture-alt, logo-gauche, logo-droite, bandeau))
  sommaire(numero, title)
  doc
}
