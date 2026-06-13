import json
import urllib.parse
import urllib.request
from datetime import date


CITY_COORDINATES = {
    "Dallas": {
        "latitude": 32.7767,
        "longitude": -96.7970,
        "timezone": "America/Chicago",
    }
}

#build full API Call
def build_weather_url(city_name, requested_date):
    city = CITY_COORDINATES[city_name]
    query = {
        "latitude": city["latitude"],
        "longitude": city["longitude"],
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        "temperature_unit": "fahrenheit",
        "wind_speed_unit": "mph",
        "precipitation_unit": "inch",
        "timezone": city["timezone"],
        "start_date": requested_date,
        "end_date": requested_date,
    }

    return "https://api.open-meteo.com/v1/forecast?" + urllib.parse.urlencode(query)

def fetch_weather(city_name, requested_date):
    url = build_weather_url(city_name, requested_date)
    with urllib.request.urlopen(url, timeout=30) as response:
        response_text = response.read().decode("utf-8")

    return {
        "request_url": url,
        "payload": json.loads(response_text),
    }
