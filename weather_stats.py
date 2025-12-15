import requests
import sqlite3

def init_db():
    conn = sqlite3.connect("weather.db")
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS cities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            latitude REAL,
            longitude REAL
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS daily_weather (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city_id INTEGER,
            date TEXT,
            max_temp_f REAL,
            min_temp_f REAL,
            rain REAL,
            snow REAL,
            UNIQUE(city_id, date),
            FOREIGN KEY(city_id) REFERENCES cities(id)
        );
    """)

    conn.commit()
    return conn, cur

def get_or_create_city(cur, conn, city, lat, lon):
    cur.execute(
        "INSERT OR IGNORE INTO cities (name, latitude, longitude) VALUES (?, ?, ?)",
        (city, lat, lon)
    )
    conn.commit()

    cur.execute("SELECT id FROM cities WHERE name = ?", (city,))
    return cur.fetchone()[0]

def store_daily_weather(cur, conn, city_id, data):
    days = data["daily"]["time"]
    max_temps = [c_to_f(t) for t in data["daily"]["temperature_2m_max"]]
    min_temps = [c_to_f(t) for t in data["daily"]["temperature_2m_min"]]
    rain = data["daily"]["rain_sum"]
    snow = data["daily"]["snowfall_sum"]

    inserted = 0

    for i in range(len(days)):
        if inserted >= 25:
            break

        try:
            cur.execute("""
                INSERT INTO daily_weather
                (city_id, date, max_temp_f, min_temp_f, rain, snow)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                city_id,
                days[i],
                max_temps[i],
                min_temps[i],
                rain[i],
                snow[i]
            ))
            inserted += 1
        except sqlite3.IntegrityError:
            # Duplicate date for this city — skip
            continue

    conn.commit()
    print(f"{inserted} new rows stored.")

def c_to_f(c):
    return (c * 9/5) + 32

def weather_stats(city: str, start_date: str, end_date: str):
    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"
    geo_response = requests.get(geo_url).json()

    if "results" not in geo_response:
        print(f"City '{city}' not found.")
        return None, None, None

    latitude = geo_response["results"][0]["latitude"]
    longitude = geo_response["results"][0]["longitude"]

    weather_url = (
        "https://archive-api.open-meteo.com/v1/archive?"
        f"latitude={latitude}&longitude={longitude}"
        f"&start_date={start_date}&end_date={end_date}"
        "&daily=temperature_2m_max,temperature_2m_min,rain_sum,snowfall_sum"
        "&timezone=auto"
    )

    data = requests.get(weather_url).json()

    if "daily" not in data:
        print("No daily weather data found.")
        return None, None, None

    return data, latitude, longitude

conn, cur = init_db()

city = input("Enter city name: ")
start_date = input("Enter start date (YYYY-MM-DD): ")
end_date = input("Enter end date (YYYY-MM-DD): ")

data, lat, lon = weather_stats(city, start_date, end_date)

if data:
    city_id = get_or_create_city(cur, conn, city, lat, lon)
    store_daily_weather(cur, conn, city_id, data)

conn.close()
