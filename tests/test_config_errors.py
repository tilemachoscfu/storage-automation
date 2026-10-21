from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'


class ConfigErrorTests(unittest.TestCase):
    def test_cli_errors_locate_but_do_not_echo_invalid_values(self):
        with tempfile.TemporaryDirectory() as temporary:
            config = Path(temporary) / 'test.env'
            private_value = 'synthetic-sensitive-value'
            config.write_text('# comment\n\n' + private_value + '\n')
            for script in ('prepare_storage.py', 'verify_storage.py'):
                with self.subTest(script=script):
                    result = subprocess.run(
                        [sys.executable, str(SCRIPTS / script), '--config', str(config)],
                        capture_output=True, text=True)
                    self.assertNotEqual(result.returncode, 0)
                    output = result.stdout + result.stderr
                    self.assertIn('line 3: expected KEY=VALUE', output)
                    self.assertNotIn(private_value, output)
