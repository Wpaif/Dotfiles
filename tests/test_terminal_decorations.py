import json
import os
from pathlib import Path
import subprocess
import tempfile
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / 'home/.local/bin/terminal-decorations'


class DecorationsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.config = self.base / 'config/alacritty/alacritty.toml'
        self.config.parent.mkdir(parents=True)
        self.config.write_text('[general]\nimport=["theme.toml"]\n[window]\ndecorations="full"\nopacity=0.83\n[font]\nsize=13.0\n')
        binary = self.base / 'alacritty'
        binary.write_text('''#!/usr/bin/env python3
import json, os, sys
with open(os.environ['DECORATIONS_LOG'], 'a') as f:
    f.write(json.dumps(sys.argv[1:]) + '\\n')
''')
        binary.chmod(0o755)
        self.log = self.base / 'calls'
        self.env = dict(os.environ, PATH=f'{self.base}:{os.environ["PATH"]}',
                        XDG_CONFIG_HOME=str(self.base / 'config'), XDG_STATE_HOME=str(self.base / 'state'),
                        DECORATIONS_LOG=str(self.log))

    def run_cli(self, *args):
        return subprocess.run(['bash', str(CLI), *args], env=self.env,
                              capture_output=True, text=True)

    def test_toggle_preserves_other_settings_and_can_restore_title_bar(self):
        for expected in ('none', 'full'):
            result = self.run_cli('toggle')
            self.assertEqual(result.returncode, 0, result.stderr)
            config = tomllib.loads(self.config.read_text())
            self.assertEqual(config['window'], {'decorations': expected, 'opacity': 0.83})
            self.assertEqual(config['font']['size'], 13.0)
            self.assertEqual(config['general']['import'], ['theme.toml'])
        self.assertFalse(self.log.exists())

    def test_shortcut_opens_new_window_with_explicit_decoration_override(self):
        result = self.run_cli('toggle', '--new-window')
        self.assertEqual(result.returncode, 0, result.stderr)
        call = json.loads(self.log.read_text().splitlines()[-1])
        self.assertIn('--option', call)
        self.assertIn('window.decorations="none"', call)
        self.assertNotIn('config', call)

    def test_inserts_missing_window_table(self):
        self.config.write_text('[font]\nsize=14.0\n')
        result = self.run_cli('hide')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(tomllib.loads(self.config.read_text()),
                         {'font': {'size': 14.0}, 'window': {'decorations': 'none'}})

    def test_invalid_action_preserves_configuration(self):
        before = self.config.read_bytes()
        result = self.run_cli('invalid')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.config.read_bytes(), before)
