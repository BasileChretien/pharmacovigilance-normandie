-- tableaux.lua: every table of a page sits in its own box, so that a table wider than the
-- screen scrolls inside that box instead of making the whole page scroll sideways.
--
--   <div class="tableau-defile [tableau-cartes | tableau-large]">
--     <div class="tableau-defile-cadre"><table>…</table></div>
--   </div>
--
-- How each table behaves on a phone (assets/theme.scss, "Tables"; docs/tableaux.md):
-- - two columns: the text wraps, the table fits;
-- - three columns or more: one card per row (tableau-cartes). Each body cell gets
--   data-label, the header of its column, which the card shows above the value; the
--   table keeps its rows, cells and headers for screen readers;
-- - class tableau-large (the cytochrome grids): the columns stay, the box scrolls and the
--   first column stays in view;
-- - class tableau-encadre: a generator already wrote the box in raw HTML; left as it is.
-- assets/js/tableaux.js draws the cue at the edge that hides columns, and makes a box that
-- scrolls reachable with the keyboard.

local CARTES_A_PARTIR_DE = 3

-- The header of each column, from the last header row (a cell spanning two columns labels
-- both). Nil when the table has no header row: such a table cannot become cards.
local function libelles(tbl)
  if not tbl.head or #tbl.head.rows == 0 then
    return nil
  end
  local entete = tbl.head.rows[#tbl.head.rows]
  local textes = {}
  for _, cellule in ipairs(entete.cells) do
    local texte = pandoc.utils.stringify(cellule.contents)
    for _ = 1, cellule.col_span do
      textes[#textes + 1] = texte
    end
  end
  return textes
end

local function etiqueter(tbl, textes)
  for _, corps in ipairs(tbl.bodies) do
    for _, ligne in ipairs(corps.body) do
      local colonne = 1
      for _, cellule in ipairs(ligne.cells) do
        local texte = textes[colonne]
        if texte and texte ~= "" then
          cellule.attributes["data-label"] = texte
        end
        colonne = colonne + cellule.col_span
      end
    end
  end
end

local function Table(tbl)
  if not FORMAT:match("html") or tbl.classes:includes("tableau-encadre") then
    return nil
  end
  local classes = { "tableau-defile" }
  if tbl.classes:includes("tableau-large") then
    classes[#classes + 1] = "tableau-large"
  else
    local textes = libelles(tbl)
    if textes and #tbl.colspecs >= CARTES_A_PARTIR_DE then
      classes[#classes + 1] = "tableau-cartes"
      etiqueter(tbl, textes)
    end
  end
  local cadre = pandoc.Div({ tbl }, pandoc.Attr("", { "tableau-defile-cadre" }))
  return pandoc.Div({ cadre }, pandoc.Attr("", classes))
end

return { { Table = Table } }
