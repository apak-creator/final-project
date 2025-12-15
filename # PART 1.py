# PART 1.1 — Imports & Database Setup

import requests
import sqlite3
from bs4 import BeautifulSoup

DB_PATH = "profiles.db"
LASTFM_API_ROOT = "http://ws.audioscrobbler.com/2.0/"


def init_db(cur):
    cur.execute("""
        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            city TEXT,
            state TEXT
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS artists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS tracks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            artist_id INTEGER NOT NULL,
            UNIQUE(name, artist_id),
            FOREIGN KEY (artist_id) REFERENCES artists(id)
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS lastfm_toptracks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            period TEXT NOT NULL,
            track_id INTEGER NOT NULL,
            playcount INTEGER NOT NULL,
            UNIQUE(user_id, period, track_id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (track_id) REFERENCES tracks(id)
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS lastfm_recent_scrobbles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            track_id INTEGER NOT NULL,
            scrobble_time TEXT,
            UNIQUE(user_id, track_id, scrobble_time),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (track_id) REFERENCES tracks(id)
        );
    """)

#Reads users from database
def get_usernames_from_db(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    init_db(cur)
    conn.commit()

    cur.execute("SELECT username FROM profiles ORDER BY state, city")
    users = [row[0] for row in cur.fetchall()]

    conn.close()
    return users


def get_or_create_id(cur, table, column, value):
    cur.execute(f"INSERT OR IGNORE INTO {table} ({column}) VALUES (?)", (value,))
    cur.execute(f"SELECT id FROM {table} WHERE {column}=?", (value,))
    return cur.fetchone()[0]


def get_or_create_track_id(cur, track_name, artist_id):
    cur.execute(
        "INSERT OR IGNORE INTO tracks (name, artist_id) VALUES (?, ?)",
        (track_name, artist_id)
    )
    cur.execute(
        "SELECT id FROM tracks WHERE name=? AND artist_id=?",
        (track_name, artist_id)
    )
    return cur.fetchone()[0]

# Last.fm API (Top Tracks)
def collect_api_toptracks(cur, user_id, username, api_key, period, api_page, row_limit):
    inserted = 0

    params = {
        "method": "user.getTopTracks",
        "user": username,
        "period": period,
        "limit": 200,
        "page": api_page,
        "api_key": api_key,
        "format": "json"
    }

    r = requests.get(LASTFM_API_ROOT, params=params, timeout=20)
    r.raise_for_status()
    data = r.json()

    tracks = data.get("toptracks", {}).get("track", [])

    for t in tracks:
        if inserted >= row_limit:
            break

        track_name = t.get("name")
        artist_name = t.get("artist", {}).get("name")
        playcount = int(t.get("playcount", 0))

        if not track_name or not artist_name:
            continue

        artist_id = get_or_create_id(cur, "artists", "name", artist_name)
        track_id = get_or_create_track_id(cur, track_name, artist_id)

        try:
            cur.execute("""
                INSERT INTO lastfm_toptracks (user_id, period, track_id, playcount)
                VALUES (?, ?, ?, ?)
            """, (user_id, period, track_id, playcount))
            inserted += 1
        except sqlite3.IntegrityError:
            pass

    return inserted
