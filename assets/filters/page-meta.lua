-- page-meta.lua
-- 1. Turns ::: {.a-retenir} and ::: {.quand-consulter} into titled, labelled boxes.
-- 2. Adds a "draft" banner when the page front matter says statut: brouillon.
-- 3. Appends a "Sources et relecture" section built from the front matter
--    (sources, relu_par, relu_le, prochaine_relecture), so every page shows
--    its sources and review dates in the same place.

local stringify = pandoc.utils.stringify

local TITRES = {
  ["a-retenir"] = "À retenir",
  ["quand-consulter"] = "Quand consulter",
}

-- Labels of the generated blocks, by page language (lang: en in the front matter).
local LIBELLES = {
  fr = {
    brouillon = "Brouillon à relire : ce contenu n’a pas encore été validé par un pharmacologue.",
    sources = "Sources et relecture",
    plus_loin = "Pour aller plus loin",
    consulte = "consulté le",
    relu = "Relu par %s le %s.",
    pas_relu = "Pas encore relu.",
    prochaine = " Prochaine relecture : %s.",
  },
  en = {
    brouillon = "Draft to be reviewed: a pharmacologist has not yet checked this content.",
    sources = "Sources and review",
    plus_loin = "Further reading (in French)",
    consulte = "accessed",
    relu = "Reviewed by %s on %s.",
    pas_relu = "Not reviewed yet.",
    prochaine = " Next review: %s.",
  },
}

local function date_fr(s)
  local y, m, d = s:match("^(%d%d%d%d)%-(%d%d)%-(%d%d)$")
  if y then
    return d .. "/" .. m .. "/" .. y
  end
  return s
end

local function meta_str(meta, key)
  local v = meta[key]
  if v == nil then
    return nil
  end
  local s = stringify(v)
  if s == "" or s == "null" or s == "~" then
    return nil
  end
  return s
end

-- Patient and professional versions: shown as two labelled sections, one after the
-- other, with a "go to version" link at the top, instead of tabs. The user panel
-- (docs/panel/synthese.md) showed that tabs hid the professional text, kept it out
-- of the search index, broke the heading order and could not be printed.
local function version_class(text)
  if text:lower():find("patient") then
    return "partie-patients"
  end
  return "partie-pros"
end

local function sections_from_tabset(el)
  local groups = {}
  local current = nil
  local preamble = pandoc.Blocks({})
  for _, block in ipairs(el.content) do
    if block.t == "Header" and block.level == 2 then
      current = { header = block, blocks = pandoc.Blocks({ block }) }
      table.insert(groups, current)
    elseif current then
      current.blocks:insert(block)
    else
      preamble:insert(block)
    end
  end
  if #groups == 0 then
    return nil
  end
  local out = pandoc.Blocks({})
  out:extend(preamble)
  if #groups > 1 then
    local links = pandoc.Inlines("Aller à la version : ")
    for i, group in ipairs(groups) do
      if i > 1 then
        links:extend(pandoc.Inlines(" · "))
      end
      links:insert(pandoc.Link(stringify(group.header.content), "#" .. group.header.identifier))
    end
    out:insert(pandoc.Div(
      { pandoc.Plain(links) },
      pandoc.Attr("", { "versions" }, { { "role", "navigation" }, { "aria-label", "Versions de la page" } })
    ))
  end
  for _, group in ipairs(groups) do
    out:insert(pandoc.Div(group.blocks, pandoc.Attr("", { "partie", version_class(stringify(group.header.content)) })))
  end
  return out
end

-- ::: {.texte-patient} and ::: {.texte-pro} only mark text for check_content.py, which
-- reads the source. Nothing in the rendered site uses them, and Pandoc leaves any heading
-- inside an ordinary div out of the table of contents (user panel, round 2: "Sur cette
-- page" listed only "Sources et relecture"). So the bare wrapper is dropped from the output.
local WRAPPERS = { ["texte-patient"] = true, ["texte-pro"] = true }

local function is_bare_wrapper(el)
  return #el.classes == 1 and WRAPPERS[el.classes[1]] and el.identifier == "" and #el.attributes == 0
end

function Div(el)
  if is_bare_wrapper(el) then
    return el.content
  end
  if el.classes:includes("deux-versions") then
    return sections_from_tabset(el)
  end
  for cls, titre_defaut in pairs(TITRES) do
    if el.classes:includes(cls) then
      -- A box may carry its own title: ::: {.quand-consulter titre="En cas d'urgence"}
      local titre = el.attributes["titre"] or titre_defaut
      el.attributes["titre"] = nil
      if not el.classes:includes("encadre") then
        el.classes:insert("encadre")
      end
      el.attributes["role"] = "note"
      el.attributes["aria-label"] = titre
      local tete = pandoc.Div(
        { pandoc.Plain(pandoc.Inlines(titre)) },
        pandoc.Attr("", { "encadre-titre" })
      )
      el.content:insert(1, tete)
      return el
    end
  end
  return nil
end

-- Further reading, from the front matter (pour_aller_plus_loin: titre, url, site), so the
-- links to the CRPV network and to the French college of medical pharmacology look the
-- same on every page. A site code gives the publisher's name; any other text is shown as is.
local SITES = {
  rfcrpv = "Réseau français des centres régionaux de pharmacovigilance",
  cnpm = "Collège national de pharmacologie médicale (pour les professionnels et les étudiants)",
}

local function plus_loin_list(meta)
  local items = {}
  local liens = meta.pour_aller_plus_loin
  if type(liens) ~= "table" then
    return items
  end
  for _, l in ipairs(liens) do
    if type(l) == "table" and l.titre ~= nil and l.url ~= nil then
      local inlines = pandoc.Inlines({ pandoc.Link(pandoc.Inlines(stringify(l.titre)), stringify(l.url)) })
      if l.site ~= nil then
        local site = stringify(l.site)
        inlines:extend(pandoc.Inlines(" — " .. (SITES[site] or site)))
      end
      table.insert(items, { pandoc.Plain(inlines) })
    end
  end
  return items
end

local function sources_list(meta, libelles)
  local items = {}
  local src = meta.sources
  if type(src) ~= "table" then
    return items
  end
  for _, s in ipairs(src) do
    if type(s) == "table" and s.titre ~= nil then
      local titre = stringify(s.titre)
      local inlines
      if s.url ~= nil and stringify(s.url) ~= "" then
        inlines = pandoc.Inlines({ pandoc.Link(pandoc.Inlines(titre), stringify(s.url)) })
      else
        inlines = pandoc.Inlines(titre)
      end
      if s.consulte_le ~= nil then
        inlines:extend(pandoc.Inlines(" (" .. libelles.consulte .. " " .. date_fr(stringify(s.consulte_le)) .. ")"))
      end
      table.insert(items, { pandoc.Plain(inlines) })
    end
  end
  return items
end

-- Editorial placeholders such as "[à compléter : source]" or "[to confirm]" become a
-- small labelled badge, so readers see a deliberate "to be completed" mark rather than
-- stray brackets (user panel, round 2: 8 of 10 testers lost trust over raw brackets).
local PLACEHOLDER_WORDS = { "compléter", "vérifier", "to confirm", "à construire", "à publier",
  "à préciser", "à demander", "à valider", "draft", "à confirmer" }

local function is_placeholder(text)
  -- pandoc.text.lower, not string.lower: on Windows string.lower reads UTF-8 bytes
  -- as Latin-1 and breaks accented letters, so "compléter" never matched.
  local lower = pandoc.text.lower(text)
  for _, word in ipairs(PLACEHOLDER_WORDS) do
    if lower:find(word, 1, true) then
      return true
    end
  end
  return false
end

local function closes_bracket(el)
  return el.t == "Str" and el.text:find("]", 1, true) ~= nil
end

-- If a placeholder starts at inlines[i], return its badge, the text after the closing
-- bracket, and the index of the last token used; otherwise nil.
local function placeholder_at(inlines, i)
  local first = inlines[i]
  if first.t ~= "Str" or first.text:sub(1, 1) ~= "[" then
    return nil
  end
  local j = i
  while j <= #inlines and not closes_bracket(inlines[j]) do
    j = j + 1
  end
  if j > #inlines then
    return nil
  end
  local run = pandoc.Inlines({})
  for k = i, j do
    run:insert(inlines[k])
  end
  local last = run[#run].text
  local close = last:find("]", 1, true)
  run[#run] = pandoc.Str(last:sub(1, close))
  if not is_placeholder(stringify(run)) then
    return nil
  end
  local badge = pandoc.Span(run, pandoc.Attr("", { "a-completer" }, { { "title", "Élément à compléter avant publication" } }))
  return badge, last:sub(close + 1), j
end

function Inlines(inlines)
  local out = pandoc.Inlines({})
  local i = 1
  while i <= #inlines do
    local badge, trailing, j = placeholder_at(inlines, i)
    if badge then
      out:insert(badge)
      if trailing ~= "" then
        out:insert(pandoc.Str(trailing))
      end
      i = j + 1
    else
      out:insert(inlines[i])
      i = i + 1
    end
  end
  return out
end

-- Pages written with "###" directly under the title (no "##") skip a heading level:
-- shift them up so the outline goes h1 -> h2 -> h3 (RGAA 9.1).
local function fix_heading_levels(blocks)
  local min_level = 7
  blocks:walk({ Header = function(h)
    if h.level < min_level then
      min_level = h.level
    end
  end })
  if min_level >= 3 and min_level < 7 then
    local shift = min_level - 2
    return blocks:walk({ Header = function(h)
      h.level = h.level - shift
      return h
    end })
  end
  return blocks
end

function Pandoc(doc)
  local meta = doc.meta
  local statut = meta_str(meta, "statut")
  local libelles = LIBELLES[meta_str(meta, "lang") or "fr"] or LIBELLES.fr
  doc.blocks = fix_heading_levels(doc.blocks)

  if statut == "brouillon" then
    local bandeau = pandoc.Div(
      { pandoc.Para(pandoc.Inlines(libelles.brouillon)) },
      pandoc.Attr("", { "statut-brouillon" }, { { "role", "note" } })
    )
    doc.blocks:insert(1, bandeau)
  end

  local liens = plus_loin_list(meta)
  if #liens > 0 then
    doc.blocks:insert(pandoc.Div({
      pandoc.Header(2, pandoc.Inlines(libelles.plus_loin), pandoc.Attr("pour-aller-plus-loin")),
      pandoc.BulletList(liens),
    }, pandoc.Attr("", { "plus-loin" })))
  end

  local items = sources_list(meta, libelles)
  if statut ~= nil or #items > 0 then
    local bloc = pandoc.Blocks({})
    bloc:insert(pandoc.Header(2, pandoc.Inlines(libelles.sources), pandoc.Attr("sources-et-relecture")))
    if #items > 0 then
      bloc:insert(pandoc.BulletList(items))
    end
    local relu_par = meta_str(meta, "relu_par")
    local relu_le = meta_str(meta, "relu_le")
    local prochaine = meta_str(meta, "prochaine_relecture")
    local txt
    if relu_par and relu_le then
      txt = string.format(libelles.relu, relu_par, date_fr(relu_le))
    else
      txt = libelles.pas_relu
    end
    if prochaine then
      txt = txt .. string.format(libelles.prochaine, date_fr(prochaine))
    end
    bloc:insert(pandoc.Para(pandoc.Inlines(txt)))
    doc.blocks:insert(pandoc.Div(bloc, pandoc.Attr("", { "sources-relecture" })))
  end

  return doc
end
