#!/usr/bin/env python3
"""Mealie Liquid Glass theme injector.

Auto-discovers Mealie's frontend static directory, mounts the bundled
liquid-glass.css (already placed alongside this script by the volume mount),
injects a cache-busted <link> into every HTML file, then hands off to
Mealie's original entrypoint (/app/run.sh).

Usage (as container entrypoint):
    /theme/entrypoint-liquid-glass.sh

Environment variables:
    LIQUID_GLASS_CSS    Path to the CSS file (default: alongside this script).
    LIQUID_GLASS_LINK_ID  Optional id for the injected <link> (default: liquid-glass-theme).
    LIQUID_GLASS_LOG    Set to "0" to silence informational output.

Exit codes:
    0  on success (CSS injected OR Mealie started without injection)
    1  on hard failure (entrypoint not found, etc.)
"""

from __future__ import annotations

import glob
import hashlib
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

MEALIE_RUN = "/app/run.sh"
CSS_DEFAULT_NAME = "liquid-glass.css"
LINK_ID = "liquid-glass-theme"
LINK_RE = re.compile(
    # Match every legacy + current variant of our injected link:
    #   - with or without id="liquid-glass-theme"
    #   - any query token (date-stamped or md5)
    #   - <link ...> with or without trailing slash
    r'<link\s+rel="stylesheet"\s+href="/liquid-glass\.css\?v=[^"]*"(?:\s+id="liquid-glass-theme")?\s*/?>',
    re.IGNORECASE,
)


def log(msg: str) -> None:
    if os.environ.get("LIQUID_GLASS_LOG", "1") != "0":
        print(f"[liquid-glass] {msg}", flush=True)


def find_frontend_dir() -> Path | None:
    """Locate Mealie's frontend static dir across known layouts."""

    # 1. STATIC_FILES env override (used by the Nix package, dev setups, ...).
    static_files = os.environ.get("STATIC_FILES", "").strip()
    if static_files and Path(static_files, "index.html").is_file():
        return Path(static_files)

    # 2. The default wheel layout under the active Python interpreter's venv.
    #    Works for any Python version, any virtualenv location.
    try:
        import sysconfig  # local import: only needed at startup

        sp = sysconfig.get_paths().get("purelib")
        if sp:
            candidate = Path(sp) / "mealie" / "frontend"
            if (candidate / "index.html").is_file():
                return candidate
    except Exception:
        pass

    # 3. Hardcoded venv path (matches mealie-recipes/mealie Dockerfile).
    for pattern in (
        "/opt/mealie/lib/python*/site-packages/mealie/frontend",
        "/usr/lib/python*/dist-packages/mealie/frontend",
        "/usr/local/lib/python*/site-packages/mealie/frontend",
    ):
        matches = sorted(glob.glob(pattern))
        for m in matches:
            if Path(m, "index.html").is_file():
                return Path(m)

    # 4. Final fallback: any "mealie/frontend" under any site-packages we can find.
    for sp_root in glob.glob("/opt/mealie/lib/python*/site-packages"):
        candidate = Path(sp_root) / "mealie" / "frontend"
        if (candidate / "index.html").is_file():
            return candidate

    return None


def find_css() -> Path | None:
    """Find the liquid-glass.css file. Prefer the env var, then sit alongside us."""
    env = os.environ.get("LIQUID_GLASS_CSS", "").strip()
    if env and Path(env).is_file():
        return Path(env)
    here = Path(__file__).resolve().parent / CSS_DEFAULT_NAME
    return here if here.is_file() else None


def cache_bust_token(css_path: Path) -> str:
    """Short, stable token derived from the CSS file contents."""
    h = hashlib.md5()
    with css_path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()[:10]


def inject_into_html(html_path: Path, link_tag: str) -> bool:
    """Replace any existing liquid-glass <link> with the new one, right before </head>.

    Returns True if the file was modified.
    """
    try:
        original = html_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        original = html_path.read_text(encoding="latin-1")

    # Strip every previous liquid-glass link, even from older versions of this script.
    cleaned = LINK_RE.sub("", original)

    if "</head>" not in cleaned:
        return False

    new = cleaned.replace("</head>", f"{link_tag}\n</head>", 1)

    # Idempotent: bail out if nothing actually changed.
    if new == original:
        return False

    html_path.write_text(new, encoding="utf-8")
    return True


def main() -> int:
    css = find_css()
    if not css:
        log("ERROR: liquid-glass.css not found. Mount it next to this script or set LIQUID_GLASS_CSS.")
        return 1

    frontend = find_frontend_dir()
    if not frontend:
        log("WARNING: could not locate Mealie's frontend dir; skipping CSS injection. Mealie will still start.")
    else:
        token = cache_bust_token(css)
        link_tag = (
            f'<link rel="stylesheet" href="/liquid-glass.css?v={token}" '
            f'id="{LINK_ID}">'
        )

        # Make sure the CSS file is reachable at /liquid-glass.css, regardless
        # of where the user mounted their CSS volume. We do this by *also*
        # dropping a copy next to the frontend dir's index.html (where Mealie
        # serves static assets from). The cache-buster token takes care of
        # the "which one wins" race.
        served = frontend / CSS_DEFAULT_NAME
        try:
            shutil.copyfile(css, served)
            log(f"copied {css} -> {served}")
        except OSError as e:
            log(f"WARNING: could not copy CSS into frontend dir: {e}")

        html_files = list(frontend.rglob("*.html"))
        patched = 0
        for html in html_files:
            if inject_into_html(html, link_tag):
                patched += 1
        log(f"injected link into {patched}/{len(html_files)} HTML file(s) under {frontend}")

    if not Path(MEALIE_RUN).is_file():
        log(f"ERROR: Mealie entrypoint not found at {MEALIE_RUN}")
        return 1

    log(f"handing off to {MEALIE_RUN}")
    # Replace this process with Mealie. execvp preserves pid 1 behaviour.
    try:
        os.execvp(MEALIE_RUN, [MEALIE_RUN, *sys.argv[1:]])
    except OSError as e:
        log(f"ERROR: failed to exec {MEALIE_RUN}: {e}")
        return 1
    return 0  # unreachable


if __name__ == "__main__":
    sys.exit(main())
