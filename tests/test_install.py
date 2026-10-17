"""Instalação real em diretórios temporários; sem pacotes, rede ou sessão gráfica."""
import os
import json
from pathlib import Path
import subprocess
import tempfile
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
INSTALL = ROOT / 'install.sh'


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='dotfiles install ')
        self.base = Path(self.temp.name)
        self.target = self.base / 'nova home'
        self.env = dict(os.environ, XDG_RUNTIME_DIR=str(self.base / 'runtime'), TMPDIR=str(self.base))
        self.env.pop('ALACRITTY_SOCKET', None)
        self.env.pop('TMUX', None)

    def tearDown(self):
        self.temp.cleanup()

    def install(self, *args, check=True):
        self.assertTrue(INSTALL.is_file(), 'install.sh ainda não existe')
        return subprocess.run(['bash', str(INSTALL), '--target', str(self.target), *args],
                              cwd='/tmp', env=self.env, capture_output=True, text=True, check=check)

    def test_dry_run_creates_nothing(self):
        result = self.install('--dry-run', '--bootstrap', '--frosted-glass')
        self.assertFalse(self.target.exists())
        self.assertIn('SIMULAÇÃO', result.stdout)
        self.assertIn('vidro fosco', result.stdout)

    def test_new_install_defaults_to_current_visual_and_includes_all_controls(self):
        self.install()
        self.assertEqual((self.target / '.local/state/tmux/theme').read_text().strip(), 'ayu-minimal')
        config = tomllib.loads((self.target / '.config/alacritty/alacritty.toml').read_text())
        self.assertEqual(config['window']['opacity'], 0.92)
        self.assertEqual(config['window']['decorations'], 'none')
        bindings = {binding['key']: binding for binding in config['keyboard']['bindings']}
        self.assertTrue({'T', 'O', 'D'} <= bindings.keys())
        self.assertNotIn('--new-window', bindings['D']['command']['args'][-1])
        palette = tomllib.loads((self.target / '.config/alacritty/theme.toml').read_text())['colors']
        self.assertEqual(palette['primary']['background'], '#07090d')
        self.assertEqual(palette['normal']['green'], '#9ccc42')
        for helper in ('terminal-theme', 'terminal-opacity', 'terminal-decorations', 'terminal-frosted-glass'):
            self.assertTrue(os.access(self.target / '.local/bin' / helper, os.X_OK))

    def test_frosted_glass_rejects_alternate_home_without_writing(self):
        result = self.install('--frosted-glass', check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('--target', result.stderr)
        self.assertFalse(self.target.exists())

    def test_frosted_glass_requires_gnome_before_installing(self):
        env = dict(self.env, HOME=str(self.target), XDG_CURRENT_DESKTOP='KDE')
        result = subprocess.run(['bash', str(INSTALL), '--frosted-glass'], env=env,
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('GNOME', result.stderr)
        self.assertFalse(self.target.exists())

    def test_frosted_glass_is_applied_after_installing_files_with_correct_xdg_paths(self):
        import sys
        commands = self.base / 'profile-bin'
        commands.mkdir()
        python = commands / 'python3'
        python.write_text('''#!/bin/sh
if [ "$1" = -c ]; then exec "$REAL_PYTHON" "$@"; fi
test -f "$XDG_CONFIG_HOME/alacritty/alacritty.toml" || exit 1
test -f "$XDG_CONFIG_HOME/nvim/lua/plugins/visual.lua" || exit 1
printf '%s\\n' "$1" "$XDG_CONFIG_HOME" "$XDG_STATE_HOME" "$XDG_DATA_HOME" > "$PROFILE_LOG"
''')
        python.chmod(0o755)
        env = dict(self.env, HOME=str(self.target), XDG_CURRENT_DESKTOP='GNOME',
                   XDG_CONFIG_HOME=str(self.target / '.config'), XDG_STATE_HOME=str(self.target / '.local/state'),
                   XDG_DATA_HOME=str(self.target / '.local/share'), REAL_PYTHON=sys.executable,
                   PROFILE_LOG=str(self.base / 'profile.log'), PATH=f'{commands}:{self.env["PATH"]}')
        # Missing GNOME binaries are transport fixtures; no desktop calls occur.
        for name in ('gnome-shell', 'gnome-extensions', 'gsettings', 'gdbus', 'glib-compile-schemas'):
            binary = commands / name
            binary.write_text('#!/bin/sh\nexit 1\n')
            binary.chmod(0o755)
        result = subprocess.run(['bash', str(INSTALL), '--frosted-glass'], env=env,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        log = (self.base / 'profile.log').read_text().splitlines()
        self.assertEqual(log, [str(self.target / '.local/bin/terminal-frosted-glass'),
                               env['XDG_CONFIG_HOME'], env['XDG_STATE_HOME'], env['XDG_DATA_HOME']])

    def test_fresh_install_includes_configs_helpers_and_selected_palette(self):
        self.install('--theme', 'gruvbox')
        for file in ['.zshrc', '.bashrc', '.tmux.conf', '.config/starship.toml',
                     '.config/helix/config.toml', '.local/bin/terminal-theme', '.local/bin/tmux-theme']:
            self.assertTrue((self.target / file).is_file(), file)
        self.assertTrue(os.access(self.target / '.local/bin/tmux-theme', os.X_OK))
        self.assertEqual((self.target / '.local/state/tmux/theme').read_text().strip(), 'gruvbox')
        colors = tomllib.loads((self.target / '.config/alacritty/theme.toml').read_text())['colors']
        self.assertEqual(colors['primary']['background'], '#282828')
        self.assertEqual(colors['normal']['green'], '#98971a')
        self.assertNotIn('/home/wilian', (self.target / '.zshrc').read_text())

    def test_existing_files_are_backed_up_and_unrelated_files_remain(self):
        self.target.mkdir()
        (self.target / '.zshrc').write_text('minha configuração anterior\n')
        untouched = self.target / '.config/outro-app/config'
        untouched.parent.mkdir(parents=True)
        untouched.write_text('preservar')
        keymaps = self.target / '.config/nvim/lua/config/keymaps.lua'
        keymaps.parent.mkdir(parents=True)
        keymaps.write_text('-- meus atalhos\n')
        self.install()
        backups = list((self.target / '.local/state/dotfiles/backups').glob('*/home/.zshrc'))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_text(), 'minha configuração anterior\n')
        self.assertEqual(untouched.read_text(), 'preservar')
        self.assertEqual(keymaps.read_text(), '-- meus atalhos\n')
        self.assertTrue((self.target / '.config/nvim/lua/plugins/visual.lua').is_file())

    def test_rerunning_keeps_saved_theme_and_makes_no_extra_backup(self):
        self.install('--theme', 'gruvbox')
        before = sorted(str(p) for p in self.target.rglob('*'))
        self.install()
        self.assertEqual(before, sorted(str(p) for p in self.target.rglob('*')))
        self.assertEqual((self.target / '.local/state/tmux/theme').read_text().strip(), 'gruvbox')

    def test_symlink_component_is_backed_up_without_changing_its_target(self):
        outside = self.base / 'antigo-alacritty'
        outside.mkdir()
        (outside / 'alacritty.toml').write_text('antigo')
        config = self.target / '.config'
        config.mkdir(parents=True)
        (config / 'alacritty').symlink_to(outside, target_is_directory=True)
        self.install()
        self.assertFalse((config / 'alacritty').is_symlink())
        self.assertEqual((outside / 'alacritty.toml').read_text(), 'antigo')
        backups = list((self.target / '.local/state/dotfiles/backups').glob('*/config/alacritty'))
        self.assertEqual(len(backups), 1)
        self.assertTrue(backups[0].is_symlink())

    def test_invalid_theme_fails_before_writing_anything(self):
        result = self.install('--theme', '../invalido', check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.target.exists())

    def test_linked_parent_is_rejected_before_installing(self):
        outside = self.base / 'config-externa'
        outside.mkdir()
        self.target.mkdir()
        (self.target / '.config').symlink_to(outside, target_is_directory=True)
        result = self.install(check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(list(outside.iterdir()), [])
        self.assertFalse((self.target / '.zshrc').exists())

    def test_xdg_directories_are_used_for_normal_install(self):
        self.assertTrue(INSTALL.is_file(), 'install.sh ainda não existe')
        env = dict(self.env, HOME=str(self.target), XDG_CONFIG_HOME=str(self.base / 'config'),
                   XDG_STATE_HOME=str(self.base / 'state'), XDG_DATA_HOME=str(self.base / 'share'))
        subprocess.run(['bash', str(INSTALL)], cwd='/tmp', env=env, capture_output=True, text=True, check=True)
        self.assertTrue((self.base / 'config/alacritty/theme.toml').is_file())
        self.assertTrue((self.base / 'state/tmux/theme').is_file())
        self.assertFalse((self.target / '.config').exists())

    def test_zsh_can_load_without_optional_programs(self):
        import shutil
        zsh = shutil.which('zsh')
        if not zsh:
            self.skipTest('Zsh não está instalado')
        self.install()
        empty = self.base / 'empty-bin'
        empty.mkdir()
        env = dict(self.env, HOME=str(self.target), PATH=str(empty), ZSH=str(self.target / '.oh-my-zsh'))
        result = subprocess.run([zsh, '-dfc', 'source "$1"; print READY', '-', str(self.target / '.zshrc')],
                                env=env, capture_output=True, text=True, check=True)
        self.assertEqual(result.stdout, 'READY\n')
        self.assertEqual(result.stderr, '')

    def test_clipboard_chooses_wayland_x11_or_terminal(self):
        commands = self.base / 'commands'
        commands.mkdir()
        for name in ['wl-copy', 'xclip', 'tmux']:
            p = commands / name
            p.write_text('#!/bin/sh\nprintf "%s\\n" "$0" "$@" > "$COPY_LOG"\n/bin/cat > "$COPY_TEXT"\n')
            p.chmod(0o755)
        for wayland, display, expected in [('wayland-0', ':0', 'wl-copy'), ('', ':0', 'xclip'), ('', '', 'tmux')]:
            env = dict(self.env, PATH=str(commands), WAYLAND_DISPLAY=wayland, DISPLAY=display,
                       COPY_LOG=str(self.base / 'copy-log'), COPY_TEXT=str(self.base / 'copy-text'))
            subprocess.run([str(ROOT / 'home/.local/bin/tmux-copy')], input='texto copiado\n',
                           text=True, env=env, check=True)
            self.assertTrue((self.base / 'copy-log').read_text().splitlines()[0].endswith('/' + expected))
            self.assertEqual((self.base / 'copy-text').read_text(), 'texto copiado\n')

    def test_editor_accepts_hx_binary(self):
        commands = self.base / 'editor-bin'
        commands.mkdir()
        hx = commands / 'hx'
        hx.write_text('#!/bin/sh\nprintf "hx:%s\\n" "$1"\n')
        hx.chmod(0o755)
        result = subprocess.run([str(ROOT / 'home/.local/bin/dotfiles-editor'), 'arquivo.c'],
                                env=dict(self.env, PATH=str(commands)), capture_output=True, text=True, check=True)
        self.assertEqual(result.stdout, 'hx:arquivo.c\n')

    def mock_manjaro_bootstrap(self, fail_packages=False):
        commands = self.base / 'manjaro-bin'
        commands.mkdir()
        transport = commands / 'bootstrap-tool'
        transport.write_text(r'''#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
name = Path(sys.argv[0]).name
args = sys.argv[1:]
with Path(os.environ['BOOTSTRAP_LOG']).open('a') as log:
    log.write(json.dumps([name, *args]) + '\n')
if name == 'sudo':
    os.execvp(args[0], args)
elif name == 'pacman':
    sys.exit(int(os.environ.get('BOOTSTRAP_PACKAGE_FAILURE', '0')))
elif name == 'git':
    assert args[:3] == ['clone', '--depth', '1'], args
    destination = Path(args[-1])
    destination.mkdir(parents=True, exist_ok=True)
    (destination / '.git').mkdir()
    if 'ohmyzsh/ohmyzsh' in args[-2]:
        (destination / 'oh-my-zsh.sh').write_text('# fixture do framework\n')
    else:
        plugin = args[-2].rsplit('/', 1)[-1].removesuffix('.git')
        (destination / (plugin + '.zsh')).write_text('# fixture do plugin\n')
elif name == 'fc-list':
    print('JetBrainsMono Nerd Font Mono')
elif name in ('curl', 'wget'):
    sys.exit('O teste Manjaro não deve acessar a rede')
else:
    sys.exit('Comando inesperado: ' + name)
''')
        transport.chmod(0o755)
        for name in ['sudo', 'pacman', 'git', 'fc-list', 'curl', 'wget']:
            (commands / name).symlink_to(transport)
        self.env['PATH'] = str(commands) + ':' + self.env['PATH']
        self.env['BOOTSTRAP_LOG'] = str(self.base / 'bootstrap.jsonl')
        self.env['BOOTSTRAP_PACKAGE_FAILURE'] = '1' if fail_packages else '0'

    def test_manjaro_bootstrap_runs_pacman_and_installs_all_components(self):
        self.mock_manjaro_bootstrap()
        self.install('--bootstrap', '--theme', 'gruvbox')
        calls = [json.loads(line) for line in (self.base / 'bootstrap.jsonl').read_text().splitlines()]
        package_calls = [call for call in calls if call[0] == 'pacman']
        self.assertEqual(len(package_calls), 1)
        self.assertEqual(package_calls[0][1:3], ['-Syu', '--needed'])
        for package in ['zsh', 'alacritty', 'tmux', 'fzf', 'starship', 'helix', 'clang', 'ttf-jetbrains-mono-nerd']:
            self.assertIn(package, package_calls[0])
        clone_calls = [call for call in calls if call[0] == 'git']
        self.assertEqual({call[-2] for call in clone_calls}, {
            'https://github.com/ohmyzsh/ohmyzsh.git',
            'https://github.com/zsh-users/zsh-autosuggestions.git',
            'https://github.com/zsh-users/zsh-syntax-highlighting.git'})
        self.assertFalse(any(call[0] in {'curl', 'wget'} for call in calls))
        self.assertTrue((self.target / '.oh-my-zsh/oh-my-zsh.sh').is_file())
        self.assertTrue((self.target / '.local/bin/tmux-theme').is_file())
        self.assertEqual((self.target / '.local/state/tmux/theme').read_text().strip(), 'gruvbox')
        self.assertEqual(tomllib.loads((self.target / '.config/alacritty/alacritty.toml').read_text())['font']['normal']['family'],
                         'JetBrainsMono Nerd Font Mono')

    def test_manjaro_pacman_failure_does_not_replace_existing_config(self):
        self.mock_manjaro_bootstrap(fail_packages=True)
        self.target.mkdir()
        old = self.target / '.zshrc'
        old.write_text('configuração anterior\n')
        result = self.install('--bootstrap', check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(old.read_text(), 'configuração anterior\n')
        self.assertFalse((self.target / '.config/alacritty/alacritty.toml').exists())
        self.assertFalse((self.target / '.oh-my-zsh').exists())

    def test_export_palette_does_not_touch_the_running_environment(self):
        env = dict(self.env, XDG_CONFIG_HOME=str(ROOT / 'home/.config'), XDG_STATE_HOME=str(self.base / 'state'))
        result = subprocess.run([str(ROOT / 'home/.local/bin/tmux-theme'), '--export-alacritty', 'gruvbox'],
                                env=env, capture_output=True, text=True, check=True)
        self.assertEqual(tomllib.loads(result.stdout)['colors']['primary']['background'], '#282828')
        self.assertFalse((self.base / 'state').exists())


if __name__ == '__main__':
    unittest.main()
