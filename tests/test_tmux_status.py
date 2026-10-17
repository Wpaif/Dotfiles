import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class StatusTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.power = self.root / 'power'
        self.power.mkdir()
        self.proc = self.root / 'stat'
        self.proc.write_text('cpu 100 0 100 800 0 0 0 0 0 0\n')
        self.script = self.root / 'tmux-status'
        source = (ROOT / 'home/.local/bin/tmux-status').read_text()
        self.script.write_text(source.replace('/sys/class/power_supply', str(self.power))
                               .replace('/proc/stat', str(self.proc)))
        self.env = dict(os.environ, XDG_STATE_HOME=str(self.root / 'state'))

    def run_status(self, segment):
        return subprocess.run(['sh', str(self.script), segment], env=self.env,
                              check=True, capture_output=True, text=True).stdout.strip()

    def battery(self, name, capacity, status):
        directory = self.power / name
        directory.mkdir()
        (directory / 'type').write_text('Battery\n')
        (directory / 'capacity').write_text(f'{capacity}\n')
        (directory / 'status').write_text(f'{status}\n')

    def test_battery_shows_charge_and_charging(self):
        self.battery('BAT0', 73, 'Charging')
        self.assertEqual(self.run_status('battery'), '󰂄 73%')

    def test_battery_shows_low_charge(self):
        self.battery('BAT1', 12, 'Discharging')
        self.assertEqual(self.run_status('battery'), '󰂎 12%')

    def test_no_battery_produces_no_segment(self):
        self.assertEqual(self.run_status('battery'), '')

    def test_cpu_uses_difference_between_samples(self):
        self.assertEqual(self.run_status('cpu'), ' --')
        self.proc.write_text('cpu 130 0 120 850 0 0 0 0 0 0\n')
        self.assertEqual(self.run_status('cpu'), ' 50%')
