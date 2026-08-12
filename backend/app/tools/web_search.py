import httpx

from app.config import settings

TOOL_SPEC = {
    "name": "web_search",
    "description": (
        "Busca informação atualizada na web. Use quando o usuário pedir algo que "
        "depende de dados recentes: tendências, notícias, estatísticas, preços, "
        "eventos atuais — qualquer coisa que você não teria certeza de saber de cor."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Termos de busca, em linguagem natural.",
            },
            "max_results": {
                "type": "integer",
                "description": "Número máximo de resultados. Padrão: 5.",
            },
        },
        "required": ["query"],
    },
}

BASE_URL = "https://api.tavily.com/search"


async def execute(tool_input: dict) -> dict:
    query = (tool_input.get("query") or "").strip()
    if not query:
        return {"error": True, "message": "Query de busca não pode ser vazia."}

    max_results = tool_input.get("max_results", 5)

    if not settings.tavily_api_key:
        return {"error": True, "message": "TAVILY_API_KEY não configurada no servidor."}

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
            return {"error": True, "message": "Tempo esgotado na busca web."}
        except httpx.HTTPError as exc:
            return {"error": True, "message": f"Falha de rede na busca web: {exc}"}

    if resp.status_code != 200:
        return {"error": True, "message": f"Tavily retornou erro {resp.status_code}."}

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
