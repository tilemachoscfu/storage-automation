#!/bin/sh
set -eu

: "${STORAGE_PATH:=/storage}"
: "${VOLUME_ID:?set VOLUME_ID}"

marker="$STORAGE_PATH/.homelab-volume-id"
actual=$(cat "$marker" 2>/dev/null) || {
    echo "required storage volume is unavailable" >&2
    exit 1
}

if [ "$actual" != "$VOLUME_ID" ]; then
    echo "unexpected storage volume" >&2
    exit 1
fi

exec "$@"

