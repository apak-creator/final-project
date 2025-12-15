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

def itunes_chart(db_name='music_weather.db'):
    conn = sqlite3.connect(db_name)
    query = '''
        SELECT g.genre_name, COUNT(*) as track_count,
               AVG(i.track_time_millis) / 60000.0 as avg_length_minutes
        FROM itunes_tracks i
        JOIN genres g ON i.genre_id = g.id
        GROUP BY g.genre_name
        ORDER BY track_count DESC
        LIMIT 10
    '''
    genre_df = pd.read_sql_query(query, conn)
    year_query = '''
        SELECT release_year, COUNT(*) as track_count
        FROM itunes_tracks
        WHERE release_year IS NOT NULL
        GROUP BY release_year
        ORDER BY release_year
    '''
    year_df = pd.read_sql_query(year_query, conn)
    length_query = '''
        SELECT track_time_millis / 60000.0 as track_length_minutes
        FROM itunes_tracks
        WHERE track_time_millis IS NOT NULL
    '''
    length_df = pd.read_sql_query(length_query, conn)
    
    conn.close()
    sns.set_style("whitegrid")
    sns.set_palette("husl")

    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('iTunes Music Data Analysis', fontsize=16, fontweight='bold')
    
    sns.barplot(data=genre_df, x='track_count', y='genre_name', 
                ax=axes[0, 0], palette='viridis')
    axes[0, 0].set_title('Top 10 Genres by Track Count', fontweight='bold')
    axes[0, 0].set_xlabel('Number of Tracks')
    axes[0, 0].set_ylabel('Genre')

    sns.barplot(data=genre_df, x='avg_length_minutes', y='genre_name',
                ax=axes[0, 1], palette='mako')
    axes[0, 1].set_title('Average Track Length by Genre', fontweight='bold')
    axes[0, 1].set_xlabel('Average Length (minutes)')
    axes[0, 1].set_ylabel('Genre')

    sns.lineplot(data=year_df, x='release_year', y='track_count',
                 ax=axes[1, 0], marker='o', linewidth=2.5, color='coral')
    axes[1, 0].set_title('Tracks by Release Year', fontweight='bold')
    axes[1, 0].set_xlabel('Release Year')
    axes[1, 0].set_ylabel('Number of Tracks')
    axes[1, 0].tick_params(axis='x', rotation=45)
    sns.histplot(data=length_df, x='track_length_minutes', 
                 bins=30, kde=True, ax=axes[1, 1], color='teal')
    axes[1, 1].set_title('Distribution of Track Lengths', fontweight='bold')
    axes[1, 1].set_xlabel('Track Length (minutes)')
    axes[1, 1].set_ylabel('Frequency')
    
    plt.tight_layout()
    plt.savefig('itunes_visualizations.png', dpi=300, bbox_inches='tight')
    print("Visualizations saved as 'itunes_visualizations.png'")
    plt.show()

    plt.figure(figsize=(10, 6))
    scatter_query = '''
        SELECT release_year, track_time_millis / 60000.0 as track_length_minutes
        FROM itunes_tracks
        WHERE release_year IS NOT NULL AND track_time_millis IS NOT NULL
    '''
    conn = sqlite3.connect(db_name)
    scatter_df = pd.read_sql_query(scatter_query, conn)
    conn.close()
    
    sns.scatterplot(data=scatter_df, x='release_year', y='track_length_minutes',
                    alpha=0.6, s=50, color='purple')
    plt.title('Track Length vs Release Year', fontsize=14, fontweight='bold')
    plt.xlabel('Release Year')
    plt.ylabel('Track Length (minutes)')
    plt.tight_layout()
    plt.savefig('itunes_scatter_plot.png', dpi=300, bbox_inches='tight')
    print("Scatter plot saved as 'itunes_scatter_plot.png'")
    plt.show()

def main():
    
    print("Running iTunes data analysis...\n")
    
    results = find_itunes_avg()
    
    print("\n" + "="*50 + "\n")
    
    itunes_chart()
    
    print("\nAnalysis complete!")


if __name__ == "__main__":
    main()
