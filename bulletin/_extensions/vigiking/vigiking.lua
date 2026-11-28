-- vigiking.lua: maps an issue's Markdown onto the bulletin's layout (bulletin/README.md).
--
--   ## Titre {auteur="…"}                 an article, on its own page in the PDF: one column,
--                                          or two when ::: {.saut-colonne} splits it; the
--                                          text is sized to fill the page (taille=14 sets it)
--   ## Titre {.liste}                     a list of drug names (kept for older issues: all
--                                          text is now left-aligned)
--   ## Titre {.references-page}           the sources found from their DOI or PMID
--                                          (references.py), just before the back cover
--   ## Titre {.dos}                        the back cover; its ### headings become bands
--   ::: {.encadre}  ::: {.legende}  ::: {.saut-colonne}  ::: {.pastille couleur=rouge}
--   ::: {.references} (small print)  ::: {.deux-colonnes}
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

local function Span(el)
  if not TYPST then
    return nil
  end
  for _, cls in ipairs({ "ci", "cm" }) do
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
  if not TYPST then
    return nil
  end
  if el.classes:includes("pastille") then
    local couleur = el.attributes.couleur or "bleu"
    return envelopper("#pastille(couleur: " .. chaine(couleur) .. ")[", el.content)
  end
  for _, cls in ipairs({ "encadre", "legende", "references", "deux-colonnes" }) do
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
  if b.attributes.auteur then
    table.insert(args, "auteur: " .. chaine(b.attributes.auteur))
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
      if b.attributes.auteur then
        out:insert(pandoc.Div(pandoc.Para({ pandoc.Str("Par " .. b.attributes.auteur) }), { class = "auteur" }))
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
