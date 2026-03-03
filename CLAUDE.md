# Garden Planner

## Quick Reference
- **Run:** `python3 app.py` (serves on port 5003)
- **Service:** `garden-planner` (garden-planner.service)
- **Database:** `garden.db` (SQLite, auto-created on startup)
- **Plant data:** `plants.json` (seed data, ~35 plants)

## Architecture
Flask + SQLite backend serving a single-page HTML template with vanilla JS and HTML5 Canvas.

- `app.py` — Flask app with all API routes
- `plants.json` — seed plant data (vegetables and perennial flowers)
- `templates/index.html` — single-page app with all CSS/JS inline
- `garden.db` — SQLite database (gardens, plans, custom_plants tables)

## API Endpoints
- `GET /` — serve the SPA
- `GET/POST /api/plants` — list all plants / add custom plant
- `GET/POST /api/gardens` — list / create gardens
- `DELETE /api/gardens/<id>` — delete garden
- `GET/POST /api/gardens/<id>/plans` — list / create plans
- `GET/PUT/DELETE /api/plans/<id>` — get / update / delete plan
- `POST /api/plans/<id>/duplicate` — duplicate a plan

## Features
- Visual garden layout on HTML5 Canvas grid (1 cell = 1 sq ft)
- Plant palette with 20 vegetables + 15 perennial flowers
- Multi-cell plants (1x1, 2x2, 3x3 footprints)
- Multiple gardens and plan versions with duplicate support
- Spacing warnings (red) when plants are clipped by grid edge
- Visibility warnings (orange) when short plants are behind tall ones
- Front profile view showing plant heights
- Zoom (scroll), pan (drag), hover tooltips
- Custom plant creation dialog
- Auto-save (debounced 500ms)
