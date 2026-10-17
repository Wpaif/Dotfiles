import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import tempfile
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / 'home/.local/bin/terminal-frosted-glass'


class FrostedGlassTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.config = self.base / 'config/alacritty/alacritty.toml'
        self.config.parent.mkdir(parents=True)
        self.config.write_text('[general]\nimport=["theme.toml"]\n[window]\nopacity=0.8\ndecorations="none"\n[font]\nsize=13.0\n')
        self.env = dict(os.environ, HOME=str(self.base), XDG_CONFIG_HOME=str(self.base / 'config'),
                        XDG_STATE_HOME=str(self.base / 'state'), XDG_DATA_HOME=str(self.base / 'data'),
                        XDG_RUNTIME_DIR=str(self.base / 'runtime'), GSETTINGS_BACKEND='keyfile')
        self.env.pop('ALACRITTY_SOCKET', None)
        binaries = self.base / 'bin'
        binaries.mkdir()
        alacritty = binaries / 'alacritty'
        alacritty.write_text('#!/bin/sh\nexit 0\n')
        alacritty.chmod(0o755)
        self.env['PATH'] = f'{binaries}:{os.environ["PATH"]}'

    def test_alacritty_preset_preserves_other_preferences_and_backs_up(self):
        before = self.config.read_text()
        result = subprocess.run(['python3', str(CLI), '--alacritty-only'], env=self.env,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        config = tomllib.loads(self.config.read_text())
        self.assertEqual(config['window'], {'opacity': 0.92, 'decorations': 'none'})
        self.assertTrue(config['colors']['transparent_background_colors'])
        self.assertEqual(config['font']['size'], 13.0)
        self.assertEqual(config['general']['import'], ['theme.toml'])
        backups = list((self.base / 'state/dotfiles/backups').glob('*/alacritty.toml'))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_text(), before)

    def test_boolean_parser_does_not_change_extension_names(self):
        parse = runpy.run_path(str(CLI))['variant']
        self.assertEqual(parse("['true-theme@example.org']"), ['true-theme@example.org'])
        self.assertEqual(parse('@as []'), [])
        self.assertIs(parse('false'), False)

    @unittest.skipUnless(shutil.which('gsettings') and shutil.which('glib-compile-schemas'), 'Requires GLib')
    def test_gnome_profile_uses_real_schemas_without_changing_host_settings(self):
        extension = self.base / 'data/gnome-shell/extensions/blur-my-shell@aunetx'
        schemas = extension / 'schemas'
        schemas.mkdir(parents=True)
        (extension / 'metadata.json').write_text(json.dumps({'uuid': 'blur-my-shell@aunetx', 'shell-version': ['50']}))
        schema = 'org.gnome.shell.extensions.blur-my-shell.applications'
        definitions = {
            'enable-all': ('b', 'true'), 'whitelist': ('as', '[]'), 'static-blur': ('b', 'true'),
            'customize': ('b', 'false'), 'sigma': ('i', '30'), 'brightness': ('d', '1.0'),
            'opacity': ('i', '215'), 'dynamic-opacity': ('b', 'true'),
            'corner-radius': ('i', '15'), 'blur': ('b', 'false'),
        }
        keys = ''.join(f'<key name="{key}" type="{kind}"><default>{value}</default></key>'
                       for key, (kind, value) in definitions.items())
        (schemas / 'test.gschema.xml').write_text(
            f'<schemalist><schema id="{schema}" path="/org/gnome/shell/extensions/blur-my-shell/applications/">{keys}</schema></schemalist>')
        subprocess.run(['glib-compile-schemas', str(schemas)], check=True)
        binaries = self.base / 'bin'
        binaries.mkdir(exist_ok=True)
        for name, output in [('gnome-shell', 'GNOME Shell 50.4'), ('gdbus', '()'), ('gnome-extensions', 'enabled')]:
            path = binaries / name
            path.write_text(f'#!/bin/sh\nprintf "%s\\n" "{output}"\n')
            path.chmod(0o755)
        env = dict(self.env, PATH=f'{binaries}:{os.environ["PATH"]}')
        result = subprocess.run(['python3', str(CLI)], env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        def get(key):
            return subprocess.run(['gsettings', '--schemadir', str(schemas), 'get', schema, key],
                                  env=env, check=True, capture_output=True, text=True).stdout.strip()
        self.assertEqual(get('opacity'), '255')
        self.assertEqual(get('dynamic-opacity'), 'false')
        self.assertEqual(get('enable-all'), 'false')
        self.assertEqual(get('sigma'), '24')
        self.assertEqual(get('whitelist'), "['Alacritty', 'org.alacritty.Alacritty']")
