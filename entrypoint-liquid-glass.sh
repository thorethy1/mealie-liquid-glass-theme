#!/bin/sh
# Thin wrapper that hands off to the Python injector.
# The Python script does the actual work (auto-detect frontend dir,
# md5-based cache busting, HTML patching) so it stays maintainable.
set -eu
exec /usr/bin/env python3 "$(dirname "$0")/entrypoint-liquid-glass.py" "$@"
