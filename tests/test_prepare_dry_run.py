import contextlib
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import prepare_storage as prepare


class DryRunTests(unittest.TestCase):
    def invoke(self, config):
        with patch.object(sys, "argv", ["prepare", "--config", str(config)]), \
                patch.object(prepare.os, "chown") as chown, \
                patch.object(Path, "chmod") as chmod, \
                contextlib.redirect_stdout(io.StringIO()) as output:
            prepare.main()
            chown.assert_not_called()
            chmod.assert_not_called()
            self.assertIn("mode=DRY-RUN", output.getvalue())

    def test_missing_root_is_not_created(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "absent-storage"
            config = Path(directory) / "config.env"
            config.write_text(f"HOST_STORAGE_PATH={root}\nVOLUME_ID=test-volume\n")
            self.invoke(config)
            self.assertFalse(root.exists())
            self.assertEqual(list(Path(directory).iterdir()), [config])

    def test_existing_files_modes_and_marker_remain_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "storage"
            root.mkdir()
            for relative in prepare.DIRECTORIES:
                path = root / relative
                path.mkdir(parents=True, exist_ok=True)
                path.chmod(0o750)
            marker = root / ".homelab-volume-id"
            marker.write_bytes(b"existing-volume\n")
            sentinel = root / "media/movies/existing.txt"
            sentinel.write_bytes(b"preserve user data")
            sentinel.chmod(0o600)
            config = Path(directory) / "config.env"
            config.write_text(f"HOST_STORAGE_PATH={root}\nVOLUME_ID=different-volume\nDIRECTORY_MODE=2770\n")

            def snapshot():
                return {p.relative_to(root): (p.stat().st_mode, p.stat().st_uid,
                        p.stat().st_gid, p.stat().st_mtime_ns,
                        p.read_bytes() if p.is_file() else None)
                        for p in [root, *root.rglob("*")]}

            before = snapshot()
            self.invoke(config)
            self.assertEqual(snapshot(), before)

    def test_missing_volume_id_fails_without_creating_root(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "absent-storage"
            config = Path(directory) / "config.env"
            config.write_text(f"HOST_STORAGE_PATH={root}\n")
            with self.assertRaisesRegex(ValueError, "VOLUME_ID"):
                self.invoke(config)
            self.assertFalse(root.exists())
