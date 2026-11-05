# STORAGE AUTOMATION

Fail-closed storage integration for a containerized media stack.

This repository documents and automates a safe pattern for connecting dedicated storage to download managers and media libraries. A volume marker prevents containers from starting on an unmounted host directory, while verification tools check paths, permissions and hardlink support before services are enabled.

The example network layout places download clients behind Gluetun and uses AirVPN as the provider. No VPN credentials, private keys, server selections, host addresses or live media paths are included.

## Data flow

```text
Jellyseerr → Sonarr / Radarr → qBittorrent → dedicated storage → Jellyfin
Lidarr → Soularr / slskd → dedicated storage → Navidrome
qBittorrent / slskd → Gluetun → AirVPN → external network
```

## Included

| Component | Purpose |
| --- | --- |
| `scripts/prepare_storage.py` | Create the directory layout and volume marker, with dry-run by default |
| `scripts/storage-mount-guard.sh` | Stop a container when the expected mounted volume is absent |
| `scripts/verify_storage.py` | Verify marker, permissions, write access and hardlink support |
| `scripts/docker_storage_report.py` | Produce a Markdown report from `docker inspect` JSON |
| `compose/storage.override.example.yml` | Example storage mounts and Gluetun network isolation |
| `config/storage.env.example` | Non-secret, portable configuration template |

## Safety model

The marker is stored on the mounted filesystem itself. Containers receive the storage mount and guard script using `create_host_path: false`. At startup, the guard compares the marker with the configured volume ID and exits before the service entrypoint when they do not match.

This avoids the common failure mode where a missing disk leaves an empty mount directory on the system drive and containers silently begin writing into it.

### When the guard refuses to start a service

Do not rerun preparation with `--apply` or create a replacement marker. If the
disk is absent, that can put a valid-looking marker on the system drive.

1. Confirm the Docker daemon and Compose project are the intended ones before
   interpreting a missing container as a missing disk.
2. On the daemon host, use the actual **host bind source**, not the container
   destination. Run `findmnt --target "$HOST_STORAGE_PATH"` with that path set
   explicitly. Compare the backing filesystem with the expected volume: an
   existing directory, or a successful lookup that returns the root filesystem,
   is not proof that the dedicated disk is mounted.
3. Only after confirming the filesystem identity, check that its existing
   `.homelab-volume-id` matches the configured ID locally. If the device or
   marker is missing or unexpected, leave the guard in place and investigate.
   Do not publish mount details or marker values.

The checks above are read-only. The separate `verify_storage.py` command
performs temporary write and hardlink probes; reserve it for a known volume.

## Quick start

```sh
git clone https://github.com/tilemachoscfu/storage-automation.git
cd storage-automation
cp config/storage.env.example config/storage.env
$EDITOR config/storage.env
```

Review the proposed layout without changing the filesystem:

```sh
python3 scripts/prepare_storage.py --config config/storage.env
```

Create the marker and directories only after reviewing the output:

```sh
sudo python3 scripts/prepare_storage.py --config config/storage.env --apply
python3 scripts/verify_storage.py --config config/storage.env
```

Adapt `compose/storage.override.example.yml` to the existing Compose project. Render the merged configuration before restarting anything:

```sh
docker compose -f compose.yml -f compose/storage.override.yml config
```

## Migration rules

- Snapshot Compose files and application configuration before integration.
- Keep existing torrent save paths and library roots unchanged.
- Apply new storage defaults only to new content.
- Use the same filesystem for download and library paths when hardlink imports are required.
- Give player services read-only storage access; grant write access only where needed.
- Validate service API connections after changing paths.
- Test the missing-volume case before unattended startup.
- Keep qBittorrent and similar clients in Gluetun's network namespace so VPN failure is fail-closed.

## Suggested path layout

```text
/storage
├── .homelab-volume-id
├── downloads
│   ├── complete
│   │   ├── lidarr
│   │   ├── radarr
│   │   └── tv-sonarr
│   └── incomplete
└── media
    ├── movies
    ├── music
    └── tv
```

## Scope

The repository provides the reusable storage and network-safety layer. Application API keys and application-specific mutations remain local because they depend on the deployed Sonarr, Radarr, Lidarr, Jellyfin, Navidrome and Jellyseerr instances.

Use only on systems you own or administer. See [SECURITY.md](SECURITY.md) before deployment.

