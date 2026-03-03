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


PLANTS_PATH = os.path.join(os.path.dirname(__file__), "plants.json")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/plants", methods=["GET"])
def get_plants():
    with open(PLANTS_PATH) as f:
        plants = json.load(f)
    conn = get_db()
    custom = conn.execute("SELECT * FROM custom_plants").fetchall()
    conn.close()
    for row in custom:
        plants.append({
            "id": row["id"],
            "name": row["name"],
            "label": row["label"],
            "color": row["color"],
            "spacing": row["spacing"],
            "height": row["height"],
            "category": row["category"],
            "custom": True,
        })
    return jsonify(plants)


@app.route("/api/plants", methods=["POST"])
def add_plant():
    data = request.get_json()
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO custom_plants (name, label, color, spacing, height, category) VALUES (?, ?, ?, ?, ?, ?)",
        (data["name"], data["label"], data["color"], data.get("spacing", 1), data.get("height", "medium"), data.get("category", "vegetable")),
    )
    conn.commit()
    plant_id = cur.lastrowid
    conn.close()
    return jsonify({"id": plant_id}), 201


# --- Garden CRUD ---

@app.route("/api/gardens", methods=["GET"])
def list_gardens():
    conn = get_db()
    rows = conn.execute("SELECT * FROM gardens ORDER BY created_at DESC").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route("/api/gardens", methods=["POST"])
def create_garden():
    data = request.get_json()
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO gardens (name, width, depth) VALUES (?, ?, ?)",
        (data["name"], data["width"], data["depth"]),
    )
    conn.commit()
    garden_id = cur.lastrowid
    conn.close()
    return jsonify({"id": garden_id}), 201


@app.route("/api/gardens/<int:garden_id>", methods=["DELETE"])
def delete_garden(garden_id):
    conn = get_db()
    conn.execute("DELETE FROM plans WHERE garden_id = ?", (garden_id,))
    conn.execute("DELETE FROM gardens WHERE id = ?", (garden_id,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


# --- Plan CRUD ---

@app.route("/api/gardens/<int:garden_id>/plans", methods=["GET"])
def list_plans(garden_id):
    conn = get_db()
    rows = conn.execute("SELECT * FROM plans WHERE garden_id = ? ORDER BY created_at DESC", (garden_id,)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route("/api/gardens/<int:garden_id>/plans", methods=["POST"])
def create_plan(garden_id):
    data = request.get_json()
    grid_data = json.dumps(data.get("grid_data", {}))
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO plans (garden_id, name, grid_data) VALUES (?, ?, ?)",
        (garden_id, data["name"], grid_data),
    )
    conn.commit()
    plan_id = cur.lastrowid
    conn.close()
    return jsonify({"id": plan_id}), 201


@app.route("/api/plans/<int:plan_id>", methods=["GET"])
def get_plan(plan_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM plans WHERE id = ?", (plan_id,)).fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "not found"}), 404
    result = dict(row)
    result["grid_data"] = json.loads(result["grid_data"])
    return jsonify(result)


@app.route("/api/plans/<int:plan_id>", methods=["PUT"])
def update_plan(plan_id):
    data = request.get_json()
    conn = get_db()
    if "grid_data" in data:
        data["grid_data"] = json.dumps(data["grid_data"])
    fields = []
    values = []
    for key in ("name", "grid_data"):
        if key in data:
            fields.append(f"{key} = ?")
            values.append(data[key])
    if fields:
        values.append(plan_id)
        conn.execute(f"UPDATE plans SET {', '.join(fields)} WHERE id = ?", values)
        conn.commit()
    conn.close()
    return jsonify({"ok": True})


@app.route("/api/plans/<int:plan_id>", methods=["DELETE"])
def delete_plan(plan_id):
    conn = get_db()
    conn.execute("DELETE FROM plans WHERE id = ?", (plan_id,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@app.route("/api/plans/<int:plan_id>/duplicate", methods=["POST"])
def duplicate_plan(plan_id):
    data = request.get_json() or {}
    conn = get_db()
    original = conn.execute("SELECT * FROM plans WHERE id = ?", (plan_id,)).fetchone()
    if not original:
        conn.close()
        return jsonify({"error": "not found"}), 404
    new_name = data.get("name", original["name"] + " (copy)")
    cur = conn.execute(
        "INSERT INTO plans (garden_id, name, grid_data) VALUES (?, ?, ?)",
        (original["garden_id"], new_name, original["grid_data"]),
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return jsonify({"id": new_id}), 201


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5001, debug=True)
