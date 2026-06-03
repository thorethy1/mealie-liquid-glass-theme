#!/bin/sh
set -eu

FRONTEND_DIR="/opt/mealie/lib/python3.12/site-packages/mealie/frontend"
CSS_LINK='<link rel="stylesheet" href="/liquid-glass.css?v=20260603-20">'

if [ -d "$FRONTEND_DIR" ]; then
  find "$FRONTEND_DIR" -type f -name '*.html' | while read -r HTML; do
    # Remove old injected cache-busted link if present, then add the current one.
    sed -i 's#<link rel="stylesheet" href="/liquid-glass.css?v=[^"]*">##g' "$HTML"
    sed -i "s#</head>#$CSS_LINK</head>#" "$HTML"
  done
fi

exec /app/run.sh "$@"
