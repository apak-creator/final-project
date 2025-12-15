import sqlite3

conn = sqlite3.connect('profiles.db')
cur = conn.cursor()

# Check Last.fm data
cur.execute("SELECT COUNT(*) FROM tracks")
lastfm_count = cur.fetchone()[0]
print(f"Last.fm tracks in database: {lastfm_count}")

# Check iTunes data
cur.execute("SELECT COUNT(*) FROM itunes_tracks")
itunes_count = cur.fetchone()[0]
print(f"iTunes tracks in database: {itunes_count}")

# Check if there are tracks NOT yet in iTunes
cur.execute("""
    SELECT COUNT(DISTINCT t.name)
    FROM tracks t
    JOIN artists a ON t.artist_id = a.id
    WHERE NOT EXISTS (
        SELECT 1 FROM itunes_tracks it
        WHERE it.track_name = t.name AND it.artist_name = a.name
    )
""")
unprocessed = cur.fetchone()[0]
print(f"Last.fm tracks NOT yet in iTunes: {unprocessed}")

conn.close()