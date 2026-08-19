import httpx

from app.config import settings

TOOL_SPEC = {
    "name": "get_weather",
    "description": (
        "Checks the current weather for a city. Use when the user asks about "
        "weather conditions, temperature, rain, or needs to decide whether they "
        "can film content outdoors in a given place."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "City name, e.g. 'São Paulo' or 'Lisbon'",
            },
            "units": {
                "type": "string",
                "enum": ["metric", "imperial"],
                "description": "metric = Celsius, imperial = Fahrenheit. Default: metric.",
            },
        },
        "required": ["city"],
    },
}

BASE_URL = "https://api.openweathermap.org/data/2.5/weather"


async def execute(tool_input: dict) -> dict:
    city = (tool_input.get("city") or "").strip()
    if not city:
        return {"error": True, "message": "City name cannot be empty."}

    units = tool_input.get("units", "metric")

    if not settings.openweather_api_key:
        return {"error": True, "message": "OPENWEATHER_API_KEY is not configured on the server."}

    params = {
        "q": city,
        "appid": settings.openweather_api_key,
        "units": units,
        "lang": "en",
    }

    async with httpx.AsyncClient(timeout=settings.tool_timeout_seconds) as client:
        try:
            resp = await client.get(BASE_URL, params=params)
        except httpx.TimeoutException:
            return {"error": True, "message": "Timed out fetching the weather."}
        except httpx.HTTPError as exc:
            return {"error": True, "message": f"Network error fetching the weather: {exc}"}

    if resp.status_code == 404:
        return {"error": True, "message": f"City '{city}' not found."}
    if resp.status_code != 200:
        return {"error": True, "message": f"OpenWeather returned an error ({resp.status_code})."}

    data = resp.json()
    unit_symbol = "°C" if units == "metric" else "°F"

    return {
        "city": data.get("name", city),
        "country": data.get("sys", {}).get("country"),
        "description": data.get("weather", [{}])[0].get("description"),
        "temperature": f"{data.get('main', {}).get('temp')}{unit_symbol}",
        "feels_like": f"{data.get('main', {}).get('feels_like')}{unit_symbol}",
        "humidity": f"{data.get('main', {}).get('humidity')}%",
        "wind_speed": data.get("wind", {}).get("speed"),
    }
