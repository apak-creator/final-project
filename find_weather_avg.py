import requests

import requests

# converts celsius into fahrenheit
def c_to_f(c):
    return (c * 9/5) + 32

# function for finding raw statistics for weather in a specific timeframe
def weather_stats(city: str, start_date: str, end_date: str):
    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1" # converts city location to coordinates for Open-Meteo format
    geo_response = requests.get(geo_url).json()
    
    if "results" not in geo_response:
        print(f"City '{city}' not found.")
        return None

    latitude = geo_response["results"][0]["latitude"]
    longitude = geo_response["results"][0]["longitude"]
    # historical weather
    weather_url = (
        "https://archive-api.open-meteo.com/v1/archive?"
        f"latitude={latitude}&longitude={longitude}"
        f"&start_date={start_date}&end_date={end_date}"
        "&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,rain_sum,snowfall_sum"
        "&timezone=auto"
    )

    data = requests.get(weather_url).json()

    if "daily" not in data: # error handling
        print("No weather data found for this timeframe.")
        return None

    days = data["daily"]["time"] # sorting data by type
    max_temps_far = [c_to_f(t) for t in data["daily"]["temperature_2m_max"]]
    min_temps_far = [c_to_f(t) for t in data["daily"]["temperature_2m_min"]]
    rain = data["daily"]["rain_sum"]
    snow = data["daily"]["snowfall_sum"]

    print(f"\nWeather summary for {city} from {start_date} to {end_date}:\n")
    for i in range(len(days)):
        print(f"Date: {days[i]}")
        print(f"  Max Temp: {max_temps_far[i]:.1f}°F")
        print(f"  Min Temp: {min_temps_far[i]:.1f}°F")
        print(f"  Rain: {rain[i]} mm")
        print(f"  Snow: {snow[i]} cm")
        print("-" * 35)
    
    return data

# function for calculating averages from weather_stats
def find_weather_avg(data):
    """
    Calculate and print average max/min temperatures, rain, and snow from weather data.
    """
    if not data or "daily" not in data:
        print("No valid data provided for averages.")
        return

    max_temps_far = [c_to_f(t) for t in data["daily"]["temperature_2m_max"]] # sorting data by type
    min_temps_far = [c_to_f(t) for t in data["daily"]["temperature_2m_min"]]
    rain = data["daily"]["rain_sum"]
    snow = data["daily"]["snowfall_sum"]

    avg_max = sum(max_temps_far) / len(max_temps_far) # avg. calculations
    avg_min = sum(min_temps_far) / len(min_temps_far)
    avg_rain = sum(rain) / len(rain)
    avg_snow = sum(snow) / len(snow)

    print("\n--- Averages ---")
    print(f"Average Max Temp: {avg_max:.2f}°F")
    print(f"Average Min Temp: {avg_min:.2f}°F")
    print(f"Average Rainfall: {avg_rain:.2f} mm/day")
    print(f"Average Snowfall: {avg_snow:.2f} cm/day")

# user inputs for location & timeframe
city = input("Enter a city name: ")
start_date = input("Enter start date (YYYY-MM-DD): ")
end_date = input("Enter end date (YYYY-MM-DD): ")

weather_data = weather_stats(city, start_date, end_date)
find_weather_avg(weather_data)
