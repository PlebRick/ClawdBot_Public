#!/bin/bash
# Re-extract cookies after Rick re-logs in on Chrome.
# Usage: ./refresh-cookies.sh [domain_group...]
# Called by Clawd after Rick confirms re-login.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Refreshing cookies..."
"$SCRIPT_DIR/extract-cookies.sh" "$@"
STATUS=$?

if [ $STATUS -eq 0 ]; then
    echo "✅ Cookies refreshed successfully"
else
    echo "❌ Cookie refresh failed (exit $STATUS)"
fi

exit $STATUS
