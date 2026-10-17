-- Somente apresentação: mantém atalhos, fontes de dados, LSP e ferramentas.
local p = require("dotfiles.ayu").palette
local function mode(color)
  return { a = { fg = p.bg, bg = color, gui = "bold" }, b = { fg = p.fg, bg = p.surface }, c = { fg = p.fg, bg = p.bg } }
end

return {
  { "LazyVim/LazyVim", opts = { colorscheme = "ayu-dark" } },
  {
    "nvim-lualine/lualine.nvim",
    opts = function(_, opts)
      opts.options = opts.options or {}
      opts.options.component_separators = { left = "│", right = "│" }
      opts.options.section_separators = { left = "", right = "" }
      opts.options.theme = {
        normal = mode(p.accent), insert = mode(p.green), visual = mode(p.blue),
        replace = mode(p.red), command = mode(p.cyan), terminal = mode(p.green),
        inactive = { a = { fg = p.muted, bg = p.bg }, b = { fg = p.muted, bg = p.bg }, c = { fg = p.muted, bg = p.bg } },
      }
    end,
  },
  {
    "akinsho/bufferline.nvim",
    opts = function(_, opts)
      opts.options = opts.options or {}
      opts.options.separator_style = { "│", "│" }
      opts.options.indicator = { icon = "▎", style = "icon" }
      opts.highlights = vim.tbl_deep_extend("force", opts.highlights or {}, {
        fill = { bg = p.bg }, background = { fg = p.muted, bg = p.bg },
        buffer_visible = { fg = p.fg, bg = p.bg }, buffer_selected = { fg = p.accent, bg = p.surface, bold = true, italic = false },
        separator = { fg = p.border, bg = p.bg }, separator_visible = { fg = p.border, bg = p.bg },
        separator_selected = { fg = p.border, bg = p.surface }, indicator_selected = { fg = p.accent, bg = p.surface },
        modified = { fg = p.accent, bg = p.bg }, modified_selected = { fg = p.accent, bg = p.surface },
      })
    end,
  },
  { "folke/which-key.nvim", opts = { win = { border = "single" } } },
  {
    "folke/noice.nvim",
    opts = { views = { cmdline_popup = { border = { style = "single" } }, popup = { border = { style = "single" } } } },
  },
  {
    "folke/snacks.nvim",
    opts = {
      styles = { float = { border = "single" }, input = { border = "single" }, notification = { border = "single" } },
      dashboard = { preset = { header = "󰀫  LazyVim  /  Ayu Dark" } },
    },
  },
}
