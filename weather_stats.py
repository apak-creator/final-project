import requests

def c_to_f(c): # convert celsius into fahrenheit
    return (c * 9/5) + 32

def get_historical_weather(city: str, start_date: str, end_date: str):    
    # convert city name input into coordinates for Open-Meteo
    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"
    geo_response = requests.get(geo_url).json()

    if "results" not in geo_response:
        return {"error": f"City '{city}' not found."}

    latitude = geo_response["results"][0]["latitude"]
    longitude = geo_response["results"][0]["longitude"]

    # get historical weather
    weather_url = (
        "https://archive-api.open-meteo.com/v1/archive?"
        f"latitude={latitude}&longitude={longitude}"
        f"&start_date={start_date}&end_date={end_date}"
        "&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,rain_sum,snowfall_sum"
        "&timezone=auto"
    ) 

    return requests.get(weather_url).json()

city = input("Enter a city name: ") # user inputs for city & dates
start_date = input("Enter start date (YYYY-MM-DD): ")
end_date = input("Enter end date (YYYY-MM-DD): ")

data = get_historical_weather(city, start_date, end_date)

if "error" in data: # error handling
    print(data["error"])
else:
    print(f"\nWeather summary for {city} from {start_date} to {end_date}:\n")

    days = data["daily"]["time"]
    max_temps_cel = data["daily"]["temperature_2m_max"]
    min_temps_cel = data["daily"]["temperature_2m_min"]
    rain = data["daily"]["rain_sum"]
    snow = data["daily"]["snowfall_sum"]

    max_temps_far = [c_to_f(t) for t in max_temps_cel] # converts celsius data into fahrenheit
    min_temps_far = [c_to_f(t) for t in min_temps_cel]

    for i in range(len(days)): # finding high/lows in averages
        print(f"Date: {days[i]}")
        print(f"  Max Temp: {max_temps_far[i]}°F")
        print(f"  Min Temp: {min_temps_far[i]}°F")
        print(f"  Rain: {rain[i]} mm")
        print(f"  Snow: {snow[i]} cm")
        print("-" * 35)

    avg_max = sum(max_temps_far) / len(max_temps_far) # finding averages for temps, rain, and snow (now using fahrenheit)
    avg_min = sum(min_temps_far) / len(min_temps_far)
    avg_rain = sum(rain) / len(rain)
    avg_snow = sum(snow) / len(snow)

    print("\n--- Averages ---") # prints all averages
    print(f"Average Max Temp: {avg_max:.2f}°F")
    print(f"Average Min Temp: {avg_min:.2f}°F")
    print(f"Average Rainfall: {avg_rain:.2f} mm/day")
    print(f"Average Snowfall: {avg_snow:.2f} cm/day")
