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

def get_create_genre(cur, g_name):
    cur.execute('SELECT id FROM genres WHERE g_name = ?', (g_name,))
    result = cur.fetchone()
    
    if result:
        return result[0]
    else:
        cur.execute('INSERT INTO genres (g_name) VALUES (?)', (g_name,))
        return cur.lastrowid
