-- figure-svg shortcode: places a hand-authored SVG of assets/img/figures/ in a <figure>.
--
--   {{< figure-svg notice-1 alt="Texte alternatif" legende="Légende visible" >}}
--   (optional: description="Description longue, lue par les lecteurs d'écran")
--
-- The SVG is inlined, not loaded through <img>: an SVG image cannot use the page's
-- self-hosted fonts (assets/fonts/). The alternative text becomes the SVG's <title>
-- (role="img"), the description its <desc>, the caption a <figcaption>.
-- Style rules: docs/regles-redaction.md, section 5; checked by tools/checks/check_figures.py.

local FOLDER = "assets/img/figures/"

local function escape(text)
  return (text:gsub("&", "&amp;"):gsub("<", "&lt;"):gsub(">", "&gt;"):gsub('"', "&quot;"))
end

local function argument(kwargs, key)
  local value = kwargs[key]
  if value == nil then
    return ""
  end
  return pandoc.utils.stringify(value)
end

local function read_svg(name)
  local path = pandoc.path.join({ quarto.project.directory, FOLDER .. name .. ".svg" })
  local file = io.open(path, "rb")
  if not file then
    error("figure-svg : fichier introuvable " .. FOLDER .. name .. ".svg")
  end
  local svg = file:read("a")
  file:close()
  local start = svg:find("<svg", 1, true)
  if not start then
    error("figure-svg : pas d'élément <svg> dans " .. FOLDER .. name .. ".svg")
  end
  return svg:sub(start)
end

return {
  ["figure-svg"] = function(args, kwargs)
    local name = pandoc.utils.stringify(args[1] or "")
    local alt = argument(kwargs, "alt")
    local legende = argument(kwargs, "legende")
    local description = argument(kwargs, "description")
    if name == "" or alt == "" or legende == "" then
      error("figure-svg : nom, alt et legende sont obligatoires (" .. name .. ")")
    end
    local id = "figure-" .. name
    local svg = read_svg(name)

    local labels = ' role="img" aria-labelledby="' .. id .. '-titre"'
    local inside = '<title id="' .. id .. '-titre">' .. escape(alt) .. "</title>"
    if description ~= "" then
      labels = labels .. ' aria-describedby="' .. id .. '-desc"'
      inside = inside .. '<desc id="' .. id .. '-desc">' .. escape(description) .. "</desc>"
    end
    local tag_end = svg:find(">", 1, true)
    svg = "<svg" .. labels .. svg:sub(5, tag_end) .. inside .. svg:sub(tag_end + 1)

    local html = '<figure class="figure-pv" id="' .. id .. '">\n' .. svg
      .. "\n<figcaption>" .. escape(legende) .. "</figcaption>\n</figure>"
    return pandoc.RawBlock("html", html)
  end,
}
