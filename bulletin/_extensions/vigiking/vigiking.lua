-- vigiking.lua: maps an issue's Markdown onto the bulletin's layout (bulletin/README.md).
--
--   ## Titre {auteur="…"}                 an article, on its own page in the PDF: one column,
--                                          or two when ::: {.saut-colonne} splits it; the
--                                          text is sized to fill the page (taille=14 sets it);
--                                          rubrique="Littérature" above the title (and the
--                                          contents grouped by rubric), relecture="B. Nom"
--   ### Intertitre                        a subheading inside the article (several short
--                                          items under one title: "brèves")
--   ::: {.editorial}                      before the first article: on the contents page
--   ::: {.chiffres}                       key figures, one paragraph each: "66 % des cas…"
--   ::: {.source}                         the official source of an article, one small line
--   [texte]{.intertitre}                  a heading run into its paragraph
--   ## Titre {.liste}                     a list of drug names (kept for older issues: all
--                                          text is now left-aligned)
--   ## Titre {.references-page}           the sources found from their DOI or PMID
--                                          (references.py), just before the back cover
--   ## Titre {.dos}                        the back cover; its ### headings become bands
--   ::: {.encadre}  ::: {.legende}  ::: {.saut-colonne}  ::: {.pastille couleur=rouge}
--   ::: {.references} (small print)  ::: {.deux-colonnes}
--   ::: {.bloc titre="Cas clinique" couleur="#b3261e"}  a titled block: a type of content of
--                                          its own (Word style "Bloc <titre>"); colour optional
--   [texte]{.ci}  contraindicated (red, bold)    [texte]{.cm}  CredibleMeds (orange, italic)
--
-- Articles are numbered and each takes a colour from its place in the issue, from blue to
-- green (typst-template.typ, teinte); the web version gets the same colour as --accent.
-- The PDF (Typst) gets the template's functions; the web version keeps the classes for
-- vigiking.css and gets its cover here.

local TYPST = FORMAT:match("typst") ~= nil
local COLBREAK = "#colbreak()"
local ICI = pandoc.path.directory(PANDOC_SCRIPT_FILE)
local BLEU, VERT = { 10, 92, 158 }, { 11, 107, 69 }

local function raw_block(s)
  return pandoc.RawBlock("typst", s)
end

local function raw_inline(s)
  return pandoc.RawInline("typst", s)
end

-- A Typst string literal.
local function chaine(s)
  return '"' .. s:gsub("\\", "\\\\"):gsub('"', '\\"') .. '"'
end

-- Typst markup of some inlines (a title).
local function en_typst(inlines)
  local texte = pandoc.write(pandoc.Pandoc({ pandoc.Plain(inlines) }), "typst")
  return (texte:gsub("%s+$", ""))
end

-- Colour of article i out of n, mixed in sRGB as the PDF template does.
local function teinte(i, n)
  local t = n <= 1 and 0 or (i - 1) / (n - 1)
  local c = {}
  for k = 1, 3 do
    c[k] = math.floor(BLEU[k] * (1 - t) + VERT[k] * t + 0.5)
  end
  return string.format("#%02x%02x%02x", c[1], c[2], c[3])
end

-- Colours of a titled block (::: {.bloc couleur="#rrggbb"}), from the author's colour: a
-- pale tint of it behind the text, and the colour itself for the title and the rule,
-- darkened towards ink until the title reads on that tint (WCAG AA, 4.5:1). So any
-- colour an author picks in Word stays readable.
local ENCRE = "#10283a"

local function composantes(hex)
  return tonumber(hex:sub(2, 3), 16), tonumber(hex:sub(4, 5), 16), tonumber(hex:sub(6, 7), 16)
end

local function melange(a, b, t)
  local r1, g1, b1 = composantes(a)
  local r2, g2, b2 = composantes(b)
  local function m(x, y)
    return math.floor(x + (y - x) * t + 0.5)
  end
  return string.format("#%02x%02x%02x", m(r1, r2), m(g1, g2), m(b1, b2))
end

local function luminance(hex)
  local function lin(v)
    v = v / 255
    return v <= 0.03928 and v / 12.92 or ((v + 0.055) / 1.055) ^ 2.4
  end
  local r, g, b = composantes(hex)
  return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)
end

local function contraste(a, b)
  local la, lb = luminance(a), luminance(b)
  if la < lb then
    la, lb = lb, la
  end
  return (la + 0.05) / (lb + 0.05)
end

local function couleurs_bloc(hex)
  if not (hex and hex:match("^#%x%x%x%x%x%x$")) then
    return nil
  end
  hex = hex:lower()
  local fond = melange(hex, "#ffffff", 0.9)
  local titre, t = hex, 0
  while contraste(titre, fond) < 4.5 and t < 1 do
    t = t + 0.1
    titre = melange(hex, ENCRE, t)
  end
  return titre, fond
end

local function est_article(b)
  return b.t == "Header"
    and b.level == 2
    and not b.classes:includes("dos")
    and not b.classes:includes("references-page")
end

-- Blocks wrapped in a Typst function call: open[ ...blocks... ].
local function envelopper(open, blocks)
  local out = pandoc.Blocks({ raw_block(open) })
  out:extend(blocks)
  out:insert(raw_block("]"))
  return out
end

-- A titled block: a Typst call for the PDF; colours as CSS variables for the web page.
local function bloc(el)
  local titre, fond = couleurs_bloc(el.attributes.couleur)
  if not TYPST then
    el.attributes.couleur = nil
    if titre then
      el.attributes.style = "--bloc: " .. titre .. "; --bloc-fond: " .. fond
    end
    return el
  end
  local args = {}
  if el.attributes.titre then
    table.insert(args, "titre: " .. chaine(el.attributes.titre))
  end
  if titre then
    table.insert(args, 'couleur: rgb("' .. titre .. '")')
    table.insert(args, 'fond: rgb("' .. fond .. '")')
  end
  return envelopper("#bloc(" .. table.concat(args, ", ") .. ")[", el.content)
end

-- Key figures (::: chiffres, one paragraph each): the leading number, then what it counts.
local function chiffre(bloc_texte)
  local texte = pandoc.utils.stringify(bloc_texte):gsub("\194\160", " ")
  local nombre, libelle = texte:match("^%s*([%+%-<>~]?%s*%d[%d%s.,]*%s*%%?)%s+(.+)$")
  if not nombre then
    return "", texte
  end
  return (nombre:gsub("%s+$", "")), libelle
end

local function chiffres(el)
  local items = {}
  for _, b in ipairs(el.content) do
    if b.t == "Para" or b.t == "Plain" then
      local nombre, libelle = chiffre(b)
      table.insert(items, { nombre, libelle })
    end
  end
  if TYPST then
    local args = {}
    for _, it in ipairs(items) do
      table.insert(args, "(" .. chaine(it[1]) .. ", " .. chaine(it[2]) .. ")")
    end
    return raw_block("#chiffres(" .. table.concat(args, ", ") .. ")")
  end
  local tuiles = pandoc.Blocks({})
  for _, it in ipairs(items) do
    tuiles:insert(pandoc.Div(pandoc.Plain({
      pandoc.Span(it[1], { class = "nombre" }), pandoc.Space(), pandoc.Span(it[2], { class = "libelle" }),
    }), { class = "chiffre" }))
  end
  return pandoc.Div(tuiles, { class = "chiffres" })
end

local function Span(el)
  if not TYPST then
    return nil
  end
  for _, cls in ipairs({ "ci", "cm", "intertitre" }) do
    if el.classes:includes(cls) then
      local out = pandoc.Inlines({ raw_inline("#" .. cls .. "[") })
      out:extend(el.content)
      out:insert(raw_inline("]"))
      return out
    end
  end
end

local function Div(el)
  if el.classes:includes("saut-colonne") then
    return TYPST and raw_block(COLBREAK) or {}
  end
  if el.classes:includes("bloc") then
    return bloc(el)
  end
  if el.classes:includes("chiffres") then
    return chiffres(el)
  end
  if not TYPST then
    return nil
  end
  if el.classes:includes("pastille") then
    local couleur = el.attributes.couleur or "bleu"
    return envelopper("#pastille(couleur: " .. chaine(couleur) .. ")[", el.content)
  end
  for _, cls in ipairs({ "encadre", "legende", "references", "deux-colonnes", "source", "editorial" }) do
    if el.classes:includes(cls) then
      return envelopper("#" .. cls .. "[", el.content)
    end
  end
end

-- The back cover last: the references page, appended after it by the build, moves before.
local function dos_a_la_fin(blocks)
  local avant, dos = pandoc.Blocks({}), pandoc.Blocks({})
  local dans_dos = false
  for _, b in ipairs(blocks) do
    if b.t == "Header" and b.level == 2 then
      dans_dos = b.classes:includes("dos")
    end
    if dans_dos then
      dos:insert(b)
    else
      avant:insert(b)
    end
  end
  avant:extend(dos)
  return avant
end

-- Typst call opening a level-2 section: an article, the references page or the back cover.
local function ouverture(b)
  local titre = en_typst(b.content)
  if b.classes:includes("dos") then
    return "#dos([" .. titre .. "])["
  end
  if b.classes:includes("references-page") then
    return "#annexe([" .. titre .. "])["
  end
  local args = { "titre-texte: " .. chaine(pandoc.utils.stringify(b.content)) }
  for _, cle in ipairs({ "auteur", "rubrique", "relecture" }) do
    if b.attributes[cle] then
      table.insert(args, cle .. ": " .. chaine(b.attributes[cle]))
    end
  end
  if b.attributes.taille then
    table.insert(args, "taille: " .. (tonumber(b.attributes.taille) or 15) .. "pt")
  end
  return "#article(" .. table.concat(args, ", ") .. ")[" .. titre .. "]["
end

-- PDF: one Typst call per level-2 section, its columns as separate blocks.
local function sections_typst(blocks)
  local out = pandoc.Blocks({})
  local ouvert, au_dos = false, false
  for _, b in ipairs(blocks) do
    if b.t == "Header" and b.level == 2 then
      if ouvert then
        out:insert(raw_block("]"))
      end
      au_dos = b.classes:includes("dos")
      out:insert(raw_block(ouverture(b)))
      ouvert = true
    elseif au_dos and b.t == "Header" and b.level == 3 then
      out:insert(raw_block("#bande[" .. en_typst(b.content) .. "]"))
    elseif ouvert and not au_dos and b.t == "RawBlock" and b.text == COLBREAK then
      -- The article's column break: end of the first column's block, start of the second.
      out:insert(raw_block("]["))
    else
      out:insert(b)
    end
  end
  if ouvert then
    out:insert(raw_block("]"))
  end
  return out
end

local function image_meta(meta, cle, alt)
  if meta[cle] then
    return pandoc.Image(alt, pandoc.utils.stringify(meta[cle]))
  end
end

-- Web: the cover, a band of logos then the theme beside the cover picture.
local function une_web(meta)
  local s = pandoc.utils.stringify
  local logos = pandoc.Inlines({})
  for _, l in ipairs({
    image_meta(meta, "logo-gauche", "CRPV de Rouen"),
    image_meta(meta, "bandeau", "Vigiking Normand"),
    image_meta(meta, "logo-droite", "CRPV de Caen"),
  }) do
    logos:insert(l)
  end
  local texte = pandoc.Blocks({})
  if meta.numero then
    texte:insert(pandoc.Div(pandoc.Plain(s(meta.numero)), { class = "une-numero" }))
  end
  if meta.title then
    texte:insert(pandoc.Header(1, meta.title, pandoc.Attr("", { "une-titre", "unnumbered", "unlisted" })))
  end
  if meta.pdf then
    local lien = pandoc.Link("Télécharger le PDF", s(meta.pdf))
    texte:insert(pandoc.Div(pandoc.Plain({ lien }), { class = "une-pdf" }))
  end
  local visuel = pandoc.Blocks({})
  local photo = image_meta(meta, "couverture", meta["couverture-alt"] and s(meta["couverture-alt"]) or "")
  if photo then
    visuel:insert(pandoc.Div(pandoc.Plain({ photo }), { class = "une-photo" }))
  else
    local carte = pandoc.Image("", pandoc.path.join({ ICI, "reseau.svg" }))
    visuel:insert(pandoc.Div(pandoc.Plain({ carte }), { class = "une-carte" }))
  end
  visuel:insert(pandoc.Div(texte, { class = "une-texte" }))
  return pandoc.Div({
    pandoc.Div(pandoc.Plain(logos), { class = "une-bandeau" }),
    pandoc.Div(visuel, { class = "une-visuel" }),
  }, { class = "une column-page" })
end

-- Web: numbered, coloured articles; the author under each title; the map on the back cover.
local function sections_web(blocks, n)
  local out, i = pandoc.Blocks({}), 0
  for _, b in ipairs(blocks) do
    out:insert(b)
    if est_article(b) then
      i = i + 1
      b.classes:insert("article")
      b.attributes.style = "--accent: " .. teinte(i, n)
      local signe = {}
      if b.attributes.auteur then
        table.insert(signe, "Par " .. b.attributes.auteur)
      end
      if b.attributes.relecture then
        table.insert(signe, "Relecture : " .. b.attributes.relecture)
      end
      if #signe > 0 then
        out:insert(pandoc.Div(pandoc.Para({ pandoc.Str(table.concat(signe, " · ")) }), { class = "auteur" }))
      end
    elseif b.t == "Header" and b.level == 2 and b.classes:includes("dos") then
      local alt = "Carte de la Normandie : les villes reliées aux centres de pharmacovigilance de Caen et de Rouen"
      local carte = pandoc.Image(alt, pandoc.path.join({ ICI, "reseau.svg" }))
      out:insert(pandoc.Div(pandoc.Plain({ carte }), { class = "dos-carte" }))
    end
  end
  return out
end

local function mise_en_page(doc)
  local blocks = dos_a_la_fin(doc.blocks)
  if TYPST then
    doc.blocks = sections_typst(blocks)
  else
    local n = 0
    for _, b in ipairs(blocks) do
      if est_article(b) then
        n = n + 1
      end
    end
    doc.blocks = sections_web(blocks, n)
    doc.blocks:insert(1, une_web(doc.meta))
  end
  return doc
end

return {
  { Span = Span, Div = Div },
  { Pandoc = mise_en_page },
}
