import httpx

from app.config import settings

TOOL_SPEC = {
    "name": "get_weather",
    "description": (
        "Consulta o clima atual de uma cidade. Use quando o usuário perguntar sobre "
        "condições climáticas, temperatura, chuva, ou precisar decidir se pode gravar "
        "conteúdo externo em determinado lugar."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "Nome da cidade, ex: 'São Paulo' ou 'Lisboa'",
            },
            "units": {
                "type": "string",
                "enum": ["metric", "imperial"],
                "description": "metric = Celsius, imperial = Fahrenheit. Padrão: metric.",
            },
        },
        "required": ["city"],
    },
}

BASE_URL = "https://api.openweathermap.org/data/2.5/weather"


async def execute(tool_input: dict) -> dict:
    city = (tool_input.get("city") or "").strip()
    if not city:
        return {"error": True, "message": "Nome da cidade não pode ser vazio."}

    units = tool_input.get("units", "metric")

    if not settings.openweather_api_key:
        return {"error": True, "message": "OPENWEATHER_API_KEY não configurada no servidor."}

    params = {
        "q": city,
        "appid": settings.openweather_api_key,
        "units": units,
        "lang": "pt_br",
    }

    async with httpx.AsyncClient(timeout=settings.tool_timeout_seconds) as client:
        try:
            resp = await client.get(BASE_URL, params=params)
        except httpx.TimeoutException:
            return {"error": True, "message": "Tempo esgotado consultando o clima."}
        except httpx.HTTPError as exc:
            return {"error": True, "message": f"Falha de rede ao consultar o clima: {exc}"}

    if resp.status_code == 404:
        return {"error": True, "message": f"Cidade '{city}' não encontrada."}
    if resp.status_code != 200:
        return {"error": True, "message": f"OpenWeather retornou erro {resp.status_code}."}

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
