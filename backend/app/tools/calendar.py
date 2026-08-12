import asyncio
import json
import uuid
from datetime import date, datetime
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "events.json"
_lock = asyncio.Lock()

CREATE_TOOL_SPEC = {
    "name": "create_calendar_event",
    "description": (
        "Cria um evento na agenda (ex: gravação de conteúdo, publicação, reunião). "
        "Use quando o usuário pedir para agendar, marcar ou reservar algo."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Título do evento."},
            "date": {
                "type": "string",
                "description": "Data no formato YYYY-MM-DD.",
            },
            "time": {
                "type": "string",
                "description": "Horário no formato HH:MM (24h). Opcional.",
            },
            "description": {
                "type": "string",
                "description": "Detalhes adicionais do evento. Opcional.",
            },
        },
        "required": ["title", "date"],
    },
}

LIST_TOOL_SPEC = {
    "name": "list_calendar_events",
    "description": (
        "Lista eventos da agenda. Use quando o usuário perguntar o que tem marcado, "
        "se um dia está livre, ou quiser ver a agenda."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "date": {
                "type": "string",
                "description": (
                    "Filtra por uma data exata no formato YYYY-MM-DD. "
                    "Se omitido, retorna todos os próximos eventos."
                ),
            },
        },
        "required": [],
    },
}


def _read_events() -> list[dict]:
    if not DATA_FILE.exists():
        return []
    with DATA_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def _write_events(events: list[dict]) -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with DATA_FILE.open("w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=2)


def _validate_date(value: str) -> bool:
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except ValueError:
        return False


async def execute_create(tool_input: dict) -> dict:
    title = (tool_input.get("title") or "").strip()
    event_date = (tool_input.get("date") or "").strip()

    if not title:
        return {"error": True, "message": "Título do evento não pode ser vazio."}
    if not _validate_date(event_date):
        return {"error": True, "message": "Data inválida, use o formato YYYY-MM-DD."}

    event = {
        "id": str(uuid.uuid4())[:8],
        "title": title,
        "date": event_date,
        "time": tool_input.get("time"),
        "description": tool_input.get("description"),
    }

    async with _lock:
        events = _read_events()
        events.append(event)
        events.sort(key=lambda e: (e["date"], e.get("time") or ""))
        _write_events(events)

    return {"created": True, "event": event}


async def execute_list(tool_input: dict) -> dict:
    date_filter = tool_input.get("date")
    if date_filter and not _validate_date(date_filter):
        return {"error": True, "message": "Data inválida, use o formato YYYY-MM-DD."}

    async with _lock:
        events = _read_events()

    if date_filter:
        events = [e for e in events if e["date"] == date_filter]
    else:
        today_str = date.today().isoformat()
        events = [e for e in events if e["date"] >= today_str][:20]

    return {"count": len(events), "events": events}
