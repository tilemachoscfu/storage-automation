#!/usr/bin/env python3
"""Render storage and network information from `docker inspect` JSON."""

from __future__ import annotations

import json
import sys


def main() -> None:
    containers = json.load(sys.stdin)
    print("| Container | Network mode | Storage mounts | Read-only | Restart |")
    print("| --- | --- | --- | --- | --- |")
    for container in containers:
        host = container["HostConfig"]
        mounts = [
            f"{mount['Source']}→{mount['Destination']}"
            for mount in container.get("Mounts", [])
            if mount["Destination"].startswith(("/storage", "/data"))
        ]
        print(
            f"| {container['Name'].lstrip('/')} | {host['NetworkMode']} | "
            f"{'; '.join(mounts) or '-'} | {host['ReadonlyRootfs']} | "
            f"{host['RestartPolicy']['Name']} |"
        )


if __name__ == "__main__":
    main()

