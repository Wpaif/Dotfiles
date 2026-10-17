import json
import os
import socket
import pty
import time
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / 'home/.local/bin/terminal-opacity'


class OpacityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.log = self.base / 'ipc.jsonl'
        binary = self.base / 'alacritty'
        binary.write_text('''#!/usr/bin/env python3
import json, os, sys
with open(os.environ['OPACITY_LOG'], 'a') as f:
    f.write(json.dumps(sys.argv[1:]) + '\\n')
if 'get-config' in sys.argv: print(os.environ.get('RUNTIME_CONFIG', ''))
sys.exit(int(os.environ.get('IPC_FAIL', '0')))
''')
        binary.chmod(0o755)
        self.env = dict(os.environ, PATH=f'{self.base}:{os.environ["PATH"]}',
                        HOME=str(self.base), XDG_CONFIG_HOME=str(self.base / 'config'),
                        XDG_RUNTIME_DIR=str(self.base), OPACITY_LOG=str(self.log))

    def control(self, keys, **extra):
        return subprocess.run(['bash', str(CLI), '--control', '/tmp/original.sock', '42'],
                              input=keys, text=True, capture_output=True,
                              env=dict(self.env, **extra))

    def calls(self):
        return [json.loads(line) for line in self.log.read_text().splitlines()]

    def test_left_previews_in_original_window_and_enter_keeps_value(self):
        result = self.control('\x1b[D\r')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.calls()[-1], ['msg', '--socket', '/tmp/original.sock',
                                         'config', '--window-id', '42', 'window.opacity=0.99', 'colors.transparent_background_colors=true'])

    def test_escape_restores_previous_window_opacity(self):
        self.control('\x1b[D\r')
        result = self.control('\x1b[D\x1b')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.calls()[-1][-2], 'window.opacity=0.99')

    def test_bounds_stay_between_ten_and_one_hundred_percent(self):
        self.assertEqual(self.control('\x1b[D' * 100 + '\r').returncode, 0)
        self.assertEqual(self.calls()[-1][-2], 'window.opacity=0.10')
        self.assertEqual(self.control('\x1b[C' * 100 + '\r').returncode, 0)
        self.assertEqual(self.calls()[-1][-2], 'window.opacity=1.00')

    def test_ipc_failure_is_reported(self):
        result = self.control('\x1b[D\r', IPC_FAIL='1')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Alacritty', result.stderr)

    def test_shortcut_opens_control_without_shell_window_environment(self):
        env = dict(self.env)
        env.pop('ALACRITTY_SOCKET', None)
        env.pop('ALACRITTY_WINDOW_ID', None)
        result = subprocess.run(['bash', str(CLI)], env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('--discover', self.calls()[0])

    def test_launcher_preserves_explicit_original_window(self):
        env = dict(self.env, ALACRITTY_SOCKET='/tmp/source.sock', ALACRITTY_WINDOW_ID='123')
        result = subprocess.run(['bash', str(CLI)], env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.calls()[0][-3:], ['--control', '/tmp/source.sock', '123'])

    def test_discovery_excludes_control_window_and_targets_original(self):
        candidate = Path(os.environ.get('ALACRITTY_SOCKET', '/nonexistent'))
        if not candidate.is_socket():
            candidate = self.base / 'original.sock'
            sock = socket.socket(socket.AF_UNIX)
            self.addCleanup(sock.close)
            try:
                sock.bind(str(candidate))
            except PermissionError:
                self.skipTest('Sandbox blocks Unix sockets and no existing socket is visible')
        proc = self.base / 'proc'
        for pid, window in ((100, '42'), (101, '999')):
            directory = proc / str(pid)
            directory.mkdir(parents=True)
            (directory / 'environ').write_bytes(
                f'ALACRITTY_SOCKET={candidate}\0ALACRITTY_WINDOW_ID={window}\0'.encode())
            (directory / 'cwd').symlink_to(self.base)
        script = self.base / 'control.sh'
        script.write_text(CLI.read_text().replace('/proc/[0-9]*/environ', str(proc / '[0-9]*/environ')))
        result = subprocess.run(['bash', str(script), '--discover', str(candidate)],
                                input='\x1b[D\r', capture_output=True, text=True,
                                env=dict(self.env, ALACRITTY_SOCKET=str(candidate), ALACRITTY_WINDOW_ID='999'))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.calls()[-1], ['msg', '--socket', str(candidate), 'config',
                                         '--window-id', '42', 'window.opacity=0.99', 'colors.transparent_background_colors=true'])
        # With multiple destinations, fzf returns the pressed arrow and row.
        # That first arrow must already apply a preview, before the input loop.
        other = proc / '102'
        other.mkdir()
        (other / 'environ').write_bytes(
            f'ALACRITTY_SOCKET={candidate}\0ALACRITTY_WINDOW_ID=43\0'.encode())
        (other / 'cwd').symlink_to(self.base)
        fzf = self.base / 'fzf'
        fzf.write_text("#!/bin/sh\ncat >/dev/null\nprintf 'left\\n0\\n'\n")
        fzf.chmod(0o755)
        result = subprocess.run(['bash', str(script), '--discover', str(candidate)],
                                input='\r', capture_output=True, text=True,
                                env=dict(self.env, ALACRITTY_SOCKET=str(candidate), ALACRITTY_WINDOW_ID='999',
                                         RUNTIME_CONFIG='{"window":{"opacity":0.64}}'))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('window.opacity=0.63', self.calls()[-1])
        self.assertIn(self.calls()[-1][5], ('42', '43'))

    def test_preview_is_sent_before_enter_in_a_real_terminal(self):
        master, slave = pty.openpty()
        process = subprocess.Popen(['bash', str(CLI), '--control', '/tmp/original.sock', '42'],
                                   stdin=slave, stdout=slave, stderr=slave, env=self.env)
        os.close(slave)
        try:
            deadline = time.monotonic() + 3
            while not self.log.exists() and time.monotonic() < deadline:
                time.sleep(0.02)
            os.write(master, b'\x1b[D')
            deadline = time.monotonic() + 3
            while time.monotonic() < deadline:
                if self.log.exists() and any('window.opacity=0.99' in call for call in self.calls()):
                    break
                time.sleep(0.02)
            else:
                self.fail('Arrow did not apply the preview before Enter')
            self.assertIsNone(process.poll(), 'Control should remain open during preview')
            self.assertIn('colors.transparent_background_colors=true', self.calls()[-1])
            os.write(master, b'\r')
            self.assertEqual(process.wait(timeout=3), 0)
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()
            os.close(master)

    def test_reads_actual_opacity_and_restores_background_transparency_on_cancel(self):
        result = self.control('\x1b[D\x1b', RUNTIME_CONFIG=
                              '{"window":{"opacity":0.64},"colors":{"transparent_background_colors":false}}')
        self.assertEqual(result.returncode, 0, result.stderr)
        changes = [call for call in self.calls() if 'config' in call]
        self.assertIn('window.opacity=0.63', changes[0])
        self.assertIn('colors.transparent_background_colors=true', changes[0])
        self.assertIn('window.opacity=0.64', changes[-1])
        self.assertIn('colors.transparent_background_colors=false', changes[-1])
