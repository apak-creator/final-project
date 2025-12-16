#music_stats.py

import requests
import sqlite3
from bs4 import BeautifulSoup

DB_PATH = "data.db"
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


def get_usernames_from_db(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    init_db(cur)
    conn.commit()

    cur.execute("SELECT username FROM profiles ORDER BY state, city")
    users = [r[0] for r in cur.fetchall()]
    conn.close()
    return users


def get_or_create_id(cur, table, column, value):
    cur.execute(f"INSERT OR IGNORE INTO {table} ({column}) VALUES (?)", (value,))
    cur.execute(f"SELECT id FROM {table} WHERE {column}=?", (value,))
    return cur.fetchone()[0]


def get_or_create_track_id(cur, track_name, artist_id):
    cur.execute("INSERT OR IGNORE INTO tracks (name, artist_id) VALUES (?, ?)", (track_name, artist_id))
    cur.execute("SELECT id FROM tracks WHERE name=? AND artist_id=?", (track_name, artist_id))
    return cur.fetchone()[0]


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

    if "error" in data:
        raise ValueError(f"Last.fm error {data.get('error')}: {data.get('message')}")

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


def collect_recent_scrobbles(cur, user_id, username, scrape_page, row_limit):
    inserted = 0
    url = f"https://www.last.fm/user/{username}/library?page={scrape_page}"
    html = requests.get(url, timeout=20).text
    soup = BeautifulSoup(html, "lxml")
    rows = soup.select("tr.chartlist-row")

    for row in rows:
        if inserted >= row_limit:
            break

        track_tag = row.select_one(".chartlist-name a")
        artist_tag = row.select_one(".chartlist-artist a")
        time_tag = row.select_one(".chartlist-timestamp")

        if not track_tag or not artist_tag:
            continue

        track_name = track_tag.get_text(strip=True)
        artist_name = artist_tag.get_text(strip=True)
        scrobble_time = time_tag.get_text(strip=True) if time_tag else None

        artist_id = get_or_create_id(cur, "artists", "name", artist_name)
        track_id = get_or_create_track_id(cur, track_name, artist_id)

        try:
            cur.execute("""
                INSERT INTO lastfm_recent_scrobbles (user_id, track_id, scrobble_time)
                VALUES (?, ?, ?)
            """, (user_id, track_id, scrobble_time))
            inserted += 1
        except sqlite3.IntegrityError:
            pass

    return inserted


def music_stats(username, api_key, period="7day", api_page=1, scrape_page=1, max_new_rows=25, db_path=DB_PATH):
    """
    PART 1 FUNCTION (required name): music_stats()
    Inserts <= 25 NEW rows per run total (split between API + scrape).
    """
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    init_db(cur)
    conn.commit()

    user_id = get_or_create_id(cur, "users", "username", username)

    api_budget = max_new_rows // 2
    scrape_budget = max_new_rows - api_budget

    api_added = collect_api_toptracks(cur, user_id, username, api_key, period, api_page, api_budget)
    conn.commit()

    scrape_added = collect_recent_scrobbles(cur, user_id, username, scrape_page, scrape_budget)
    conn.commit()

    conn.close()

    return {
        "username": username,
        "period": period,
        "api_page": api_page,
        "scrape_page": scrape_page,
        "rows_added_api": api_added,
        "rows_added_scrape": scrape_added,
        "rows_added_total": api_added + scrape_added
    }


if __name__ == "__main__":
    API_KEY = "1a47f39cf6c81b0fa73a5b7a85bc9c5f"

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    init_db(cur)
    
    usernames_to_add = [
        ('marscynic', 'Ann Arbor', 'MI'),
        ('Camisjamin', 'Grand Rapids', 'MI'),
        ('brahdy', 'East Lansing', 'MI'),
        ('voodles', 'Ann Arbor', 'MI'),
        ('Rowanshear', 'Denton', 'TX'),
        ('mmmarxie', 'Ann Arbor', 'MI'),
        ('JacobSwain61', 'Grand Rapids', 'MI'),
        ('ggWoof', 'Grand Rapids', 'MI'),
        ('kln0', 'Grand Rapids', 'MI'),
        ('Suz101', 'Ann Arbor', 'MI'),
        ('uzier', 'Wyandotte', 'MI')
    ]
    
    for username, city, state in usernames_to_add:
        cur.execute("""
            INSERT OR IGNORE INTO profiles (username, city, state)
            VALUES (?, ?, ?)
        """, (username, city, state))
    
    conn.commit()
    conn.close()
    print(f"Ensured {len(usernames_to_add)} profiles exist in database.\n")

    users = get_usernames_from_db()
    if not users:
        print("No usernames found in profiles table (data.db).")
    else:
        for u in users:
            print(music_stats(u, API_KEY, period="7day", api_page=1, scrape_page=1))