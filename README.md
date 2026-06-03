# Mealie Liquid Glass Theme

A dark **Liquid Glass** custom theme for [Mealie](https://github.com/mealie-recipes/mealie): anthracite/black surfaces, red accents, translucent glass cards, softened borders, and cache-busted CSS injection.

## Files

- `liquid-glass.css` — the custom frontend stylesheet.
- `entrypoint-liquid-glass.sh` — container entrypoint wrapper that injects the stylesheet link into Mealie frontend HTML files before starting Mealie.
- `docker-compose.example.yml` — minimal compose snippet showing how to mount and enable the theme.

## Install with Docker Compose

Create a `theme/` directory next to your `docker-compose.yml` and copy the two theme files into it:

```bash
mkdir -p theme
cp liquid-glass.css theme/liquid-glass.css
cp entrypoint-liquid-glass.sh theme/entrypoint-liquid-glass.sh
chmod +x theme/entrypoint-liquid-glass.sh
```

Add the entrypoint and volume mounts to your Mealie service:

```yaml
services:
  mealie:
    image: ghcr.io/mealie-recipes/mealie:v3.17.0
    entrypoint: ["/theme/entrypoint-liquid-glass.sh"]
    volumes:
      - ./data:/app/data
      - ./theme/liquid-glass.css:/opt/mealie/lib/python3.12/site-packages/mealie/frontend/liquid-glass.css:ro
      - ./theme/entrypoint-liquid-glass.sh:/theme/entrypoint-liquid-glass.sh:ro
```

Then restart Mealie:

```bash
docker compose up -d
```

## Optional Mealie color variables

The CSS does most of the visual work, but these environment variables keep Mealie's built-in theme colors aligned:

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

## Cache busting

`entrypoint-liquid-glass.sh` injects:

```html
<link rel="stylesheet" href="/liquid-glass.css?v=20260603-20">
```

When you change the CSS, bump the `?v=` suffix in the script to force browsers to reload the stylesheet.

## Notes

- Tested with Mealie `v3.17.0`.
- The frontend path can change across Mealie/Python versions. If the file does not load, check the container path under `/opt/mealie/lib/python*/site-packages/mealie/frontend` and adjust the volume mount + `FRONTEND_DIR` accordingly.
