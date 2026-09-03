# Mealie Liquid Glass Theme

A dark **Liquid Glass** custom theme for [Mealie](https://github.com/mealie-recipes/mealie):
anthracite/black surfaces, red accents, translucent glass cards, softened borders,
and cache-busted CSS injection.

## Pics

<img width="1320" height="2250" alt="IMG_1196" src="https://github.com/user-attachments/assets/aa382696-3e49-4473-bc98-b2b6ce14dd1f" />
<img width="1320" height="2253" alt="IMG_1198" src="https://github.com/user-attachments/assets/5020f6f8-9625-4907-8a73-27eb3f74b0dc" />
<img width="1320" height="2505" alt="IMG_1199" src="https://github.com/user-attachments/assets/4a6f9e96-917b-4ef9-98f8-3b981d37f076" />
<img width="1320" height="2509" alt="IMG_1200" src="https://github.com/user-attachments/assets/390d925f-13ca-47b7-ba01-bd7c870d3457" />
<img width="1320" height="2524" alt="IMG_1201" src="https://github.com/user-attachments/assets/1f2b45eb-839f-46fd-b011-d235745f20d4" />

## Files

- `liquid-glass.css` — the custom frontend stylesheet.
- `entrypoint-liquid-glass.py` — Python injector: auto-discovers Mealie's frontend
  directory, injects the CSS link into every HTML file, computes a content-based
  cache-bust token, then hands off to Mealie's own entrypoint.
- `entrypoint-liquid-glass.sh` — a 4-line shell wrapper that exec's the Python
  injector. Kept as the documented entrypoint so the mount path stays simple.
- `docker-compose.example.yml` — minimal compose snippet showing how to mount
  and enable the theme.

## Quick start (Docker Compose)

Create a `theme/` directory next to your `docker-compose.yml` and copy the two
entrypoint files plus the CSS into it:

```bash
mkdir -p theme
cp liquid-glass.css theme/liquid-glass.css
cp entrypoint-liquid-glass.py theme/entrypoint-liquid-glass.py
cp entrypoint-liquid-glass.sh theme/entrypoint-liquid-glass.sh
chmod +x theme/entrypoint-liquid-glass.sh theme/entrypoint-liquid-glass.py
```

Add the entrypoint and two volume mounts to your Mealie service:

```yaml
services:
  mealie:
    image: ghcr.io/mealie-recipes/mealie:latest   # or pin to a known tag
    container_name: mealie
    restart: unless-stopped
    entrypoint: ["/theme/entrypoint-liquid-glass.sh"]
    volumes:
      - ./data:/app/data
      - ./theme/liquid-glass.css:/theme/liquid-glass.css:ro
      - ./theme/entrypoint-liquid-glass.sh:/theme/entrypoint-liquid-glass.sh:ro
      - ./theme/entrypoint-liquid-glass.py:/theme/entrypoint-liquid-glass.py:ro
    ports:
      - "9000:9000"
```

Then restart:

```bash
docker compose up -d
```

That's it — no Python version-specific paths, no manual cache-bust bumps.

## What the injector does

1. **Auto-detects Mealie's frontend directory.** It searches, in order:
   - the `STATIC_FILES` env var (used by some packaged installs)
   - the running interpreter's `site-packages` (always correct inside the
     container)
   - common venv layouts under `/opt/mealie/lib/python*/site-packages/mealie/frontend`
2. **Copies `liquid-glass.css` next to the frontend's `index.html`** so Mealie's
   static-file server can serve it at `/liquid-glass.css`.
3. **Strips every previously injected link** (including legacy date-stamped
   ones from older versions of this theme) and injects a fresh one into every
   HTML file:

   ```html
   <link rel="stylesheet" href="/liquid-glass.css?v=<md5-of-css>" id="liquid-glass-theme">
   ```

4. **Hands off** to `/app/run.sh` (Mealie's own entrypoint) with `execvp`,
   so the injector becomes pid 1's child and signal handling works correctly.

## Cache busting

The `?v=` suffix is the first 10 hex chars of the md5 of the CSS file contents.
Whenever you edit `liquid-glass.css`, every Mealie HTML file gets a new link
with a new token on the next container start — no manual bumping required.

## Optional: align Mealie's theme variables

The CSS does most of the visual work. Set these env vars on the Mealie service
to keep Vuetify's runtime colors consistent with the theme:

```env
THEME_LIGHT_PRIMARY=DC2626
THEME_LIGHT_ACCENT=EF4444
THEME_LIGHT_SECONDARY=1F2937
THEME_LIGHT_SUCCESS=22C55E
THEME_LIGHT_INFO=94A3B8
THEME_LIGHT_WARNING=F59E0B
THEME_LIGHT_ERROR=F43F5E
THEME_DARK_PRIMARY=DC2626
THEME_DARK_ACCENT=F87171
THEME_DARK_SECONDARY=030712
THEME_DARK_SUCCESS=22C55E
THEME_DARK_INFO=94A3B8
THEME_DARK_WARNING=F59E0B
THEME_DARK_ERROR=FB7185
```

## Compatibility

- **Tested against** Mealie `v3.17.x` and the rolling `latest` tag.
- **Python version**: the injector picks up any `python3.*` under the venv, so
  it survives Python-version bumps inside the container.
- **Mealie's frontend layout**: as long as `mealie/frontend/index.html` exists
  somewhere inside the container (the default wheel layout), the injector
  finds it. If Mealie ever ships pre-bundled static files at a totally new
  path, set `STATIC_FILES=/that/path` and it'll use that.

## Troubleshooting

- **Theme not applied**: check `docker logs mealie` for lines prefixed with
  `[liquid-glass]`. A `WARNING: could not locate Mealie's frontend dir`
  usually means a non-standard install — try setting `STATIC_FILES`.
- **Old, cached theme in the browser**: hard-reload (Ctrl+Shift+R). The
  md5-based `?v=` should keep this from being needed across restarts, but a
  stale Service Worker (Mealie ships a PWA) can ignore it.
- **Silence the injector logs** for a tidier startup: set
  `LIQUID_GLASS_LOG=0`.

## Notes

- The injector runs once at container start and `exec`s into Mealie; it does
  not stay resident.
- Only the CSS file is required at runtime — the Python/sh wrappers are only
  used on the host before the container starts.
