import sqlite3
import requests
import json
import time

def create_itunes_tables(db_name='music_weather.db'):
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS genres (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            genre_name TEXT UNIQUE NOT NULL
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS itunes_tracks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            track_name TEXT NOT NULL,
            artist_name TEXT NOT NULL,
            collection_name TEXT,
            genre_id INTEGER,
            release_date TEXT,
            release_year INTEGER,
            track_time_millis INTEGER,
            track_price REAL,
            collection_price REAL,
            country TEXT,
            FOREIGN KEY (genre_id) REFERENCES genres(id),
            UNIQUE(track_name, artist_name)
        )
    ''')

    conn.commit()
    conn.close()

def get_or_create_genre(cur, genre_name):
    cur.execute('SELECT id FROM genres WHERE genre_name = ?', (genre_name,))
    result = cur.fetchone()
    
    if result:
        return result[0]
    else:
        cur.execute('INSERT INTO genres (genre_name) VALUES (?)', (genre_name,))
        return cur.lastrowid

def itunes_stats(track_name, artist_name, db_name='music_weather.db'):
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    cur.execute('''
        SELECT id FROM itunes_tracks 
        WHERE track_name = ? AND artist_name = ?
    ''', (track_name, artist_name))
    if cur.fetchone():
        print(f"Track '{track_name}' by {artist_name} already exists in database.")
        conn.close()
        return False
    base_url = 'https://itunes.apple.com/search'
    query = f"{track_name} {artist_name}"
    
    params = {
        'term': query,
        'media': 'music',
        'entity': 'song',
        'limit': 5
    }
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if data['resultCount'] > 0:
            # Try to find the best match
            track_data = None
            for result in data['results']:
                if (track_name.lower() in result.get('trackName', '').lower() and 
                    artist_name.lower() in result.get('artistName', '').lower()):
                    track_data = result
                    break
            if not track_data:
                track_data = data['results'][0]
            genre_name = track_data.get('primaryGenreName', 'Unknown')
            genre_id = get_or_create_genre(cur, genre_name)
            release_date = track_data.get('releaseDate', '')
            release_year = None
            if release_date:
                try:
                    release_year = int(release_date.split('-')[0])
                except:
                    pass
            cur.execute('''
                INSERT INTO itunes_tracks 
                (track_name, artist_name, collection_name, genre_id, release_date, 
                 release_year, track_time_millis, track_price, collection_price, country)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                track_data.get('trackName', track_name),
                track_data.get('artistName', artist_name),
                track_data.get('collectionName'),
                genre_id,
                release_date,
                release_year,
                track_data.get('trackTimeMillis'),
                track_data.get('trackPrice'),
                track_data.get('collectionPrice'),
                track_data.get('country')
            ))
            
            conn.commit()
            conn.close()

            print(f"Successfully stored: '{track_name}' by {artist_name}")
            return True
        
        else:
            print(f"Track '{track_name}' by {artist_name} not found on iTunes.")
            conn.close()
            return False
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from iTunes API: {e}")
        conn.close()
        return False

def get_lastfm_tracks_to_lookup(db_name='music_weather.db', limit=25):
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    cur.execute('''
        SELECT DISTINCT track_name, artist_name 
        FROM lastfm_tracks 
        WHERE (track_name, artist_name) NOT IN (
            SELECT track_name, artist_name FROM itunes_tracks
        )
        LIMIT ?
    ''', (limit,))
    
    tracks = cur.fetchall()
    conn.close()
    
    return tracks

def main():
    db_name = 'music_weather.db'
    
    create_itunes_tables(db_name)
    tracks_to_lookup = get_lastfm_tracks_to_lookup(db_name, limit=25)
    
    if not tracks_to_lookup:
        print("No new tracks to look up. All Last.fm tracks have been processed.")
        return
    
    print(f"Found {len(tracks_to_lookup)} tracks to look up on iTunes.")
    print("Starting data collection (limited to 25 items)...\n")
    
    successful = 0
    failed = 0
    
    for track_name, artist_name in tracks_to_lookup:
        if itunes_stats(track_name, artist_name, db_name):
            successful += 1
        else:
            failed += 1
        time.sleep(0.5)
    
    print(f"\n--- Summary ---")
    print(f"Successfully stored: {successful} tracks")
    print(f"Failed/Skipped: {failed} tracks")
    
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM itunes_tracks')
    total = cur.fetchone()[0]
    conn.close()
    print(f"Total iTunes tracks in database: {total}")


if __name__ == "__main__":
    main()
