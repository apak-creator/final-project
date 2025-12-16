import sqlite3
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd

def find_weather_avg(city: str, start_date: str, end_date: str):
    conn = sqlite3.connect("data.db")
    # gets city ID from data.db
    cur = conn.cursor()
    cur.execute(
        "SELECT id FROM cities WHERE name = ?",
        (city,)
    )
    result = cur.fetchone()

    if not result:
        print(f"No data found for city '{city}'.")
        conn.close()
        return

    city_id = result[0]

    # calculates averages from weather.db
    cur.execute("""
        SELECT
            AVG(max_temp_f),
            AVG(min_temp_f),
            AVG(rain),
            AVG(snow)
        FROM daily_weather
        WHERE city_id = ?
          AND date BETWEEN ? AND ?
    """, (city_id, start_date, end_date))
    avg_max, avg_min, avg_rain, avg_snow = cur.fetchone()
    if avg_max is None:
        print("No weather records found for that date range.")
        conn.close()
        return

    print("\n--- Averages (from database) ---")
    print(f"Average Max Temp: {avg_max:.2f}°F")
    print(f"Average Min Temp: {avg_min:.2f}°F")
    print(f"Average Rainfall: {avg_rain:.2f} mm/day")
    print(f"Average Snowfall: {avg_snow:.2f} cm/day")

    # write averages to a text file
    with open(f"{city}_weather_summary.txt", "w") as f:
        f.write(f"Weather Summary for {city} ({start_date} to {end_date})\n")
        f.write(f"Average Max Temp: {avg_max:.2f}°F\n")
        f.write(f"Average Min Temp: {avg_min:.2f}°F\n")
        f.write(f"Average Rainfall: {avg_rain:.2f} mm/day\n")
        f.write(f"Average Snowfall: {avg_snow:.2f} cm/day\n")
    print(f"Averages written to {city}_weather_summary.txt")

    # loads data for visualizations
    df = pd.read_sql_query("""
        SELECT date, max_temp_f, min_temp_f, rain, snow
        FROM daily_weather
        WHERE city_id = ?
          AND date BETWEEN ? AND ?
        ORDER BY date
    """, conn, params=(city_id, start_date, end_date))

    conn.close()

    sns.set(style="whitegrid")

    # temps over time chart
    plt.figure(figsize=(10, 5))
    sns.lineplot(data=df, x="date", y="max_temp_f", label="Max Temp (°F)")
    sns.lineplot(data=df, x="date", y="min_temp_f", label="Min Temp (°F)")
    plt.xticks(rotation=45)
    plt.title(f"Daily Temperatures in {city}")
    plt.xlabel("Date")
    plt.ylabel("Temperature (°F)")
    plt.tight_layout()
    plt.show()

    # rain vs snow chart
    avg_df = pd.DataFrame({
        "Metric": ["Rain", "Snow"],
        "Average": [avg_rain, avg_snow]
    })

    plt.figure(figsize=(6, 4))
    sns.barplot(data=avg_df, x="Metric", y="Average")
    plt.title(f"Average Precipitation in {city}")
    plt.ylabel("Average Amount")
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    city = input("Enter a city name: ")
    start_date = input("Enter start date (YYYY-MM-DD): ")
    end_date = input("Enter end date (YYYY-MM-DD): ")

    find_weather_avg(city, start_date, end_date)
