from weather_api import fetch_weather

result = fetch_weather("Dallas", "2026-06-13")
print(result["payload"]["daily"])