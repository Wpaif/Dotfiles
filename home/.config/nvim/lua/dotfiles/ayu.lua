-- Camada exclusivamente visual: Ayu Dark com a paleta do terminal.
-- Referências: alacritty/alacritty-theme (ayu_dark) e slugbyte/lackluster.nvim.
local M = {}

M.palette = {
  bg = "#07090d", fg = "#b3b1ad", surface = "#10141c", selection = "#1b2736",
  border = "#27303c", muted = "#697482", accent = "#ffb454", yellow = "#ffee99",
  green = "#9ccc42", bright_green = "#b4e64d", red = "#ff4d5a", bright_red = "#ff6670",
  blue = "#59c2ff", cyan = "#95e6cb", white = "#c7c7c7",
}

function M.apply()
  local p = M.palette
  -- Paleta da sintaxe independente das cores da interface.
  local syntax = {
    comment = "#95a4b8", keyword = "#ff4f64", number = "#ffb347",
    boolean = "#e879f9", parameter = "#ffa45b", property = "#a995ff",
    constant = "#ffb347", operator = "#f0d47c", delimiter = "#bec9d9",
    string = "#9de34f", func = "#639dff", type = "#bc85ff", identifier = "#d6deeb", special = "#ff82b2",
  }
  vim.opt.termguicolors = true
  vim.opt.background = "dark"
  vim.cmd("highlight clear")
  if vim.g.syntax_on then vim.cmd("syntax reset") end
  vim.g.colors_name = "ayu-dark"

  -- Bordas simples e finas; mantém as demais opções do LazyVim.
  vim.opt.winborder = "single"
  vim.opt.fillchars:append({ vert = "│", horiz = "─", horizup = "┴", horizdown = "┬", vertleft = "┤", vertright = "├", verthoriz = "┼" })
  local groups = {
    Normal = { fg = p.fg, bg = p.bg }, NormalNC = { fg = p.fg, bg = p.bg },
    NormalFloat = { fg = p.fg, bg = p.surface }, FloatBorder = { fg = p.border, bg = p.surface },
    FloatTitle = { fg = p.accent, bg = p.surface, bold = true },
    WinSeparator = { fg = p.border, bg = p.bg }, EndOfBuffer = { fg = p.bg },
    SignColumn = { bg = p.bg }, FoldColumn = { fg = p.muted, bg = p.bg },
    LineNr = { fg = "#424d5b", bg = p.bg }, CursorLineNr = { fg = p.accent, bold = true },
    CursorLine = { bg = p.surface }, ColorColumn = { bg = p.surface },
    Cursor = { fg = p.bg, bg = p.accent }, Visual = { bg = p.selection },
    Search = { fg = p.accent, bg = p.selection }, IncSearch = { fg = p.bg, bg = p.accent },
    CurSearch = { link = "IncSearch" }, MatchParen = { fg = p.accent, bg = p.selection, bold = true },
    StatusLine = { fg = p.fg, bg = p.surface }, StatusLineNC = { fg = p.muted, bg = p.bg },
    TabLine = { fg = p.muted, bg = p.bg }, TabLineFill = { bg = p.bg },
    TabLineSel = { fg = p.accent, bg = p.surface, bold = true },
    Pmenu = { fg = p.fg, bg = p.surface }, PmenuSel = { fg = p.accent, bg = p.selection },
    PmenuSbar = { bg = p.surface }, PmenuThumb = { bg = p.border },
    NonText = { fg = p.border }, Whitespace = { fg = p.border },
    Conceal = { fg = p.muted }, Folded = { fg = p.muted, bg = p.surface },
    Directory = { fg = p.blue }, Title = { fg = p.accent, bold = true },
    MoreMsg = { fg = p.green }, Question = { fg = p.cyan }, WarningMsg = { fg = p.accent },
    ErrorMsg = { fg = p.bright_red }, Error = { fg = p.bright_red },
    Comment = { fg = syntax.comment, italic = true }, Constant = { fg = syntax.constant },
    String = { fg = syntax.string }, Character = { fg = syntax.string }, Number = { fg = syntax.number },
    Boolean = { fg = syntax.boolean }, Float = { fg = syntax.number }, Identifier = { fg = syntax.identifier },
    Function = { fg = syntax.func }, Statement = { fg = syntax.keyword }, Operator = { fg = syntax.operator },
    Keyword = { fg = syntax.keyword, bold = true }, PreProc = { fg = syntax.boolean }, Type = { fg = syntax.type },
    Special = { fg = syntax.special }, Delimiter = { fg = syntax.delimiter }, Underlined = { fg = p.blue, underline = true },
    Parameter = { fg = syntax.parameter }, Property = { fg = syntax.property },
    Todo = { fg = p.accent, bg = p.surface, bold = true },
    DiffAdd = { bg = "#142015" }, DiffChange = { bg = "#14202d" },
    DiffDelete = { bg = "#2a141c" }, DiffText = { bg = "#203348" },
    GitSignsAdd = { fg = p.green }, GitSignsChange = { fg = p.blue }, GitSignsDelete = { fg = p.red },
    DiagnosticError = { fg = p.bright_red }, DiagnosticWarn = { fg = p.accent },
    DiagnosticInfo = { fg = p.blue }, DiagnosticHint = { fg = p.cyan },
    DiagnosticOk = { fg = p.green },
    DiagnosticUnderlineError = { sp = p.red, undercurl = true },
    DiagnosticUnderlineWarn = { sp = p.accent, undercurl = true },
    DiagnosticUnderlineInfo = { sp = p.blue, undercurl = true },
    DiagnosticUnderlineHint = { sp = p.cyan, undercurl = true },
    DiagnosticVirtualTextError = { fg = p.bright_red, bg = "#201218" },
    DiagnosticVirtualTextWarn = { fg = p.accent, bg = "#211b13" },
    DiagnosticVirtualTextInfo = { fg = p.blue, bg = p.surface },
    DiagnosticVirtualTextHint = { fg = p.cyan, bg = p.surface },
    LspReferenceText = { bg = p.selection }, LspReferenceRead = { bg = p.selection },
    LspReferenceWrite = { bg = p.selection }, LspInlayHint = { fg = p.muted, bg = p.surface },
    LspSignatureActiveParameter = { fg = p.accent, bold = true },
    SnacksIndent = { fg = "#1b2330" }, SnacksIndentScope = { fg = p.border },
    SnacksPickerMatch = { fg = p.accent, bold = true },
    SnacksPickerDirectory = { fg = p.muted }, SnacksPickerDir = { fg = p.muted },
    SnacksPickerSelected = { fg = p.green }, SnacksPickerCursorLine = { bg = p.selection },
    SnacksDashboardHeader = { fg = p.muted }, SnacksDashboardIcon = { fg = p.accent },
    SnacksDashboardKey = { fg = p.accent }, SnacksDashboardDesc = { fg = p.fg },
    SnacksDashboardFooter = { fg = p.muted },
    WhichKey = { fg = p.accent }, WhichKeyGroup = { fg = p.blue }, WhichKeyDesc = { fg = p.fg },
    WhichKeySeparator = { fg = p.border }, WhichKeyValue = { fg = p.muted },
    LazyNormal = { link = "NormalFloat" }, LazyButton = { fg = p.fg, bg = p.selection },
    LazyButtonActive = { fg = p.bg, bg = p.accent, bold = true },
    MasonNormal = { link = "NormalFloat" }, MasonHeader = { fg = p.bg, bg = p.accent },
    TroubleNormal = { link = "Normal" }, TroubleNormalNC = { link = "NormalNC" },
    BlinkCmpMenu = { link = "Pmenu" }, BlinkCmpMenuBorder = { link = "FloatBorder" },
    BlinkCmpMenuSelection = { link = "PmenuSel" }, BlinkCmpLabelMatch = { fg = p.accent, bold = true },
    BlinkCmpDoc = { link = "NormalFloat" }, BlinkCmpDocBorder = { link = "FloatBorder" },
    NoiceCmdlinePopupBorder = { link = "FloatBorder" }, NoiceCmdlineIcon = { fg = p.accent },
    NoicePopupBorder = { link = "FloatBorder" },
  }
  local links = {
    ["@comment"] = "Comment", ["@string"] = "String", ["@string.escape"] = "Special",
    ["@string.regexp"] = "Special", ["@character"] = "Character", ["@number"] = "Number",
    ["@boolean"] = "Boolean", ["@constant"] = "Constant", ["@constant.builtin"] = "Constant",
    ["@variable"] = "Identifier", ["@variable.parameter"] = "Parameter",
    ["@variable.builtin"] = "Special", ["@variable.member"] = "Property",
    ["@function"] = "Function", ["@function.builtin"] = "Function", ["@function.call"] = "Function",
    ["@function.method"] = "Function", ["@function.method.call"] = "Function", ["@constructor"] = "Type", ["@type"] = "Type",
    ["@type.builtin"] = "Type", ["@keyword"] = "Keyword", ["@operator"] = "Operator",
    ["@module"] = "Type", ["@property"] = "Property", ["@attribute"] = "Special",
    ["@punctuation"] = "Delimiter", ["@tag"] = "Keyword", ["@tag.attribute"] = "Type",
    ["@tag.delimiter"] = "Delimiter", ["@markup.heading"] = "Title",
    ["@markup.link"] = "Underlined", ["@markup.raw"] = "String", ["@markup.list"] = "Special",
    ["@diff.plus"] = "GitSignsAdd", ["@diff.minus"] = "GitSignsDelete", ["@diff.delta"] = "GitSignsChange",
    ["@lsp.type.variable"] = "Identifier", ["@lsp.type.parameter"] = "Parameter",
    ["@lsp.type.property"] = "Property", ["@lsp.type.function"] = "Function",
    ["@lsp.type.method"] = "Function", ["@lsp.type.class"] = "Type", ["@lsp.type.namespace"] = "Type",
    SnacksPicker = "NormalFloat", SnacksPickerBorder = "FloatBorder", SnacksPickerTitle = "FloatTitle",
    SnacksPickerInput = "NormalFloat", SnacksPickerInputBorder = "FloatBorder",
    SnacksPickerList = "NormalFloat", SnacksPickerListBorder = "FloatBorder",
    SnacksPickerPreview = "NormalFloat", SnacksPickerPreviewBorder = "FloatBorder",
    SnacksExplorerNormal = "Normal", SnacksExplorerBorder = "WinSeparator",
  }
  for name, target in pairs(links) do groups[name] = { link = target } end
  for name, value in pairs(groups) do vim.api.nvim_set_hl(0, name, value) end
  local ansi = { "#01060e", p.red, p.green, "#f9af4f", "#53bdfa", "#fae994", "#90e1c6", p.white,
    "#686868", p.bright_red, p.bright_green, p.accent, p.blue, p.yellow, p.cyan, "#ffffff" }
  for i, color in ipairs(ansi) do vim.g["terminal_color_" .. (i - 1)] = color end
end

return M
