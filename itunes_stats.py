import sqlite3
import requests
import json
import time

def create_itunes_tables(db_name='data.db'):
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

def itunes_stats(music_stats_dict, db_name='data.db'):
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    create_itunes_tables(db_name)
    
    cur.execute('''
        SELECT DISTINCT t.name AS track_name, a.name AS artist_name
        FROM tracks t
        JOIN artists a ON t.artist_id = a.id
        WHERE NOT EXISTS (
            SELECT 1 FROM itunes_tracks it
            WHERE it.track_name = t.name AND it.artist_name = a.name
        )
        LIMIT 25
    ''')
    
    tracks = cur.fetchall()
    
    itunes_results = {
        'tracks_processed': 0,
        'tracks_found': 0,
        'tracks_not_found': 0,
        'track_details': []
    }
    
    for track_name, artist_name in tracks:
        base_url = 'https://itunes.apple.com/search'
        query = f"{track_name} {artist_name}"
        
        params = {
            'term': query,
            'media': 'music',
            'entity': 'song',
            'limit': 5
        }
        
        try:
            response = requests.get(base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('resultCount', 0) > 0:
                track_data = None
                for result in data.get('results', []):
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
                        release_year = None
                
                try:
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
                    
                    itunes_results['tracks_found'] += 1
                    itunes_results['track_details'].append({
                        'track': track_name,
                        'artist': artist_name,
                        'genre': genre_name
                    })
                    
                    print(f"Successfully stored: '{track_name}' by {artist_name}")
                    
                except sqlite3.IntegrityError:
                    print(f"Duplicate detected, skipping: '{track_name}' by {artist_name}")

            else:
                itunes_results['tracks_not_found'] += 1
                print(f"Track '{track_name}' by {artist_name} not found on iTunes.")
                
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from iTunes API: {e}")
            itunes_results['tracks_not_found'] += 1
        
        itunes_results['tracks_processed'] += 1
        time.sleep(0.5)
    
    conn.commit()
    conn.close()
    
    return itunes_results

conn = sqlite3.connect('data.db')
cur = conn.cursor()
create_itunes_tables('data.db')

print("Collecting iTunes metadata for Last.fm tracks...")
result = itunes_stats({}, 'data.db')

print(f"\n--- Summary ---")
print(f"Tracks processed: {result['tracks_processed']}")
print(f"Tracks found: {result['tracks_found']}")
print(f"Tracks not found: {result['tracks_not_found']}")

conn.close()
