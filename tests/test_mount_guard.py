import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


GUARD = Path(__file__).resolve().parents[1] / 'scripts/storage-mount-guard.sh'


class MountGuardTests(unittest.TestCase):
    def invoke(self, root, volume_id):
        env = dict(os.environ, STORAGE_PATH=str(root))
        env.pop('VOLUME_ID', None)
        if volume_id is not None:
            env['VOLUME_ID'] = volume_id
        return subprocess.run(
            ['sh', str(GUARD), sys.executable, '-c',
             'import pathlib,sys; pathlib.Path(sys.argv[1]).write_text(sys.argv[2]); sys.exit(23)',
             str(root / 'executed'), 'argument with spaces'],
            env=env, capture_output=True, text=True)

    def test_invalid_volume_never_executes_command(self):
        for marker, expected in ((None, 'expected'), ('wrong', 'expected'),
                                 ('', 'expected'), ('expected', None), ('expected', '')):
            with self.subTest(marker=marker, expected=expected), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                if marker is not None:
                    (root / '.homelab-volume-id').write_text(marker)
                result = self.invoke(root, expected)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse((root / 'executed').exists())

    def test_valid_volume_preserves_arguments_and_exit_status(self):
        with tempfile.TemporaryDirectory(prefix='guard test ') as tmp:
            root = Path(tmp)
            (root / '.homelab-volume-id').write_text('expected\n')
            result = self.invoke(root, 'expected')
            self.assertEqual(result.returncode, 23, result.stderr)
            self.assertEqual((root / 'executed').read_text(), 'argument with spaces')
