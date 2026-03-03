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
