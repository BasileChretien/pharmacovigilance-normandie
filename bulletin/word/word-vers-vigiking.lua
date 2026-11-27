-- word-vers-vigiking.lua: reads an issue written in Word (modele-vigiking.docx, read with
-- docx+styles) into the bulletin's Markdown (vigiking.lua conventions). Run by importer.py.
--
-- In Word                                         In the issue
--   Titre (style "Title")                           title:
--   Sous-titre (style "Subtitle")                   numero: (the month)
--   Titre 1                                         ## an article
--   "Auteur : A. Nom" right after the title         {auteur="A. Nom"}
--   a paragraph "[saut de colonne]"                 two columns, split there; without it,
--                                                   one column that fills its page
--   paragraph style "Encadré", "Légende",           ::: encadre, legende, references
--     "Références"
--   paragraph style "Catégorie rouge" (verte,       ::: {.pastille couleur=rouge}; the
--     bleue, jaune)                                 article becomes a left-aligned list
--   character style "Contre-indication",            [texte]{.ci}, [texte]{.cm}
--     "CredibleMeds"
--   picture, then a "Caption"/"Légende de figure"   a figure with its caption
--     paragraph
--   a picture before the first article              the cover illustration

local BLOCS = { ["Encadré"] = "encadre", ["Légende"] = "legende", ["Références"] = "references" }
local PASTILLES = {
  ["Catégorie rouge"] = "rouge",
  ["Catégorie verte"] = "vert",
  ["Catégorie bleue"] = "bleu",
  ["Catégorie jaune"] = "jaune",
}
local CARACTERES = { ["Contre-indication"] = "ci", ["CredibleMeds"] = "cm" }
local LEGENDES = { ["Caption"] = true, ["Image Caption"] = true, ["Légende de figure"] = true }
local SAUT = "[saut de colonne]"

local function style(el)
  return el.attributes["custom-style"]
end

-- Word paragraph styles: ours become classes; every other style ("Body Text"…) goes.
local function Div(el)
  local s = style(el)
  if BLOCS[s] then
    return pandoc.Div(el.content, { class = BLOCS[s] })
  elseif PASTILLES[s] then
    return pandoc.Div(el.content, pandoc.Attr("", { "pastille" }, { couleur = PASTILLES[s] }))
  elseif LEGENDES[s] then
    return pandoc.Div(el.content, { class = "legende-figure" })
  elseif s then
    return el.content
  end
end

-- Word gives a picture's size in inches; the bulletin takes the same share of the column
-- as the picture had of Word's text width (6.5 in in the template).
local LARGEUR_WORD = 6.5

local function Image(img)
  local pouces = tonumber((img.attributes.width or ""):match("^([%d%.e%-]+)in$"))
  img.attributes.height = nil
  img.attributes.width = nil
  if pouces then
    local part = math.min(100, math.max(10, math.floor(pouces / LARGEUR_WORD * 100 + 0.5)))
    img.attributes.width = part .. "%"
  end
  return img
end

local function Span(el)
  local s = style(el)
  if CARACTERES[s] then
    return pandoc.Span(el.content, { class = CARACTERES[s] })
  elseif s then
    return el.content
  end
end

local function Para(el)
  if pandoc.utils.stringify(el) == SAUT then
    return pandoc.Div({}, { class = "saut-colonne" })
  end
end

-- A figure pandoc already built from a picture and its caption: plain caption text.
local function Figure(fig)
  fig.attributes["custom-style"] = nil -- "Captioned Figure" would make it raw HTML
  fig.caption.long = fig.caption.long:walk({
    Div = function(d)
      return d.content
    end,
  })
  return fig
end

-- The author line right under a title: "Auteur : A. Nom" (or "Auteurs :").
local function auteur(bloc)
  if bloc and bloc.t == "Para" then
    return pandoc.utils.stringify(bloc):match("^%s*Auteurs?%s*:%s*(.-)%s*$")
  end
end

local function seule_image(bloc)
  return bloc and bloc.t == "Para" and #bloc.content == 1 and bloc.content[1].t == "Image"
end

-- Consecutive paragraphs in one style ("Encadré"…): one block, so one box.
local FUSIONNABLES = { encadre = true, legende = true, references = true }

local function fusionner(blocks)
  local out = pandoc.Blocks({})
  for _, b in ipairs(blocks) do
    local precedent = out[#out]
    local cls = b.t == "Div" and #b.classes == 1 and b.classes[1] or nil
    if cls and FUSIONNABLES[cls] and precedent and precedent.t == "Div"
        and #precedent.classes == 1 and precedent.classes[1] == cls then
      precedent.content:extend(b.content)
    else
      out:insert(b)
    end
  end
  return out
end

-- A picture followed by its caption paragraph: a figure.
local function figures(blocks)
  local out, i = pandoc.Blocks({}), 1
  while i <= #blocks do
    local b, suivant = blocks[i], blocks[i + 1]
    if seule_image(b) and suivant and suivant.t == "Div" and suivant.classes:includes("legende-figure") then
      local image = b.content[1]
      local legende = pandoc.utils.blocks_to_inlines(suivant.content)
      out:insert(pandoc.Figure({ pandoc.Plain({ image }) }, { pandoc.Plain(legende) }))
      i = i + 2
    else
      out:insert(b)
      i = i + 1
    end
  end
  return out
end

-- Group the blocks by article: its heading, its author; category labels make a list.
local function articles(blocks)
  local out, i = pandoc.Blocks({}), 1
  local en_cours = nil
  local function fermer()
    if not en_cours then
      return
    end
    local h = en_cours.titre
    local corps = en_cours.corps
    local a_pastille = false
    for _, c in ipairs(corps) do
      if c.t == "Div" and c.classes:includes("pastille") then
        a_pastille = true
      end
    end
    if a_pastille then
      h.classes:insert("liste")
    end
    out:insert(h)
    out:extend(corps)
    en_cours = nil
  end
  while i <= #blocks do
    local b = blocks[i]
    if b.t == "Header" and b.level == 1 then
      fermer()
      local h = pandoc.Header(2, b.content, pandoc.Attr("", {}, {}))
      local nom = auteur(blocks[i + 1])
      if nom then
        h.attributes.auteur = nom
        i = i + 1
      end
      en_cours = { titre = h, corps = pandoc.Blocks({}) }
    elseif en_cours then
      en_cours.corps:insert(b)
    else
      out:insert(b)
    end
    i = i + 1
  end
  fermer()
  return out
end

-- Front matter: the month from the subtitle; output names and images from importer.py.
local function metadonnees(meta)
  local fichier = meta.fichier and pandoc.utils.stringify(meta.fichier) or "vigiking"
  if meta.subtitle then
    meta.numero = pandoc.utils.stringify(meta.subtitle)
    meta.subtitle = "Vigiking Normand, " .. pandoc.utils.stringify(meta.subtitle)
  end
  meta["dossier-images"] = nil
  meta.pdf = fichier .. ".pdf"
  meta.format = {
    ["vigiking-typst"] = { ["output-file"] = fichier .. ".pdf" },
    ["vigiking-html"] = { ["output-file"] = fichier .. ".html" },
  }
  meta.fichier = nil
  return meta
end

-- A picture before the first article: the cover illustration (with its alternative text).
local function couverture(doc)
  for i, b in ipairs(doc.blocks) do
    if b.t == "Header" then
      return
    end
    local image = nil
    if seule_image(b) then
      image = b.content[1]
    elseif b.t == "Figure" and #b.content == 1 and seule_image(pandoc.Para(b.content[1].content)) then
      image = b.content[1].content[1]
    end
    if image then
      -- pandoc moves extracted pictures into this folder after the filter has run.
      local dossier = doc.meta["dossier-images"] and pandoc.utils.stringify(doc.meta["dossier-images"])
      doc.meta.couverture = dossier and (dossier .. "/" .. image.src) or image.src
      doc.meta["couverture-alt"] = pandoc.utils.stringify(image.caption)
      doc.blocks:remove(i)
      return
    end
  end
end

local function document(doc)
  couverture(doc)
  doc.blocks = articles(figures(fusionner(doc.blocks)))
  -- The standard back cover (bulletin/commun/dos.md), when importer.py found it.
  if doc.meta.dos then
    local chemin = pandoc.utils.stringify(doc.meta.dos)
    doc.blocks:insert(pandoc.RawBlock("markdown", "{{< include " .. chemin .. " >}}"))
    doc.meta.dos = nil
  end
  doc.meta = metadonnees(doc.meta)
  return doc
end

return {
  { Div = Div, Span = Span, Para = Para, Image = Image },
  { Figure = Figure },
  { Pandoc = document },
}
