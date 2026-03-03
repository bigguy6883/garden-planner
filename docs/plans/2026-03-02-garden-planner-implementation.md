# Garden Planner Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a visual garden layout planner where users place plants on a grid canvas, manage multiple plan versions, and see spacing/height warnings.

**Architecture:** Flask + SQLite backend serving a single-page HTML template with vanilla JS and HTML5 Canvas. Plant seed data in a JSON file, garden plans stored as JSON blobs in SQLite. Two views: top-down editable grid and read-only front profile.

**Tech Stack:** Python 3, Flask, SQLite, HTML5 Canvas, vanilla JS

**Security note:** Use `textContent` and safe DOM methods instead of `innerHTML` throughout the frontend. Build palette items and UI elements using `createElement` + `textContent`.

---

### Task 1: Project Scaffold and Flask App

**Files:**
- Create: `app.py`
- Create: `requirements.txt`
- Create: `templates/index.html`

**Step 1: Create requirements.txt**

```
flask
```

**Step 2: Create minimal Flask app**

Create `app.py`:

```python
from flask import Flask, render_template, request, jsonify
import sqlite3
import json
import os

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(__file__), "garden.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS gardens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            width INTEGER NOT NULL,
            depth INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            garden_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            grid_data TEXT NOT NULL DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (garden_id) REFERENCES gardens(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS custom_plants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            label TEXT NOT NULL,
            color TEXT NOT NULL,
            spacing INTEGER NOT NULL DEFAULT 1,
            height TEXT NOT NULL DEFAULT 'medium',
            category TEXT NOT NULL DEFAULT 'vegetable'
        );
    """)
    conn.commit()
    conn.close()


@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5001, debug=True)
```

**Step 3: Create minimal index.html**

Create `templates/index.html` with just a heading "Garden Planner" to verify the app serves.

**Step 4: Run and verify**

Run: `cd ~/garden-planner && python3 app.py`
Expected: Server starts on port 5001, visiting http://localhost:5001 shows "Garden Planner"

**Step 5: Commit**

```bash
git add app.py requirements.txt templates/index.html
git commit -m "feat: scaffold Flask app with database schema"
```

---

### Task 2: Plant Seed Data

**Files:**
- Create: `plants.json`
- Modify: `app.py` — add endpoint to serve plant data

**Step 1: Create plants.json**

Create `plants.json` with vegetables and perennial flowers. Each plant has: name, label (2-3 chars), color (hex), spacing (number of cells as a square — 1 means 1x1, 4 means 2x2, 9 means 3x3), height ("short"=under 1ft, "medium"=1-3ft, "tall"=3ft+), category ("vegetable" or "flower").

Include ~20 vegetables (tomato, pepper, lettuce, carrot, basil, cucumber, zucchini, pole bean, pea, onion, garlic, kale, spinach, radish, squash, corn, broccoli, cauliflower, eggplant, okra) and ~15 perennial flowers (coneflower, black-eyed susan, lavender, hosta, daylily, sedum, russian sage, bee balm, coral bells, catmint, blanket flower, peony, iris, shasta daisy, phlox).

**Step 2: Add plant API endpoints to app.py**

Add two routes:

`GET /api/plants` — loads plants.json, appends any custom_plants rows from DB, returns JSON array.

`POST /api/plants` — inserts a new row into custom_plants table, returns the new ID.

**Step 3: Run and verify**

Run: `curl http://localhost:5001/api/plants`
Expected: JSON array of ~35 plants

**Step 4: Commit**

```bash
git add plants.json app.py
git commit -m "feat: add plant seed data and API endpoints"
```

---

### Task 3: Garden and Plan CRUD API

**Files:**
- Modify: `app.py` — add garden and plan CRUD endpoints

**Step 1: Add garden CRUD routes**

- `GET /api/gardens` — list all gardens ordered by created_at DESC
- `POST /api/gardens` — create garden with name, width, depth
- `DELETE /api/gardens/<id>` — delete garden and its plans

**Step 2: Add plan CRUD routes**

- `GET /api/gardens/<id>/plans` — list plans for a garden
- `POST /api/gardens/<id>/plans` — create plan with name and empty grid_data
- `GET /api/plans/<id>` — get single plan with parsed grid_data JSON
- `PUT /api/plans/<id>` — update plan name and grid_data
- `DELETE /api/plans/<id>` — delete plan
- `POST /api/plans/<id>/duplicate` — copy plan with new name

**Step 3: Verify with curl**

```bash
curl -X POST http://localhost:5001/api/gardens -H 'Content-Type: application/json' -d '{"name":"Test Bed","width":8,"depth":4}'
curl http://localhost:5001/api/gardens
curl -X POST http://localhost:5001/api/gardens/1/plans -H 'Content-Type: application/json' -d '{"name":"Test Plan v1","grid_data":{}}'
curl http://localhost:5001/api/gardens/1/plans
```

Expected: Each returns correct JSON

**Step 4: Commit**

```bash
git add app.py
git commit -m "feat: add garden and plan CRUD API with duplicate support"
```

---

### Task 4: Frontend Layout — Sidebar + Canvas Container

**Files:**
- Modify: `templates/index.html` — build the full page layout

**Step 1: Build the HTML structure with inline CSS**

Layout structure:
- **Top bar** (full width): garden selector dropdown, plan selector dropdown, New Garden / New Plan / Duplicate / Delete buttons, Front View toggle button
- **Left sidebar** (220px fixed): "Plants" heading, plant palette container div, "+ Custom Plant" button
- **Main area** (fills remaining): canvas element, absolutely-positioned tooltip div (hidden by default)

Use flexbox layout. Dark-ish comfortable color scheme. All CSS in a `<style>` tag.

Build all DOM elements using `document.createElement()` and `textContent` — no innerHTML.

**Step 2: Verify layout renders**

Refresh browser at http://localhost:5001
Expected: Top bar with dropdowns/buttons, left sidebar with "Plants" heading, main area with canvas

**Step 3: Commit**

```bash
git add templates/index.html
git commit -m "feat: add frontend layout with sidebar, topbar, and canvas"
```

---

### Task 5: Plant Palette and Selection

**Files:**
- Modify: `templates/index.html` — add JS to load plants and handle selection

**Step 1: Add JavaScript to load and render plant palette**

In a `<script>` tag at the bottom of index.html:

- `loadPlants()` — fetch `/api/plants`, store in `plants` array, call `renderPalette()`
- `renderPalette()` — clear palette div, group plants by category (Vegetables / Flowers), for each plant create a div with a colored swatch span (set `style.background`) and name text (using `textContent`). Clicking a plant item sets `selectedPlant` and re-renders palette with highlight class.
- Use `document.createElement()` for all DOM construction — no innerHTML.

**Step 2: Verify**

Click plants in sidebar — selected plant highlights with a border or background change.

**Step 3: Commit**

```bash
git add templates/index.html
git commit -m "feat: add plant palette with category grouping and selection"
```

---

### Task 6: Garden/Plan Management UI

**Files:**
- Modify: `templates/index.html` — wire up garden/plan dropdowns and buttons

**Step 1: Add garden/plan management JavaScript**

State variables: `gardens`, `currentGarden`, `plansList`, `currentPlan`

Functions:
- `loadGardens()` — fetch `/api/gardens`, populate garden-select dropdown, auto-select first
- `selectGarden(id)` — set currentGarden, fetch its plans, populate plan-select, auto-select first
- `selectPlan(id)` — fetch `/api/plans/{id}`, set currentPlan, call `drawGrid()`

**Step 2: Add event listeners for buttons**

- "New Garden" — `prompt()` for name, width, depth -> POST /api/gardens -> reload
- "New Plan" — `prompt()` for name -> POST /api/gardens/{id}/plans -> reload
- "Duplicate" — `prompt()` for new name -> POST /api/plans/{id}/duplicate -> reload
- "Delete" — `confirm()` -> DELETE /api/plans/{id} -> reload
- Garden select `onchange` -> `selectGarden()`
- Plan select `onchange` -> `selectPlan()`

**Step 3: Verify**

Create a garden "Test Bed 8x4", create a plan "v1", duplicate it, delete the copy.

**Step 4: Commit**

```bash
git add templates/index.html
git commit -m "feat: wire up garden and plan management UI"
```

---

### Task 7: Top-Down Canvas Grid — Drawing and Plant Placement

**Files:**
- Modify: `templates/index.html` — implement canvas grid drawing and click-to-place

This is the core task.

**Step 1: Implement grid drawing**

Constants: `CELL_SIZE = 50` (pixels per sq ft). State: `offsetX`, `offsetY`, `scale`, `gridData` (object keyed by "row,col"), `viewMode` ('topdown' or 'front').

`drawGrid()` function:
1. Size canvas to container dimensions
2. Apply translate(offsetX, offsetY) and scale(scale)
3. Fill garden background rect
4. Draw placed plants — colored rectangles with white text labels (using `fillText`)
5. Call `checkWarnings()` and draw warning overlays (red for spacing, orange for visibility)
6. Draw grid lines
7. Draw row/column number labels along edges

**Step 2: Implement click-to-place**

Canvas click handler:
1. Convert mouse coords to grid row/col accounting for offset and scale
2. If cell is occupied: remove it (and all cells sharing same origin for multi-cell plants)
3. If cell is empty and a plant is selected: place plant. For multi-cell plants (spacing 4 = 2x2, spacing 9 = 3x3), fill the footprint. Each cell stores: name, label, color, spacing, height, origin (the top-left cell key)
4. Redraw grid and auto-save

**Step 3: Implement auto-save**

Debounced (500ms) PUT to `/api/plans/{id}` with current gridData after any change.

**Step 4: Verify**

Select a plant, click on the grid, see colored square appear. Click again to remove. Reload page — data persists.

**Step 5: Commit**

```bash
git add templates/index.html
git commit -m "feat: implement top-down canvas grid with plant placement and auto-save"
```

---

### Task 8: Zoom, Pan, and Hover Tooltip

**Files:**
- Modify: `templates/index.html` — add zoom/pan/tooltip handlers

**Step 1: Implement scroll-to-zoom**

Canvas `wheel` handler: multiply scale by 0.9 or 1.1 based on deltaY direction. Clamp scale between 0.3 and 3. Redraw.

**Step 2: Implement drag-to-pan**

- `mousedown` with no plant selected (or middle button): start panning, record start position
- `mousemove` while panning: update offsetX/offsetY, redraw
- `mouseup` / `mouseleave`: stop panning

**Step 3: Implement hover tooltip**

On `mousemove` (when not panning): convert coords to grid cell, if occupied show tooltip div positioned near cursor with plant name, height, and spacing info (using `textContent`). Hide tooltip when hovering empty space or leaving canvas.

**Step 4: Implement keyboard delete**

Track `selectedCell`. When clicking an occupied cell without a plant selected, mark it as selectedCell (highlight it). On Delete/Backspace keydown: remove all cells sharing the same origin as selectedCell, redraw, auto-save.

**Step 5: Verify**

Scroll to zoom, drag empty space to pan, hover plants for tooltip, select and delete with keyboard.

**Step 6: Commit**

```bash
git add templates/index.html
git commit -m "feat: add zoom, pan, hover tooltip, and keyboard delete"
```

---

### Task 9: Spacing and Visibility Warnings

**Files:**
- Modify: `templates/index.html` — implement `checkWarnings()` function

**Step 1: Implement warning logic**

`checkWarnings(gridData, width, depth)` returns array of `{cell, type, msg}`:

**Spacing check:** Group cells by origin. For each plant group, if cell count is less than expected spacing (plant was clipped by grid edge), add a 'spacing' warning for each cell in that group.

**Visibility check:** For each column, walk from front row (bottom, highest row index) to back row (top, row 0). Track the maximum height rank seen so far (short=1, medium=2, tall=3). If a cell's height rank is less than the max seen in front of it, add a 'visibility' warning — it's blocked by a taller plant in front.

**Step 2: Verify**

Place a tall plant near the front (bottom), short plant behind it (above) — orange warning on the short plant. Place a 2x2 plant near the grid edge so its footprint gets clipped — red warning.

**Step 3: Commit**

```bash
git add templates/index.html
git commit -m "feat: add spacing and visibility warning overlays"
```

---

### Task 10: Front Profile View

**Files:**
- Modify: `templates/index.html` — implement front view drawing

**Step 1: Implement front view renderer**

`drawFrontView()` function:
1. Size canvas to container
2. Define height in pixels: short=30, medium=70, tall=120
3. Set baseY = ground line near bottom of canvas
4. Draw ground line (brown horizontal line)
5. For each column, iterate rows from back (row 0) to front (row depth-1):
   - Draw colored rectangle: x = col * CELL_SIZE, height = heightPx for plant's height category, y = baseY - height - slight depth offset
   - Back rows slightly transparent (globalAlpha 0.7), front rows fully opaque
   - White text label centered on each bar
6. Draw column number labels below ground line

**Step 2: Wire up toggle button**

"Front View" button click: toggle `viewMode` between 'topdown' and 'front'. Update button text. Call `drawGrid()` or `drawFrontView()` accordingly. Disable click-to-place when in front view.

**Step 3: Verify**

Place plants of different heights, toggle to front view — see height profile with taller bars in back, shorter in front. Toggle back to top-down view — editing works normally.

**Step 4: Commit**

```bash
git add templates/index.html
git commit -m "feat: implement front profile view with height visualization"
```

---

### Task 11: Custom Plant Dialog

**Files:**
- Modify: `templates/index.html` — add modal dialog for adding custom plants

**Step 1: Add modal HTML and CSS**

A simple modal overlay (built with `createElement`, no innerHTML) with form fields:
- Name (text input)
- Label (text input, maxlength 3)
- Color (color picker input)
- Spacing (select: 1 sq ft, 4 sq ft / 2x2, 9 sq ft / 3x3)
- Height (select: short, medium, tall)
- Category (select: vegetable, flower)
- Save and Cancel buttons

**Step 2: Wire up "+" button and form submit**

"+ Custom Plant" button shows modal. Save button: POST to `/api/plants` with form data, reload plant list, close modal. Cancel button: close modal.

**Step 3: Verify**

Click "+", fill in "Marigold" with orange color, save. See it appear in palette under correct category. Place it on grid.

**Step 4: Commit**

```bash
git add templates/index.html
git commit -m "feat: add custom plant dialog"
```

---

### Task 12: Systemd Service and Final Polish

**Files:**
- Create: `garden-planner.service`
- Create: `CLAUDE.md`

**Step 1: Create systemd service file**

```ini
[Unit]
Description=Garden Planner
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/garden-planner
ExecStart=/usr/bin/python3 /home/pi/garden-planner/app.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

**Step 2: Create CLAUDE.md**

Project context doc with: run command, service name, DB location, plant data location, architecture overview.

**Step 3: Install and start service**

```bash
sudo cp garden-planner.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable garden-planner
sudo systemctl start garden-planner
sudo systemctl status garden-planner
```

Expected: Active (running)

**Step 4: Commit**

```bash
git add garden-planner.service CLAUDE.md
git commit -m "feat: add systemd service and project docs"
```

---

## Task Summary

| Task | Description | Depends On |
|------|-------------|------------|
| 1 | Project scaffold, Flask app, DB schema | — |
| 2 | Plant seed data (JSON) + API | 1 |
| 3 | Garden/Plan CRUD API | 1 |
| 4 | Frontend layout (HTML/CSS) | 1 |
| 5 | Plant palette + selection | 2, 4 |
| 6 | Garden/plan management UI | 3, 4 |
| 7 | Top-down canvas grid + placement | 5, 6 |
| 8 | Zoom, pan, tooltip, delete | 7 |
| 9 | Spacing + visibility warnings | 7 |
| 10 | Front profile view | 7 |
| 11 | Custom plant dialog | 5 |
| 12 | Systemd service + polish | all |
