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
