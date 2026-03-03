# Garden Planner — Design Document

**Date:** 2026-03-02

## Problem

A visual tool to plan garden layouts iteratively — place plants on a grid, rearrange freely, save multiple versions, and try different arrangements.

## Architecture

- Flask + SQLite backend on homelab (same pattern as baby tracker, meeting notes)
- HTML5 Canvas frontend with grid overlay
- Each grid cell = 1 square foot
- Plans stored as JSON blobs in SQLite
- Single HTML template with inline CSS and vanilla JS

## Plant Database

Each plant has:
- **Name** — e.g. "Tomato", "Coneflower"
- **Color** — display color on the grid
- **Label** — 2-3 letter abbreviation (e.g. "Tom", "Con")
- **Spacing** — square feet needed (e.g. tomato = 4 sq ft / 2x2, lettuce = 1 sq ft)
- **Height** — mature height category: short / medium / tall

Includes both **vegetables** and **perennial flowers** (coneflower, black-eyed susan, lavender, hostas, daylilies, etc.).

Plants are seeded from a JSON file that is easy to edit and extend. Users can add/edit custom plants through the UI.

## Two Views

### Top-Down View (Primary)
- Main editable canvas with grid overlay
- Plants shown as colored squares with text labels
- Multi-cell plants show their full footprint (e.g. 2x2 for tomato)
- Spacing violations highlighted in red
- This is where all editing happens

### Front Profile View (Read-Only)
- Side profile generated from the grid
- Shows plant heights as colored bars/blocks, tallest in back to shortest in front
- Reveals when a short plant is hidden behind a tall one
- Toggle or side-by-side with top-down view

## Smart Warnings

- **Spacing violations** — red outlines when plants overlap or are too close
- **Visibility conflicts** — orange highlight when a short plant is placed behind a tall one
- Front edge of the garden = bottom of the grid

## Canvas Interaction

- Plant palette sidebar — click to select, click grid to place
- Click placed plant to select, delete/backspace to remove
- Hover tooltip — plant name, height, spacing info
- Grid lines with row/column number labels
- Scroll to zoom, drag empty space to pan

## Garden & Plan Management

- Create gardens by defining rectangular grids (width x depth in feet)
- Multiple gardens supported (e.g. "Raised Bed 1", "Back Border")
- Save plans with names (e.g. "Spring 2026 v1")
- Duplicate a plan to iterate without losing the original
- Load/switch between plans via dropdown
- Delete unwanted plans

## Tech Stack

| Layer | Choice |
|-------|--------|
| Backend | Flask + SQLite |
| Frontend | Single HTML template, inline CSS, vanilla JS + HTML5 Canvas |
| Data | Plant seed data in JSON file, plans in SQLite |
| Service | systemd service on homelab |
| Repo | ~/garden-planner |

No external JS libraries. Vanilla Canvas API handles grid drawing, front view, and zoom/pan.
