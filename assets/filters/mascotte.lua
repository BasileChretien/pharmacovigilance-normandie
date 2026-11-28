-- mascotte.lua
-- The mascot in the title banner of every page (docs/mascotte/README.md). A page's
-- `mascotte:` (its front matter, or its section's _metadata.yml) names a variant of
-- assets/img/mascotte/ (tools/design/make_mascotte.py). This filter turns it into the
-- template variable `mascotte-titre`, the image's path from the page, which
-- _includes/title-block.html places in the banner. A page that already shows the mascot in
-- its body (home, 404, Vigiking, the empty publications list) gets none in its banner.
-- Tests: tests/test_mascotte_bandeau.py, tests/test_mascotte.py.

local stringify = pandoc.utils.stringify

local DOSSIER = "assets/img/mascotte/"

local function warn(message)
  if quarto and quarto.log and quarto.log.warning then
    quarto.log.warning(message)
  else
    io.stderr:write(message .. "\n")
  end
end

local function project_root()
  local root = quarto and quarto.project and quarto.project.directory
  return type(root) == "string" and root or nil
end

-- How many folders deep the page sits under the project root ("a/b.qmd": 1).
local function depth()
  local input = quarto and quarto.doc and quarto.doc.input_file
  local root = project_root()
  if type(input) ~= "string" or root == nil then
    return 0
  end
  local page = pandoc.path.make_relative(input, root):gsub("\\", "/")
  local _, slashes = page:gsub("/", "")
  return slashes
end

local function body_has_mascot(blocks)
  local found = false
  local function look(el)
    if el.format:match("html") and el.text:find('class="mascotte', 1, true) then
      found = true
    end
  end
  pandoc.Blocks(blocks):walk({ RawBlock = look, RawInline = look })
  return found
end

local function exists(path)
  local f = io.open(path, "r")
  if f then
    f:close()
    return true
  end
  return false
end

-- The variant's file, or nil (with a warning) for a name that is not one.
local function variant(name)
  local file = DOSSIER .. "mascotte-" .. name .. ".svg"
  local root = project_root()
  if name:match("^[%w-]+$") and (root == nil or exists(pandoc.path.join({ root, file }))) then
    return file
  end
  warn("mascotte « " .. name .. " » : variante inconnue (" .. DOSSIER .. ", tools/design/make_mascotte.py)")
  return nil
end

function Pandoc(doc)
  if doc.meta.mascotte == nil or body_has_mascot(doc.blocks) then
    return nil
  end
  local file = variant(stringify(doc.meta.mascotte))
  if file == nil then
    return nil
  end
  doc.meta["mascotte-titre"] = pandoc.MetaString(string.rep("../", depth()) .. file)
  return doc
end
