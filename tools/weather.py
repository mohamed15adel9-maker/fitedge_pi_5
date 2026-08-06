"""
tools/weather.py

Weather tools the LLM can call:
    - get_current_weather(...)
    - get_hourly_weather(...)
    - get_daily_weather(...)
"""

import requests

BASE_URL = "https://api.open-meteo.com/v1/forecast"


def _request(params):
    """Internal helper for making Open-Meteo requests."""
    response = requests.get(BASE_URL, params=params, timeout=10)
    response.raise_for_status()
    return response.json()


def get_current_weather(latitude, longitude):
    """
    Returns the current weather.
    """

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": ",".join([
            "temperature_2m",
            "apparent_temperature",
            "relative_humidity_2m",
            "precipitation",
            "weather_code",
            "wind_speed_10m",
            "uv_index",
        ])
    }

    data = _request(params)
    return data["current"]


def get_hourly_weather(latitude, longitude, hours=24):
    """
    Returns the next few hours of weather.
    Default: next 24 hours.
    """

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "forecast_hours": hours,
        "hourly": ",".join([
            "temperature_2m",
            "apparent_temperature",
            "precipitation_probability",
            "precipitation",
            "weather_code",
            "wind_speed_10m",
            "uv_index",
        ])
    }

    data = _request(params)
    return data["hourly"]


def get_daily_weather(latitude, longitude, days=7):
    """
    Returns the daily forecast.
    Default: next 7 days.
    Maximum supported by Open-Meteo is typically 16 days.
    """

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "forecast_days": days,
        "daily": ",".join([
            "weather_code",
            "temperature_2m_max",
            "temperature_2m_min",
            "apparent_temperature_max",
            "apparent_temperature_min",
            "precipitation_sum",
            "precipitation_probability_max",
            "wind_speed_10m_max",
            "uv_index_max",
            "sunrise",
            "sunset",
        ])
    }

    data = _request(params)
    return data["daily"]