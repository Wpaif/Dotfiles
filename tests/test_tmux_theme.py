"""Testes do seletor com fzf real em PTY e transporte tmux simulado.

O transporte simulado permite testar cancelamento sem sockets. A sintaxe
real do tmux é verificada separadamente por tests/tmux-theme.sh.
"""
import json
import tomllib
import fcntl
import struct
import termios
import os
from pathlib import Path
import pty
import select
import shutil
import signal
import stat
import subprocess
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / 'home/.local/bin/tmux-theme'

TRANSPORT = r'''#!/usr/bin/env python3
import json, os, shlex, sys
from pathlib import Path
p = Path(os.environ['THEME_TEST_TRANSPORT'])
state = json.loads(p.read_text()) if p.exists() else {}
if os.environ.get('THEME_TEST_NO_SERVER') == '1': sys.exit(1)
valid_options = set("""status-format status-style status-left status-right
status-left-style status-right-style window-style window-active-style
window-status-current-style window-status-last-style window-status-activity-style
window-status-separator window-status-format window-status-current-format
window-status-style window-status-bell-style pane-border-lines pane-border-style
pane-active-border-style popup-border-lines popup-border-style popup-style
message-style message-command-style mode-style display-panes-colour
display-panes-active-colour clock-mode-colour status automatic-rename""".split())
exit_status = 0
a = sys.argv[1:]
if a[0] == '-S': a = a[2:]
def scope(args):
    if '-t' not in args: return state
    target = args[args.index('-t') + 1]
    kind = 'pane' if '-p' in args else 'window' if '-w' in args else 'session'
    return state.get('__locals', {}).get(kind + ':' + target, {})
def set_option(args):
    global exit_status
    data = scope(args)
    values = []
    skip = False
    for arg in args:
        if skip: skip = False; continue
        if arg == '-t': skip = True; continue
        if arg.startswith('-'): continue
        values.append(arg)
    name = values[0]
    if not name.startswith('@') and name.split('[')[0] not in valid_options:
        print('invalid option: ' + name, file=sys.stderr)
        exit_status = 1
        return
    if any('u' in arg for arg in args if arg.startswith('-')):
        for key in list(data):
            if key == name or key.startswith(name + '['): data.pop(key)
        if data is state and name == 'status-format':
            data['status-format[0]'] = 'DEFAULT'
    else:
        data[name] = values[1]
cmd, *args = a
if cmd == 'source-file':
    for line in Path(args[0]).read_text().splitlines():
        parts = shlex.split(line)
        if parts:
            if parts[0] != 'set': sys.exit('invalid tmux command: ' + line)
            set_option(parts[1:])
elif cmd == 'show':
    data = scope(args)
    name = args[-1]
    if name.startswith('-') or ('-t' in args and name == args[args.index('-t') + 1]):
        for key, value in data.items():
            if not key.startswith('__'): print(key + ' ' + shlex.quote(value))
    else:
        if name == 'status-format':
            for key, value in data.items():
                if key.startswith('status-format['): print(key + ' ' + shlex.quote(value))
            sys.exit(0)
        if name not in data: sys.exit(1)
        print(data[name] if '-gqv' in args else name + ' ' + shlex.quote(data[name]))
elif cmd == 'set':
    set_option(args)
elif cmd == 'display-message':
    if '-p' in args: print('/test/server.sock')
elif cmd in ('list-sessions', 'list-windows', 'list-panes'):
    kind = {'list-sessions': 'session', 'list-windows': 'window', 'list-panes': 'pane'}[cmd]
    for key in state.get('__locals', {}):
        if key.startswith(kind + ':'): print(key.split(':', 1)[1])
elif cmd == 'list-clients':
    print('/dev/pts/test-a\n/dev/pts/test-b')
elif cmd == 'refresh-client':
    with p.with_suffix('.redraw').open('a') as log: log.write(args[args.index('-t') + 1] + '\n')
else:
    sys.exit('unexpected command: ' + cmd)
tmp = p.with_suffix('.tmp')
tmp.write_text(json.dumps(state))
tmp.replace(p)
sys.exit(exit_status)
'''


class ThemeSelectorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        (self.base / 'bin').mkdir()
        transport = self.base / 'bin/tmux'
        transport.write_text(TRANSPORT)
        transport.chmod(0o755)
        self.themes = self.base / 'config/tmux/themes'
        shutil.copytree(ROOT / 'home/.config/tmux/themes', self.themes)
        self.env = dict(os.environ, PATH=f'{self.base}/bin:' + os.environ['PATH'],
                        HOME=str(self.base), XDG_CONFIG_HOME=str(self.base / 'config'),
                        XDG_STATE_HOME=str(self.base / 'state'), XDG_CURRENT_DESKTOP='',
                        THEME_TEST_TRANSPORT=str(self.base / 'transport.json'), TERM='xterm-256color')
        self.env.pop('TMUX_THEME_SOCKET', None)
        self.env.pop('TMUX', None)
        self.env.pop('ALACRITTY_SOCKET', None)
        self.env.pop('ALACRITTY_WINDOW_ID', None)
        self.env['XDG_RUNTIME_DIR'] = str(self.base / 'runtime')
        self.env['TMPDIR'] = str(self.base)
        (self.base / 'runtime').mkdir()
        self.alacritty = self.base / 'config/alacritty'
        self.alacritty.mkdir()
        (self.alacritty / 'alacritty.toml').write_text('[general]\nlive_config_reload=true\n')
        self.pid = None

    def tearDown(self):
        if self.pid:
            os.killpg(self.pid, signal.SIGKILL)
            os.waitpid(self.pid, 0)
            os.close(self.fd)
        self.temp.cleanup()

    def run_cli(self, *args, check=True):
        return subprocess.run([str(CLI), *args], env=self.env, capture_output=True,
                              text=True, check=check)

    def state(self):
        return json.loads((self.base / 'transport.json').read_text())

    def saved(self):
        return (self.base / 'state/tmux/theme').read_text().strip()

    def wait_for(self, predicate):
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            if select.select([self.fd], [], [], 0.04)[0]:
                try:
                    os.read(self.fd, 65536)
                except OSError:
                    pass
            if predicate():
                return
        self.fail('Tempo esgotado esperando pelo seletor')

    def open_selector(self):
        self.pid, self.fd = pty.fork()
        if self.pid == 0:
            fcntl.ioctl(1, termios.TIOCSWINSZ, struct.pack("HHHH", 24, 80, 0, 0))
            os.execve(str(CLI), [str(CLI)], self.env)
        output = b""
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if select.select([self.fd], [], [], 0.1)[0]:
                chunk = os.read(self.fd, 65536)
                output += chunk
                if b"\x1b[6n" in chunk:
                    os.write(self.fd, b"\x1b[1;1R")
                if b'Tema' in output:
                    break
        else:
            self.fail(f'fzf não exibiu o prompt: {output!r}')

    def finish(self, key):
        os.write(self.fd, key)
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            pid, status = os.waitpid(self.pid, os.WNOHANG)
            if pid:
                self.pid = None
                os.close(self.fd)
                self.assertEqual(os.waitstatus_to_exitcode(status), 0)
                return
            time.sleep(0.03)
        self.fail('Seletor não encerrou')

    def enable_alacritty_ipc_transport(self):
        fake = self.base / 'bin/alacritty'
        fake.write_text("#!/usr/bin/env python3\nimport json,os,sys\nfrom pathlib import Path\np=Path(os.environ['HOME'],'ipc.jsonl')\nwith p.open('a') as f: f.write(json.dumps(sys.argv[1:])+'\\n')\n")
        fake.chmod(0o755)
        frontend = self.base / 'runtime/Alacritty-wayland-test-1.sock'
        second = self.base / 'runtime/Alacritty-wayland-test-2.sock'
        for path in [frontend, second]:
            os.mknod(path, stat.S_IFSOCK | 0o600)
        # O socket explícito também aparece no diretório; não enviar em duplicidade.
        self.env['ALACRITTY_SOCKET'] = str(frontend)
        return [str(frontend), str(second)]

    def ipc_calls(self):
        return [json.loads(line) for line in (self.base / 'ipc.jsonl').read_text().splitlines()]

    def test_gruvbox_is_sent_to_all_running_alacritty_instances(self):
        sockets = self.enable_alacritty_ipc_transport()
        self.run_cli('--apply', 'gruvbox')
        calls = self.ipc_calls()
        self.assertEqual(len(calls), 2)
        self.assertEqual({call[call.index('--socket') + 1] for call in calls}, set(sockets))
        for call in calls:
            self.assertEqual(call[call.index('--window-id') + 1], '-1')
            options = call[call.index('-1') + 1:]
            config = tomllib.loads('\n'.join(options))
            self.assertEqual(set(config), {'colors'})
            self.assertEqual(config['colors']['primary']['background'], '#282828')
            self.assertEqual(config['colors']['primary']['foreground'], '#ebdbb2')
            self.assertEqual(config['colors']['normal']['green'], '#98971a')
            self.assertEqual(config['colors']['bright']['yellow'], '#fabd2f')
        self.assertEqual(self.saved(), 'gruvbox')

    def test_hackthebox_preserves_vivid_green_in_normal_and_bright(self):
        self.run_cli('--apply', 'hackthebox')
        colors = self.terminal_colors()
        self.assertEqual(colors['normal']['green'], '#9fef00')
        self.assertEqual(colors['bright']['green'], '#9fef00')
        self.assertEqual(colors['cursor']['cursor'], '#9fef00')

    def test_cancel_restores_palette_in_running_alacritty(self):
        self.enable_alacritty_ipc_transport()
        self.run_cli('--apply', 'hackthebox')
        self.open_selector()
        os.write(self.fd, b'\x1b[B')
        self.wait_for(lambda: self.terminal_colors()['primary']['background'] == '#1e1e2e')
        self.finish(b'\x1b')
        for call in self.ipc_calls()[-2:]:
            options = call[call.index('-1') + 1:]
            config = tomllib.loads('\n'.join(options))
            self.assertEqual(config['colors']['primary']['background'], '#141d2b')
            self.assertEqual(config['colors']['normal']['green'], '#9fef00')

    def test_missing_fragment_initializes_saved_theme_before_preview(self):
        self.enable_alacritty_ipc_transport()
        self.run_cli('--apply', 'hackthebox')
        (self.alacritty / 'theme.toml').unlink()
        self.open_selector()
        os.write(self.fd, b'\x1b[B')
        self.wait_for(lambda: (self.alacritty / 'theme.toml').exists() and self.terminal_colors()['primary']['background'] == '#1e1e2e')
        self.finish(b'\x1b')
        self.assertEqual(self.terminal_colors()['primary']['background'], '#141d2b')
        for call in self.ipc_calls()[-2:]:
            config = tomllib.loads('\n'.join(call[call.index('-1') + 1:]))
            self.assertEqual(config['colors']['normal']['green'], '#9fef00')
        self.assertEqual(self.saved(), 'hackthebox')

    def terminal_colors(self):
        return tomllib.loads((self.alacritty / 'theme.toml').read_text())['colors']

    def test_alacritty_gets_full_palette_and_keeps_its_other_settings(self):
        config = (self.alacritty / 'alacritty.toml').read_bytes()
        self.run_cli('--apply', 'dracula')
        colors = self.terminal_colors()
        self.assertEqual(colors['primary']['background'], '#282a36')
        self.assertEqual(colors['normal']['green'], '#50fa7b')
        self.assertEqual(len(colors['normal']), 8)
        self.assertEqual(len(colors['bright']), 8)
        self.assertEqual((self.alacritty / 'alacritty.toml').read_bytes(), config)
        self.assertIn('#282a36', self.state()['status-style'])

    def test_selector_escape_restores_alacritty_file_exactly(self):
        self.run_cli('--apply', 'hackthebox')
        before = (self.alacritty / 'theme.toml').read_bytes()
        self.open_selector()
        os.write(self.fd, b'\x1b[B')
        self.wait_for(lambda: self.terminal_colors()['primary']['background'] == '#1e1e2e')
        self.finish(b'\x1b')
        self.assertEqual((self.alacritty / 'theme.toml').read_bytes(), before)
        self.assertEqual(self.saved(), 'hackthebox')

    def test_selector_enter_without_any_tmux_server(self):
        self.env['THEME_TEST_NO_SERVER'] = '1'
        self.run_cli('--apply', 'hackthebox')
        self.open_selector()
        os.write(self.fd, b'\x1b[B')
        self.wait_for(lambda: self.terminal_colors()['primary']['background'] == '#1e1e2e')
        self.finish(b'\r')
        self.assertEqual(self.saved(), 'auto')
        self.assertEqual(self.terminal_colors()['primary']['background'], '#1e1e2e')

    def test_selector_escape_without_tmux_restores_terminal(self):
        self.env['THEME_TEST_NO_SERVER'] = '1'
        self.run_cli('--apply', 'hackthebox')
        before = (self.alacritty / 'theme.toml').read_bytes()
        self.open_selector()
        os.write(self.fd, b'\x1b[B')
        self.wait_for(lambda: self.terminal_colors()['primary']['background'] == '#1e1e2e')
        self.finish(b'\x1b')
        self.assertEqual((self.alacritty / 'theme.toml').read_bytes(), before)
        self.assertEqual(self.saved(), 'hackthebox')

    def test_shortcut_launches_a_separate_selector_window(self):
        launcher = ROOT / 'home/.local/bin/terminal-theme'
        self.assertTrue(launcher.is_file(), 'Launcher do Alacritty ainda não existe')
        fake = self.base / 'bin/alacritty'
        fake.write_text("#!/usr/bin/env python3\nimport json,os,sys\nfrom pathlib import Path\nPath(os.environ['HOME'],'launched.json').write_text(json.dumps(sys.argv[1:]))\n")
        fake.chmod(0o755)
        subprocess.run([str(launcher)], env=self.env, check=True)
        args = json.loads((self.base / 'launched.json').read_text())
        self.assertIn('--command', args)
        self.assertEqual(args[-1], str(self.base / '.local/bin/tmux-theme'))
        config = tomllib.loads((ROOT / 'home/.config/alacritty/alacritty.toml').read_text())
        bindings = config['keyboard']['bindings']
        self.assertTrue(any(b['key'] == 'T' and b['mods'] == 'Control|Shift' for b in bindings))
        self.assertIn('theme.toml', config['general']['import'])
        self.assertNotIn('colors', config)

    def test_applying_theme_has_no_invalid_tmux_options(self):
        result = self.run_cli('--apply', 'dracula', check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, '')
        self.assertEqual(self.saved(), 'dracula')

    def test_installed_theme_catalog_and_all_palettes(self):
        expected = {'auto', 'hackthebox', 'catppuccin-mocha', 'catppuccin-latte',
                    'dracula', 'nord', 'tokyo-night', 'gruvbox'}
        self.assertEqual(set(self.run_cli('--list').stdout.splitlines()), expected)
        backgrounds = {'hackthebox': '#141d2b', 'catppuccin-mocha': '#1e1e2e',
                       'catppuccin-latte': '#eff1f5', 'dracula': '#282a36',
                       'nord': '#2e3440', 'tokyo-night': '#1a1b26', 'gruvbox': '#282828'}
        for name, background in backgrounds.items():
            self.run_cli('--preview', name)
            self.assertIn(background, self.state()['status-style'])

    def seed_local_overrides(self):
        state = self.state()
        state['status-format[0]'] = 'OLD GLOBAL FORMAT'
        state['status-format[1]'] = 'OLD SECOND LINE'
        state['__locals'] = {
            'session:$0': {'status-style': 'fg=red', 'status-left': 'OLD',
                           'status-format[0]': 'OLD FORMAT', 'status': 'off'},
            'session:$1': {'status-right-style': 'fg=red'},
            'window:@0': {'pane-border-style': 'fg=red', 'window-status-format': 'OLD'},
            'window:@1': {'window-active-style': 'bg=red', 'automatic-rename': 'off'},
            'pane:%0': {'window-style': 'bg=red'},
        }
        (self.base / 'transport.json').write_text(json.dumps(state))
        return state

    def test_forces_existing_sessions_windows_and_panes_and_redraws_clients(self):
        self.run_cli('--apply', 'catppuccin-mocha')
        self.seed_local_overrides()
        self.run_cli('--apply', 'dracula')
        local = self.state()['__locals']
        self.assertEqual(local['session:$0'], {'status': 'off'})
        self.assertEqual(local['session:$1'], {})
        self.assertEqual(local['window:@0'], {})
        self.assertEqual(local['window:@1'], {'automatic-rename': 'off'})
        self.assertEqual(local['pane:%0'], {})
        self.assertIn('#282a36', self.state()['window-style'])
        self.assertEqual(self.state()['status-format[0]'], 'DEFAULT')
        self.assertNotIn('status-format[1]', self.state())
        redrawn = (self.base / 'transport.redraw').read_text().splitlines()
        self.assertIn('/dev/pts/test-a', redrawn)
        self.assertIn('/dev/pts/test-b', redrawn)

    def test_cancel_restores_local_overrides_and_inheritance(self):
        self.run_cli('--apply', 'catppuccin-mocha')
        before = self.seed_local_overrides()
        self.open_selector()
        os.write(self.fd, b'\x1b[B')
        self.wait_for(lambda: self.state().get('@theme') == 'auto')
        self.finish(b'\x1b')
        self.assertEqual(self.state(), before)

    def test_preview_does_not_save_and_restore_reloads_choice(self):
        self.run_cli('--apply', 'catppuccin-mocha')
        before = self.state()['status-style']
        self.run_cli('--preview', 'dracula')
        self.assertNotEqual(self.state()['status-style'], before)
        self.assertEqual(self.saved(), 'catppuccin-mocha')
        self.run_cli('--restore')
        self.assertEqual(self.state()['status-style'], before)

    def test_invalid_name_cannot_change_saved_theme(self):
        self.run_cli('--apply', 'catppuccin-latte')
        result = self.run_cli('--apply', '../invalid', check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.saved(), 'catppuccin-latte')

    def test_palette_data_is_never_executed(self):
        marker = self.base / 'executed'
        (self.themes / 'custom.theme').write_text(f'accent=$(touch {marker})\nbackground=#112233\n')
        self.run_cli('--apply', 'custom')
        self.assertFalse(marker.exists())
        self.assertIn('#112233', self.state()['status-style'])
        self.assertIn('custom', self.run_cli('--list').stdout.splitlines())

    def test_gnome_preference_takes_priority_over_inactive_omarchy(self):
        current = self.base / '.local/state/omarchy/current/theme'
        current.mkdir(parents=True)
        (current / 'colors.toml').write_text('background="#123456"\n')
        settings = self.base / 'bin/gsettings'
        settings.write_text("#!/bin/sh\nprintf '%s\\n' prefer-light\n")
        settings.chmod(0o755)
        self.env['XDG_CURRENT_DESKTOP'] = 'GNOME'
        self.run_cli('--apply', 'auto')
        self.assertIn('#eff1f5', self.state()['status-style'])
        settings.write_text("#!/bin/sh\nprintf '%s\\n' prefer-dark\n")
        self.run_cli('--refresh')
        self.assertIn('#1e1e2e', self.state()['status-style'])

    def test_auto_reads_omarchy_and_refreshes(self):
        current = self.base / '.local/state/omarchy/current/theme'
        current.mkdir(parents=True)
        colors = current / 'colors.toml'
        colors.write_text('background = "#123456"\nforeground = "#fefefe"\naccent = "#abcdef"\n')
        self.run_cli('--apply', 'auto')
        self.assertIn('#123456', self.state()['status-style'])
        colors.write_text('background = "#654321"\n')
        self.run_cli('--refresh')
        self.assertIn('#654321', self.state()['status-style'])
        self.assertEqual(self.saved(), 'auto')

    def test_escape_restores_exact_previous_visual(self):
        self.run_cli('--apply', 'catppuccin-mocha')
        before = self.state()
        self.open_selector()
        os.write(self.fd, b'\x1b[B')
        self.wait_for(lambda: self.state().get('@theme') == 'auto')
        self.finish(b'\x1b')
        self.assertEqual(self.state(), before)
        self.assertEqual(self.saved(), 'catppuccin-mocha')

    def test_mouse_wheel_previews_and_escape_cancels(self):
        self.run_cli('--apply', 'catppuccin-mocha')
        before = self.state()
        self.open_selector()
        os.write(self.fd, b'\x1b[<65;5;6M')
        self.wait_for(lambda: self.state().get('@theme') == 'auto')
        self.finish(b'\x1b')
        self.assertEqual(self.state(), before)
        self.assertEqual(self.saved(), 'catppuccin-mocha')

    def test_ctrl_c_cancels(self):
        self.run_cli('--apply', 'catppuccin-mocha')
        before = self.state()
        self.open_selector()
        os.write(self.fd, b'\x1b[B')
        self.wait_for(lambda: self.state().get('@theme') == 'auto')
        self.finish(b'\x03')
        self.assertEqual(self.state(), before)
        self.assertEqual(self.saved(), 'catppuccin-mocha')

    def test_stale_server_theme_is_not_offered_in_selector(self):
        self.run_cli('--apply', 'hackthebox')
        state = self.state()
        state['@theme'] = 'ember'
        (self.base / 'transport.json').write_text(json.dumps(state))
        self.open_selector()
        self.wait_for(lambda: self.state().get('@theme') == 'hackthebox')
        self.finish(b'\r')
        self.assertEqual(self.saved(), 'hackthebox')

    def test_enter_persists_selected_theme(self):
        self.run_cli('--apply', 'catppuccin-mocha')
        self.open_selector()
        os.write(self.fd, b'\x1b[B')
        self.wait_for(lambda: self.state().get('@theme') == 'auto')
        self.finish(b'\r')
        self.assertEqual(self.saved(), 'auto')
        self.assertEqual(self.state()['@theme'], 'auto')


if __name__ == '__main__':
    unittest.main()
