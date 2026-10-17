import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class FloatPositionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.state = self.directory / 'state.json'
        self.state.write_text(json.dumps({'@float_client': 'outer'}))
        tmux = self.directory / 'tmux'
        # Only the transport is replaced: run the real shell script and persist
        # its options between invocations. Real sockets are denied in sandbox.
        tmux.write_text('''#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
p = Path(os.environ['FLOAT_STATE'])
s = json.loads(p.read_text())
a = sys.argv[1:]
if a[0] == 'show': print(s.get(a[-1], ''))
elif a[0] == 'set': s[a[-2]] = a[-1]
elif a[0] == 'display': print(120 if a[-1] == '#{client_width}' else 50)
elif a[0] == 'display-popup': s['popup'] = a
elif a[0] not in ('has-session', 'detach-client'): sys.exit(2)
p.write_text(json.dumps(s))
''')
        tmux.chmod(0o755)
        self.env = dict(os.environ, PATH=f'{self.directory}:{os.environ["PATH"]}',
                        FLOAT_STATE=str(self.state))

    def run_float(self, *args):
        subprocess.run([str(ROOT / 'home/.local/bin/tmux-float'), *args],
                       env=self.env, check=True, capture_output=True, text=True)
        return json.loads(self.state.read_text())

    def geometry(self, state):
        args = state['popup']
        return tuple(int(args[args.index(flag) + 1])
                     for flag in ('-x', '-y', '-w', '-h'))

    def test_initial_popup_is_centered_using_bottom_edge_coordinate(self):
        state = self.run_float('toggle', 'outer', 'main', '/tmp')
        self.assertEqual(self.geometry(state), (12, 45, 96, 40))

    def test_movement_reaches_all_edges_and_can_return_from_bottom(self):
        self.run_float('toggle', 'outer', 'main', '/tmp')
        state = self.run_float('move', '999', '999', 'inner')
        self.assertEqual(self.geometry(state), (24, 50, 96, 40))
        state = self.run_float('move', '0', '-2', 'inner')
        self.assertEqual(self.geometry(state), (24, 48, 96, 40))
        state = self.run_float('move', '-999', '-999', 'inner')
        self.assertEqual(self.geometry(state), (0, 40, 96, 40))

    def test_resizing_at_bottom_keeps_popup_inside_screen(self):
        self.run_float('toggle', 'outer', 'main', '/tmp')
        self.run_float('move', '999', '999', 'inner')
        state = self.run_float('size', '10', '10', 'inner')
        self.assertEqual(self.geometry(state), (12, 50, 108, 45))
