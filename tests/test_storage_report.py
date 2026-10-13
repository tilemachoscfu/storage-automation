import json
from pathlib import Path
import subprocess
import sys
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/docker_storage_report.py"


class ReportTests(unittest.TestCase):
    def test_mount_roots_and_children_not_similar_prefixes(self):
        mounts = [{"Source": "/srv/example", "Destination": path} for path in
                  ("/data", "/data/music", "/storage", "/storage/downloads",
                   "/database", "/storage-old", "/config")]
        text = self.report(mounts)
        for path in ("/data", "/data/music", "/storage", "/storage/downloads"):
            self.assertIn("→" + path, text)
        for path in ("/database", "/storage-old", "/config"):
            self.assertNotIn("→" + path, text)

    def test_sourceless_tmpfs(self):
        self.assertIn("tmpfs→/data/cache", self.report([
            {"Type": "tmpfs", "Destination": "/data/cache"}]))

    def test_no_relevant_mounts(self):
        self.assertIn("| - | True |", self.report([]))

    def report(self, mounts):
        row = {"Name": "/example", "HostConfig": {"NetworkMode": "bridge",
               "ReadonlyRootfs": True, "RestartPolicy": {"Name": "no"}}, "Mounts": mounts}
        return subprocess.run([sys.executable, str(SCRIPT)], input=json.dumps([row]),
                              capture_output=True, text=True, check=True).stdout
