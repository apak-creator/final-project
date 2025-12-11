import sqlite3
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd

def find_itunes_avg(db_name='music_weather.db'):
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    
