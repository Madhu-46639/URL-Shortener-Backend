from flask import Flask, request, redirect, jsonify
import sqlite3
import random
import string
from pathlib import Path

app = Flask(__name__)

DB_PATH = Path(__file__).with_name("urls.db")

# Create database and table
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS urls(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        original_url TEXT,
        short_code TEXT UNIQUE
    )
    """)
    conn.commit()
    conn.close()

# Generate short code
def generate_code(length=6):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

@app.route("/", methods=["GET"])
def home():
    return jsonify(
        {
            "message": "URL shortener is running",
            "usage": {
                "shorten": {
                    "method": "POST",
                    "path": "/shorten",
                    "json_body": {"url": "https://example.com"},
                },
                "redirect": {"method": "GET", "path": "/<short_code>"},
            },
        }
    )

# API to shorten URL
@app.route("/shorten", methods=["POST"])
def shorten():
    data = request.get_json(silent=True) or {}
    url = data.get("url")

    if not url:
        return jsonify({"error": "URL required"}), 400

    short_code = generate_code()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("INSERT INTO urls (original_url, short_code) VALUES (?, ?)", (url, short_code))

    conn.commit()
    conn.close()

    short_url = "http://localhost:5000/" + short_code
    return jsonify({"short_url": short_url})

# Redirect to original URL
@app.route("/<code>")
def redirect_url(code):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT original_url FROM urls WHERE short_code=?", (code,))
    result = cur.fetchone()

    conn.close()

    if result:
        return redirect(result[0])
    else:
        return jsonify({"error": "URL not found"}), 404

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
