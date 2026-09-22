#!/usr/bin/env python3
"""Verify marker, layout, write access and hardlink support."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import tempfile

from prepare_storage import DIRECTORIES, read_env, require


def result(name: str, passed: bool, detail: str) -> bool:
    print(f"{'PASS' if passed else 'FAIL'}  {name:<16} {detail}")
    return passed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()

    values = read_env(args.config)
    root = Path(require(values, "HOST_STORAGE_PATH")).resolve()
    volume_id = require(values, "VOLUME_ID")
    checks: list[bool] = []

    marker = root / ".homelab-volume-id"
    actual = marker.read_text(encoding="utf-8").strip() if marker.is_file() else ""
    checks.append(result("volume marker", actual == volume_id, str(marker)))

    missing = [str(root / relative) for relative in DIRECTORIES if not (root / relative).is_dir()]
    checks.append(result("directory layout", not missing, ", ".join(missing) or "complete"))

    downloads = root / "downloads/complete"
    library = root / "media"
    writable = os.access(downloads, os.W_OK) and os.access(library, os.W_OK)
    checks.append(result("write access", writable, f"uid={os.geteuid()} gid={os.getegid()}"))

    hardlinks = False
    if writable:
        with tempfile.TemporaryDirectory(dir=downloads) as temporary:
            source = Path(temporary) / "source"
            target = library / f".hardlink-check-{os.getpid()}"
            try:
                source.write_bytes(b"storage-check")
                os.link(source, target)
                hardlinks = source.stat().st_ino == target.stat().st_ino
            finally:
                target.unlink(missing_ok=True)
    checks.append(result("hardlinks", hardlinks, "downloads → media"))

    raise SystemExit(0 if all(checks) else 1)


if __name__ == "__main__":
    main()

