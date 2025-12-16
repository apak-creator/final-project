# find_music_avg.py
import sqlite3
import json
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

DB_PATH = "data.db"


def find_music_average(username, period="7day", db_path=DB_PATH, out_json=None):
    """
    PART 2 FUNCTION (required name): find_music_average()
    Uses JOINs, writes JSON, returns dict.
    """
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("SELECT id FROM users WHERE username=?", (username,))
    row = cur.fetchone()
    if not row:
        conn.close()
        raise ValueError(f"User '{username}' not found in users table. Run music_stats() first.")
    user_id = row[0]

    # JOIN: avg playcount + count of stored toptracks for that period
    cur.execute("""
        SELECT AVG(ltt.playcount), COUNT(*)
        FROM lastfm_toptracks ltt
        JOIN tracks t ON ltt.track_id = t.id
        JOIN artists a ON t.artist_id = a.id
        WHERE ltt.user_id=? AND ltt.period=?;
    """, (user_id, period))
    avg_playcount, num_rows = cur.fetchone()
    avg_playcount = float(avg_playcount) if avg_playcount is not None else 0.0
    num_rows = int(num_rows) if num_rows is not None else 0

    # JOIN: top artists
    cur.execute("""
        SELECT a.name, SUM(ltt.playcount) AS total_playcount
        FROM lastfm_toptracks ltt
        JOIN tracks t ON ltt.track_id = t.id
        JOIN artists a ON t.artist_id = a.id
        WHERE ltt.user_id=? AND ltt.period=?
        GROUP BY a.id
        ORDER BY total_playcount DESC
        LIMIT 10;
    """, (user_id, period))
    top_artists = [{"artist": r[0], "total_playcount": int(r[1])} for r in cur.fetchall()]

    # JOIN: top tracks
    cur.execute("""
        SELECT t.name, a.name, ltt.playcount
        FROM lastfm_toptracks ltt
        JOIN tracks t ON ltt.track_id = t.id
        JOIN artists a ON t.artist_id = a.id
        WHERE ltt.user_id=? AND ltt.period=?
        ORDER BY ltt.playcount DESC
        LIMIT 10;
    """, (user_id, period))
    top_tracks = [{"track": r[0], "artist": r[1], "playcount": int(r[2])} for r in cur.fetchall()]

    conn.close()

    result = {
        "username": username,
        "period": period,
        "num_toptracks_rows_for_period": num_rows,
        "avg_playcount_toptracks_for_period": round(avg_playcount, 2),
        "top_artists_by_total_playcount": top_artists,
        "top_tracks_by_playcount": top_tracks
    }

    if out_json is None:
        out_json = f"music_avg_{username}_{period}.json".replace("/", "_").replace("\\", "_")

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    return result


def make_visualizations(username, period="7day", db_path=DB_PATH):
    """
    Creates 2 charts and saves PNGs.
    """
    conn = sqlite3.connect(db_path)

    tracks_df = pd.read_sql_query("""
        SELECT t.name AS track, a.name AS artist, ltt.playcount AS playcount
        FROM lastfm_toptracks ltt
        JOIN users u ON ltt.user_id = u.id
        JOIN tracks t ON ltt.track_id = t.id
        JOIN artists a ON t.artist_id = a.id
        WHERE u.username=? AND ltt.period=?
        ORDER BY ltt.playcount DESC
        LIMIT 10;
    """, conn, params=(username, period))

    artists_df = pd.read_sql_query("""
        SELECT a.name AS artist, SUM(ltt.playcount) AS total_playcount
        FROM lastfm_toptracks ltt
        JOIN users u ON ltt.user_id = u.id
        JOIN tracks t ON ltt.track_id = t.id
        JOIN artists a ON t.artist_id = a.id
        WHERE u.username=? AND ltt.period=?
        GROUP BY a.id
        ORDER BY total_playcount DESC
        LIMIT 10;
    """, conn, params=(username, period))

    conn.close()

    sns.set(style="whitegrid")

    plt.figure(figsize=(10, 5))
    sns.barplot(data=tracks_df, x="playcount", y="track")
    plt.title(f"Top 10 Tracks — {username} ({period})")
    plt.xlabel("Playcount")
    plt.ylabel("Track")
    plt.tight_layout()
    out1 = f"chart_tracks_{username}_{period}.png".replace("/", "_").replace("\\", "_")
    plt.savefig(out1, dpi=200)
    plt.show()

    plt.figure(figsize=(10, 5))
    sns.barplot(data=artists_df, x="total_playcount", y="artist")
    plt.title(f"Top 10 Artists — {username} ({period})")
    plt.xlabel("Total Playcount")
    plt.ylabel("Artist")
    plt.tight_layout()
    out2 = f"chart_artists_{username}_{period}.png".replace("/", "_").replace("\\", "_")
    plt.savefig(out2, dpi=200)
    plt.show()

    return {"tracks_chart": out1, "artists_chart": out2}


if __name__ == "__main__":
    user = input("Username: ").strip()
    period = input("Period (7day, 1month, 3month, etc.): ").strip() or "7day"

    stats = find_music_average(user, period)
    print(" Wrote JSON:", f"music_avg_{user}_{period}.json")

    charts = make_visualizations(user, period)
    print("Saved charts:", charts)