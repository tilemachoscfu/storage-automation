# Security notes

Never commit AirVPN credentials, WireGuard private keys, OpenVPN profiles, Arr API keys, Jellyfin tokens, qBittorrent passwords, real volume identifiers or host inventories.

Before restarting services:

1. Confirm the storage mount using `findmnt`.
2. Run the verifier as the same UID/GID used by write-capable containers.
3. Render and inspect the merged Compose configuration.
4. Confirm download clients use `network_mode: service:gluetun` and do not publish their own ports.
5. Confirm Gluetun reports a healthy tunnel and the expected public egress IP.
6. Stop the storage mount in a controlled test and confirm protected containers fail closed.

Report vulnerabilities through GitHub private security reporting rather than a public issue.

