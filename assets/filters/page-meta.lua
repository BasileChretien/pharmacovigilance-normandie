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

function Div(el)
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
