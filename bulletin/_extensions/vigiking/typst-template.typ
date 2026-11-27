// Vigiking Normand: layout of the bulletin's PDF, on 16:9 pages as the PowerPoint version.
// The look lives here once; an issue only holds its text (bulletin/README.md).
// Colours checked for WCAG AA contrast on white: blue 7.3:1, red 6.5:1, orange 5.0:1.

#let bleu = rgb("#2f5597")       // text and titles (as the PowerPoint version)
#let bleu-lien = rgb("#0563c1")  // links
#let bleu-fond = rgb("#eef3fa")  // background of the boxes
#let rouge-ci = rgb("#c00000")   // contraindicated (bold, not colour alone)
#let orange-cm = rgb("#b45309")  // risk listed by CredibleMeds (italic, not colour alone)
#let police = ("Calibri", "Carlito")      // Carlito: free, same metrics as Calibri
#let police-dos = ("Corbel", "Carlito")

#let ci(corps) = text(fill: rouge-ci, weight: "bold", corps)
#let cm(corps) = text(fill: orange-cm, style: "italic", corps)

#let encadre(corps) = block(
  width: 100%, inset: (x: 12pt, y: 9pt), radius: 6pt,
  stroke: 1pt + bleu, fill: bleu-fond, breakable: false, corps,
)

#let legende(corps) = block(
  width: 100%, inset: 8pt, radius: 4pt, stroke: 0.6pt + bleu,
  text(size: 10.5pt, style: "italic", corps),
)

#let references(corps) = {
  set text(size: 9pt, fill: black)
  set par(justify: false, leading: 0.35em, spacing: 0.35em)
  set enum(spacing: 0.3em)
  block(above: 10pt, corps)
}

#let deux-colonnes(corps) = columns(2, gutter: 1cm, corps)

#let pastilles = (
  rouge: (rgb("#b03a2e"), white),
  vert: (rgb("#2e7d32"), white),
  bleu: (bleu, white),
  jaune: (rgb("#f2c94c"), rgb("#1f2937")),
)

#let pastille(couleur: "bleu", corps) = {
  let (fond, encre) = pastilles.at(couleur, default: pastilles.bleu)
  block(above: 10pt, below: 6pt, box(
    fill: fond, radius: 5pt, inset: (x: 10pt, y: 5pt),
    text(fill: encre, weight: "bold", size: 14pt, corps),
  ))
}

// Title of an article, its author on the right.
#let entete(auteur, titre) = {
  grid(
    columns: (1fr, auto), column-gutter: 14pt,
    align: (left + bottom, right + bottom),
    heading(level: 2, titre),
    if auteur != none and auteur != "" {
      text(size: 12pt, style: "italic", weight: 300, auteur)
    },
  )
  v(10pt)
}

#let mise-en-forme(taille, colonnes, contenu, justifier: true) = {
  set text(size: taille)
  set par(justify: justifier, leading: 0.5em, spacing: 0.9em)
  set list(spacing: 0.7em)
  if colonnes > 1 { columns(colonnes, gutter: 1cm, contenu) } else { contenu }
}

// Text sizes tried, largest first, to fill a one-column article's page.
#let tailles = (20pt, 19pt, 18pt, 17pt, 16pt, 15pt, 14pt, 13pt, 12pt)

// An article on its own page. One column: the largest text size that fits the page,
// so nobody resizes text by hand. Two columns (split with a column break): 15 pt, or the
// size the issue sets, as Typst does not balance columns.
#let article(auteur: none, colonnes: 2, taille: auto, justifier: true, titre, contenu) = {
  pagebreak(weak: true)
  entete(auteur, titre)
  if taille != auto or colonnes > 1 {
    mise-en-forme(if taille == auto { 15pt } else { taille }, colonnes, contenu, justifier: justifier)
  } else {
    layout(zone => {
      let dispo = zone.height - measure(width: zone.width, entete(auteur, titre)).height - 1.5cm
      let qui-tient = tailles.filter(t => {
        measure(width: zone.width, mise-en-forme(t, 1, contenu, justifier: justifier)).height <= dispo
      })
      mise-en-forme(qui-tient.at(0, default: tailles.last()), 1, contenu, justifier: justifier)
    })
  }
}

// Back cover: blue bands (level-3 headings of that section), as the PowerPoint version.
#let bande(corps) = block(
  width: 100%, fill: bleu, inset: (x: 10pt, y: 5pt), above: 10pt, below: 8pt,
  align(center, text(fill: white, weight: "bold", size: 15pt, smallcaps(corps))),
)

#let dos(titre, contenu) = {
  pagebreak(weak: true)
  set text(font: police-dos, size: 14pt, fill: black)
  set par(justify: false, leading: 0.45em, spacing: 0.6em)
  bande(titre)
  contenu
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
  set text(lang: "fr", font: police, size: 15pt, fill: bleu, hyphenate: false)
  set page(
    width: 33.867cm, height: 19.05cm,
    margin: (x: 1.5cm, top: 1.1cm, bottom: 1.4cm),
    footer: context {
      if counter(page).get().first() > 1 {
        set text(size: 9pt, fill: bleu)
        grid(
          columns: (1fr, auto), align: (left + horizon, right + horizon),
          [Vigiking Normand #sym.dot.c #numero #sym.dot.c page #counter(page).display()],
          link(<sommaire>, text(size: 11pt, fill: bleu-lien)[#sym.arrow.t Sommaire]),
        )
      }
    },
  )
  show heading.where(level: 2): it => block(
    text(size: 30pt, weight: 300, fill: bleu, it.body),
  )
  show heading.where(level: 3): it => block(
    above: 12pt, below: 6pt, text(size: 16pt, weight: "bold", fill: bleu, it.body),
  )
  show figure.caption: it => text(size: 10.5pt, style: "italic", fill: black, it.body)
  show figure: set block(above: 8pt, below: 10pt)
  show link: it => text(fill: bleu-lien, underline(it))
  show outline.entry: it => block(below: 5pt, link(
    it.element.location(),
    text(size: 17pt, fill: bleu-lien, underline(it.element.body)),
  ))

  // Cover: logos, the Vigiking banner, the month, the theme and the contents.
  page(footer: none, {
    grid(
      columns: (1fr, 2.4fr, 1fr), align: (left + top, center + top, right + top),
      if logo-gauche != none { image(logo-gauche, height: 1.9cm, alt: "CRPV de Rouen") },
      if bandeau != none { image(bandeau, height: 2.4cm, alt: "Vigiking Normand") } else {
        text(size: 44pt, weight: "bold", tracking: 2pt, [VIGIKING NORMAND])
      },
      if logo-droite != none { image(logo-droite, height: 1.9cm, alt: "CRPV de Caen") },
    )
    v(0.3cm)
    align(center, text(size: 22pt, numero))
    v(0.5cm)
    align(center, block(width: 80%, text(size: 28pt, title)))
    v(0.9cm)
    grid(
      columns: (1fr, 1.5fr), column-gutter: 1cm, align: (center + horizon, left + top),
      if couverture != none { image(couverture, width: 85%, alt: couverture-alt) },
      [#outline(title: none, target: heading.where(level: 2)) <sommaire>],
    )
  })
  doc
}
