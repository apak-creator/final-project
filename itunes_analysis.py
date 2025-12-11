import sqlite3
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd

def find_itunes_avg(db_name='music_weather.db'):
    """
    Calculates averages from iTunes data in the database.
    This is YOUR calculation function.
    
    Args:
        db_name (str): Name of the SQLite database file
        
    Returns:
        dict: Dictionary containing various calculated averages
    """
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    
