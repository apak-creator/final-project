import sqlite3
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd

def find_itunes_avg(db_name='music_weather.db'):
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    cur.execute('''
        SELECT AVG(track_time_millis) / 60000.0 AS avg_track_length_minutes
        FROM itunes_tracks
        WHERE track_time_millis IS NOT NULL
    ''')
    avg_length = cur.fetchone()[0]
    cur.execute('''
        SELECT AVG(track_price) AS avg_track_price
        FROM itunes_tracks
        WHERE track_price IS NOT NULL
    ''')
    avg_price = cur.fetchone()[0]
    cur.execute('''
        SELECT AVG(release_year) AS avg_release_year
        FROM itunes_tracks
        WHERE release_year IS NOT NULL
    ''')
    avg_year = cur.fetchone()[0]
    cur.execute('''
        SELECT g.genre_name, COUNT(*) as track_count, 
               AVG(i.track_time_millis) / 60000.0 as avg_length_minutes
        FROM itunes_tracks i
        JOIN genres g ON i.genre_id = g.id
        GROUP BY g.genre_name
        ORDER BY track_count DESC
    ''')
    genre_stats = cur.fetchall()
    
    conn.close()
    
    results = {
        'avg_track_length_minutes': round(avg_length, 2) if avg_length else 0,
        'avg_track_price': round(avg_price, 2) if avg_price else 0,
        'avg_release_year': round(avg_year, 2) if avg_year else 0,
        'genre_stats': genre_stats
    }

    print("=== iTunes Data Averages ===")
    print(f"Average Track Length: {results['avg_track_length_minutes']} minutes")
    print(f"Average Track Price: ${results['avg_track_price']}")
    print(f"Average Release Year: {results['avg_release_year']}")
    print("\n=== Genre Statistics ===")
    for genre, count, avg_len in genre_stats:
        print(f"{genre}: {count} tracks, avg length {round(avg_len, 2)} min")
    with open('itunes_calculations.txt', 'w') as f:
        f.write("=== iTunes Data Calculations ===\n\n")
        f.write(f"Average Track Length: {results['avg_track_length_minutes']} minutes\n")
        f.write(f"Average Track Price: ${results['avg_track_price']}\n")
        f.write(f"Average Release Year: {results['avg_release_year']}\n\n")
        f.write("=== Genre Statistics ===\n")
        for genre, count, avg_len in genre_stats:
            f.write(f"{genre}: {count} tracks, avg length {round(avg_len, 2)} min\n")
    
    print("\nCalculations written to 'itunes_calculations.txt'")
    
    return results

