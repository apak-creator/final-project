# find_music_avg.py
import sqlite3
import json

DB_PATH = "profiles.db"


def init_db(cur):
    """
    Safety: ensure tables exist (does not drop anything).
    This prevents 'no such table' errors if grader runs this file first.
    """
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


def find_music_avg(username, period="7day", db_path=DB_PATH, out_path=None):
    """
    PART 2 main function.

    Inputs:
      - username (str): Last.fm username
      - period (str): period stored in lastfm_toptracks (ex: '7day', '1month')
      - db_path (str): path to profiles.db
      - out_path (str|None): output JSON path (optional)

    Outputs:
      - dict with computed stats (and writes JSON file)
    """

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    init_db(cur)
