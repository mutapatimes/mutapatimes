#!/usr/bin/env python3
"""Fetch today's weather for Zimbabwe's main cities from Open-Meteo and
save to data/weather.json for the daily weather card + autolist post.

Open-Meteo is free, no-auth, ECMWF/GFS-backed, generous rate limits.
We pull current + daily high/low/precipitation/code per city in one
batched call (their multi-coordinate endpoint).
"""
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

DATA_DIR = "data"
OUTPUT_FILE = os.path.join(DATA_DIR, "weather.json")

# Zim's main cities, ordered the way the card displays them (top-to-
# bottom, left-to-right in a 2-col grid).
CITIES = [
    {"name": "Harare", "lat": -17.829, "lon": 31.052},
    {"name": "Bulawayo", "lat": -20.149, "lon": 28.580},
    {"name": "Mutare", "lat": -18.970, "lon": 32.650},
    {"name": "Gweru", "lat": -19.450, "lon": 29.820},
    {"name": "Masvingo", "lat": -20.073, "lon": 30.832},
    {"name": "Victoria Falls", "lat": -17.924, "lon": 25.833},
]

# WMO weather codes → (human label, emoji used by the card).
# https://open-meteo.com/en/docs#weathervariables
WEATHER_CODES = {
    0:  ("Clear sky",            "☀️"),
    1:  ("Mainly clear",         "🌤️"),
    2:  ("Partly cloudy",        "⛅"),
    3:  ("Overcast",             "☁️"),
    45: ("Foggy",                "🌫️"),
    48: ("Rime fog",             "🌫️"),
    51: ("Light drizzle",        "🌦️"),
    53: ("Drizzle",              "🌦️"),
    55: ("Heavy drizzle",        "🌧️"),
    56: ("Freezing drizzle",     "🌨️"),
    57: ("Freezing drizzle",     "🌨️"),
    61: ("Light rain",           "🌦️"),
    63: ("Rain",                 "🌧️"),
    65: ("Heavy rain",           "🌧️"),
    66: ("Freezing rain",        "🌨️"),
    67: ("Freezing rain",        "🌨️"),
    71: ("Light snow",           "🌨️"),
    73: ("Snow",                 "❄️"),
    75: ("Heavy snow",           "❄️"),
    77: ("Snow grains",          "❄️"),
    80: ("Light showers",        "🌦️"),
    81: ("Showers",              "🌧️"),
    82: ("Heavy showers",        "🌧️"),
    85: ("Snow showers",         "❄️"),
    86: ("Heavy snow showers",   "❄️"),
    95: ("Thunderstorm",         "⛈️"),
    96: ("Thunderstorm + hail",  "⛈️"),
    99: ("Severe thunderstorm",  "⛈️"),
}


def fetch_one(city):
    """Hit Open-Meteo for a single city. Returns dict or None on failure."""
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={city['lat']}&longitude={city['lon']}"
        "&current=temperature_2m,weather_code,relative_humidity_2m,wind_speed_10m"
        "&daily=temperature_2m_max,temperature_2m_min,weather_code,precipitation_sum,precipitation_probability_max"
        "&timezone=Africa/Harare&forecast_days=1"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "MutapaTimesBot/1.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.load(resp)
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as e:
        print(f"  ERROR {city['name']}: {e}")
        return None

    daily = data.get("daily") or {}
    current = data.get("current") or {}
    code = (daily.get("weather_code") or [None])[0]
    label, emoji = WEATHER_CODES.get(code, ("Unknown", "❓"))
    return {
        "city": city["name"],
        "current_temp": current.get("temperature_2m"),
        "high": (daily.get("temperature_2m_max") or [None])[0],
        "low": (daily.get("temperature_2m_min") or [None])[0],
        "precip_mm": (daily.get("precipitation_sum") or [None])[0],
        "precip_prob": (daily.get("precipitation_probability_max") or [None])[0],
        "humidity": current.get("relative_humidity_2m"),
        "wind_kmh": current.get("wind_speed_10m"),
        "code": code,
        "label": label,
        "emoji": emoji,
    }


def main():
    import argparse
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    ap = argparse.ArgumentParser(description="Fetch weather for a region's cities.")
    ap.add_argument("--region", default="zw")
    region = ap.parse_args().region

    # Region config: cities (name/lat/lon), data dir, timezone. Zimbabwe falls
    # back to the in-file CITIES/DATA_DIR so its weather.json is unchanged.
    city_list, data_dir, tz = CITIES, DATA_DIR, "Africa/Harare"
    try:
        from regions import get_region, region_weather_cities
        r = get_region(region)
        city_list = region_weather_cities(region) or CITIES
        data_dir = r.get("data_dir", DATA_DIR)
        tz = r.get("weather_tz") or ("Africa/Harare" if region == "zw" else "Africa/Johannesburg")
    except ImportError:
        pass
    out_file = os.path.join(data_dir, "weather.json")

    print(f"=== FETCH WEATHER ({region}) ===")
    cities = []
    for city in city_list:
        result = fetch_one(city)
        if result is None:
            print(f"  WARN: dropping {city['name']} (fetch failed)")
            continue
        cities.append(result)
        print(f"  {result['city']:<16} {result['emoji']} {result['label']:<20}"
              f" high {result['high']}°  low {result['low']}°")

    if not cities:
        print("  ERROR: 0 cities fetched — not overwriting existing data")
        sys.exit(1)

    output = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": "https://open-meteo.com/",
        "tz": tz,
        "cities": cities,
    }

    os.makedirs(data_dir, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n  Wrote {out_file} ({len(cities)} cities)")
    print("\n=== DONE ===")


if __name__ == "__main__":
    main()
