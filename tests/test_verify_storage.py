import errno
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import verify_storage as verify


class HardlinkProbeTests(unittest.TestCase):
    def test_probe_preserves_existing_files_and_cleans_its_own(self):
        for failure in (False, True):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                for relative in verify.DIRECTORIES:
                    (root / relative).mkdir(parents=True, exist_ok=True)
                (root / '.homelab-volume-id').write_text('test-volume\n')
                sentinel = root / 'media' / f'.hardlink-check-{os.getpid()}'
                sentinel.write_bytes(b'existing user file')
                config = root / 'test.env'
                config.write_text(f'HOST_STORAGE_PATH={root}\nVOLUME_ID=test-volume\n')
                before = set(root.rglob('*'))
                real_link = os.link
                with patch.object(sys, 'argv', ['verify', '--config', str(config)]), \
                        patch.object(verify.os, 'link', side_effect=OSError(errno.EXDEV, 'cross-device') if failure else real_link):
                    with self.assertRaises(SystemExit) as result:
                        verify.main()
                    self.assertEqual(result.exception.code, 1 if failure else 0)
                self.assertEqual(sentinel.read_bytes(), b'existing user file')
                self.assertEqual(set(root.rglob('*')), before)
