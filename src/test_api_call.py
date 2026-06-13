from weather_api import fetch_weather
result = fetch_weather("Dallas")
print(result["payload"]["current"])