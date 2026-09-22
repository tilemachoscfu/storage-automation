#!/usr/bin/env python3
"""Prepare a media-storage layout. Dry-run unless --apply is supplied."""

from __future__ import annotations

import argparse
import os
from pathlib import Path


DIRECTORIES = (
    "downloads/complete/lidarr",
    "downloads/complete/radarr",
    "downloads/complete/tv-sonarr",
    "downloads/incomplete",
    "media/movies",
    "media/music",
    "media/tv",
)


def read_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        key, separator, value = line.partition("=")
        if not separator:
            raise ValueError(f"invalid configuration line: {raw_line}")
        values[key.strip()] = value.strip()
    return values


def require(values: dict[str, str], name: str) -> str:
    value = values.get(name, "")
    if not value or "CHANGE_ME" in value:
        raise ValueError(f"set {name} in the configuration file")
    return value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    values = read_env(args.config)
    root = Path(require(values, "HOST_STORAGE_PATH")).resolve()
    volume_id = require(values, "VOLUME_ID")
    uid = int(values.get("OWNER_UID", "1000"))
    gid = int(values.get("OWNER_GID", "1000"))
    mode = int(values.get("DIRECTORY_MODE", "2770"), 8)

    print(f"mode={'APPLY' if args.apply else 'DRY-RUN'} root={root}")
    for relative in DIRECTORIES:
        target = root / relative
        print(f"directory {target} mode={mode:o} owner={uid}:{gid}")
        if args.apply:
            target.mkdir(parents=True, exist_ok=True)
            target.chmod(mode)
            os.chown(target, uid, gid)

    marker = root / ".homelab-volume-id"
    print(f"marker {marker}")
    if args.apply:
        marker.write_text(volume_id + "\n", encoding="utf-8")
        marker.chmod(0o640)
        os.chown(marker, uid, gid)


if __name__ == "__main__":
    main()

