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

function Div(el)
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

local function sources_list(meta)
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
        inlines:extend(pandoc.Inlines(" (consulté le " .. date_fr(stringify(s.consulte_le)) .. ")"))
      end
      table.insert(items, { pandoc.Plain(inlines) })
    end
  end
  return items
end

function Pandoc(doc)
  local meta = doc.meta
  local statut = meta_str(meta, "statut")

  if statut == "brouillon" then
    local bandeau = pandoc.Div(
      { pandoc.Para(pandoc.Inlines("Brouillon à relire : ce contenu n’a pas encore été validé par un pharmacologue.")) },
      pandoc.Attr("", { "statut-brouillon" }, { { "role", "note" } })
    )
    doc.blocks:insert(1, bandeau)
  end

  local items = sources_list(meta)
  if statut ~= nil or #items > 0 then
    local bloc = pandoc.Blocks({})
    bloc:insert(pandoc.Header(2, pandoc.Inlines("Sources et relecture"), pandoc.Attr("sources-et-relecture")))
    if #items > 0 then
      bloc:insert(pandoc.BulletList(items))
    end
    local relu_par = meta_str(meta, "relu_par")
    local relu_le = meta_str(meta, "relu_le")
    local prochaine = meta_str(meta, "prochaine_relecture")
    local txt
    if relu_par and relu_le then
      txt = "Relu par " .. relu_par .. " le " .. date_fr(relu_le) .. "."
    else
      txt = "Pas encore relu."
    end
    if prochaine then
      txt = txt .. " Prochaine relecture : " .. date_fr(prochaine) .. "."
    end
    bloc:insert(pandoc.Para(pandoc.Inlines(txt)))
    doc.blocks:insert(pandoc.Div(bloc, pandoc.Attr("", { "sources-relecture" })))
  end

  return doc
end
