import httpx

from app.config import settings

TOOL_SPEC = {
    "name": "web_search",
    "description": (
        "Searches the web for up-to-date information. Use when the user asks for "
        "something that depends on recent data: trends, news, statistics, prices, "
        "current events — anything you wouldn't be confident knowing off the top "
        "of your head."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search terms, in natural language.",
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results. Default: 5.",
            },
        },
        "required": ["query"],
    },
}

BASE_URL = "https://api.tavily.com/search"


async def execute(tool_input: dict) -> dict:
    query = (tool_input.get("query") or "").strip()
    if not query:
        return {"error": True, "message": "Search query cannot be empty."}

    max_results = tool_input.get("max_results", 5)

    if not settings.tavily_api_key:
        return {"error": True, "message": "TAVILY_API_KEY is not configured on the server."}

    payload = {
        "api_key": settings.tavily_api_key,
        "query": query,
        "max_results": max_results,
        "search_depth": "basic",
    }

    async with httpx.AsyncClient(timeout=settings.tool_timeout_seconds) as client:
        try:
            resp = await client.post(BASE_URL, json=payload)
        except httpx.TimeoutException:
            return {"error": True, "message": "Web search timed out."}
        except httpx.HTTPError as exc:
            return {"error": True, "message": f"Network error during web search: {exc}"}

    if resp.status_code != 200:
        return {"error": True, "message": f"Tavily returned an error ({resp.status_code})."}

    data = resp.json()
    results = [
        {
            "title": r.get("title"),
            "url": r.get("url"),
            "snippet": r.get("content"),
        }
        for r in data.get("results", [])
    ]

    return {"query": query, "results": results}
