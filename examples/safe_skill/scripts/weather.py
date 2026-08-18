import os
import requests


def summarize_weather(city: str) -> str:
    if not city or len(city) > 100:
        raise ValueError("city must be between 1 and 100 characters")
    endpoint = os.getenv("WEATHER_API_URL", "https://example.com/weather")
    try:
        response = requests.get(endpoint, params={"city": city}, timeout=5)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        return f"Weather service unavailable: {exc}"
    return f"{city}: {data.get('summary', 'No summary available')}"

