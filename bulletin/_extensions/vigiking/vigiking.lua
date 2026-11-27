-- vigiking.lua: maps an issue's Markdown onto the bulletin's layout (bulletin/README.md).
--
--   ## Titre {auteur="…"}                 an article, on its own page in the PDF, in two
--                                          columns split by ::: {.saut-colonne} (15 pt)
--   ## Titre {auteur="…" .une-colonne}    one column, text sized to fill the page;
--                                          taille=14 sets the size by hand
--   ## Titre {.liste}                     left-aligned (lists of drug names), not justified
--   ## Titre {.dos}                        the back cover; its ### headings become blue bands
--   ::: {.encadre}  ::: {.legende}  ::: {.saut-colonne}  ::: {.pastille couleur=rouge}
--   ::: {.references} (small print, two columns)  ::: {.deux-colonnes}
--   [texte]{.ci}  contraindicated (red, bold)    [texte]{.cm}  CredibleMeds (orange, italic)
--
-- The PDF (Typst) gets the template's functions (typst-template.typ); the web version keeps
-- the classes for vigiking.css.

local TYPST = FORMAT:match("typst") ~= nil

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
    return TYPST and raw_block("#colbreak()") or {}
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

-- One article per level-2 heading: its title, then its body in columns (PDF).
local function articles(doc)
  local out = pandoc.Blocks({})
  local ouvert, au_dos = false, false
  for _, b in ipairs(doc.blocks) do
    if b.t == "Header" and b.level == 2 then
      if ouvert then
        out:insert(raw_block("]"))
      end
      local auteur = b.attributes.auteur
      au_dos = b.classes:includes("dos")
      if TYPST then
        local titre = en_typst(b.content)
        if au_dos then
          out:insert(raw_block("#dos([" .. titre .. "])["))
        else
          local args = { "colonnes: " .. (b.classes:includes("une-colonne") and 1 or 2) }
          if auteur then
            table.insert(args, "auteur: " .. chaine(auteur))
          end
          if b.classes:includes("liste") then
            table.insert(args, "justifier: false")
          end
          if b.attributes.taille then
            table.insert(args, "taille: " .. (tonumber(b.attributes.taille) or 15) .. "pt")
          end
          out:insert(raw_block("#article(" .. table.concat(args, ", ") .. ")[" .. titre .. "]["))
        end
        ouvert = true
      else
        -- Web: the author on a line under the title, out of the table of contents.
        out:insert(b)
        if auteur then
          out:insert(pandoc.Div(pandoc.Para({ pandoc.Emph(auteur) }), { class = "auteur" }))
        end
      end
    elseif TYPST and au_dos and b.t == "Header" and b.level == 3 then
      out:insert(raw_block("#bande[" .. en_typst(b.content) .. "]"))
    else
      out:insert(b)
    end
  end
  if ouvert then
    out:insert(raw_block("]"))
  end
  -- Web: a link to the PDF (front matter pdf:) at the top.
  if not TYPST and doc.meta.pdf then
    local cible = pandoc.utils.stringify(doc.meta.pdf)
    local lien = pandoc.Link(pandoc.Inlines("Télécharger la version PDF"), cible)
    out:insert(1, pandoc.Div(pandoc.Para({ lien }), { class = "version-pdf" }))
  end
  doc.blocks = out
  return doc
end

return {
  { Span = Span, Div = Div },
  { Pandoc = articles },
}
