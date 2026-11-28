-- rcp-annote.lua: the annotated SmPC of comprendre/lire-un-rcp.qmd.
--
--   ::: {.rcp-annote}
--   ::: {.rcp-section numero="4.8" titre="Effets indésirables"}
--   **À y chercher.** …
--
--   **Dans ce RCP.** …
--   :::
--   :::
--
-- Each section becomes a disclosure (details and summary): its number and title side by side
-- (.rcp-ligne, so that a long title wraps under itself), which open its note. Native HTML,
-- so the keyboard, screen readers and browsers without JavaScript all work as they are. A
-- section without its number or title stops the render.

local function echapper(s)
  return (s:gsub("&", "&amp;"):gsub("<", "&lt;"):gsub(">", "&gt;"):gsub('"', "&quot;"))
end

local function Div(el)
  if not el.classes:includes("rcp-section") or not FORMAT:match("html") then
    return nil
  end
  local numero, titre = el.attributes.numero, el.attributes.titre
  if not numero or numero == "" or not titre or titre == "" then
    error("rcp-annote : un bloc .rcp-section sans numero ou sans titre")
  end
  local blocs = pandoc.Blocks({
    pandoc.RawBlock(
      "html",
      '<details class="rcp-section"><summary><span class="rcp-ligne"><span class="rcp-numero">'
        .. echapper(numero)
        .. '</span> <span class="rcp-titre">'
        .. echapper(titre)
        .. '</span></span></summary><div class="rcp-note">'
    ),
  })
  blocs:extend(el.content)
  blocs:insert(pandoc.RawBlock("html", "</div></details>"))
  return blocs
end

return { { Div = Div } }
