#!/bin/bash
# Extract Chrome cookies for web-scout skill
# Usage: ./extract-cookies.sh [domain_group...]
# Requires GNOME Keyring access (D-Bus session bus)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export DBUS_SESSION_BUS_ADDRESS="${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/$(id -u)/bus}"

exec python3 "$SCRIPT_DIR/extract-cookies.py" "$@"
