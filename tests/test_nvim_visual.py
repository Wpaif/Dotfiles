import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which('nvim'), 'Neovim is required for visual integration validation')
class NeovimVisualTests(unittest.TestCase):
    def test_real_colorscheme_and_visual_overrides_preserve_editor_behavior(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            script = root / 'verify.lua'
            script.write_text('''
vim.opt.rtp:prepend(vim.env.VISUAL_ROOT .. "/home/.config/nvim")
vim.o.shiftwidth = 3
vim.g.autoformat = false
vim.keymap.set("n", "<leader>ff", "<cmd>echo 'original'<cr>")
local mapping = vim.fn.maparg("<leader>ff", "n")
vim.cmd.colorscheme("ayu-dark")
assert(vim.g.colors_name == "ayu-dark")
assert(vim.api.nvim_get_hl(0, { name = "Normal" }).bg == 0x07090d)
assert(vim.api.nvim_get_hl(0, { name = "String" }).fg == 0x9de34f)
assert(vim.api.nvim_get_hl(0, { name = "DiagnosticError" }).fg == 0xff6670)
assert(vim.api.nvim_get_hl(0, { name = "WinSeparator" }).fg == 0x27303c)
assert(vim.o.shiftwidth == 3 and vim.g.autoformat == false)
assert(vim.fn.maparg("<leader>ff", "n") == mapping)
local specs = require("plugins.visual")
for _, spec in ipairs(specs) do
  if spec[1] == "nvim-lualine/lualine.nvim" then
    local opts = { options = {}, sections = { lualine_c = { "filename", "diagnostics" } } }
    spec.opts(nil, opts)
    assert(vim.deep_equal(opts.sections.lualine_c, { "filename", "diagnostics" }))
    assert(opts.options.theme.normal.a.bg == "#ffb454")
  elseif spec[1] == "akinsho/bufferline.nvim" then
    local close = function() end
    local opts = { options = { close_command = close, diagnostics = "nvim_lsp" } }
    spec.opts(nil, opts)
    assert(opts.options.close_command == close and opts.options.diagnostics == "nvim_lsp")
    assert(opts.highlights.buffer_selected.bg == "#10141c")
  end
end
vim.cmd("qa!")
''')
            env = dict(os.environ, VISUAL_ROOT=str(ROOT), XDG_STATE_HOME=str(root / 'state'),
                       XDG_CACHE_HOME=str(root / 'cache'))
            result = subprocess.run(['nvim', '--headless', '-u', 'NONE', '-c', f'lua dofile("{script}")'],
                                    env=env, capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn('Error', result.stderr)
