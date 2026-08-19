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
        "Creates a calendar event (e.g. a content shoot, a publish date, a "
        "meeting). Use when the user asks to schedule, book, or reserve something."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Event title."},
            "date": {
                "type": "string",
                "description": "Date in YYYY-MM-DD format.",
            },
            "time": {
                "type": "string",
                "description": "Time in HH:MM (24h) format. Optional.",
            },
            "description": {
                "type": "string",
                "description": "Additional event details. Optional.",
            },
        },
        "required": ["title", "date"],
    },
}

LIST_TOOL_SPEC = {
    "name": "list_calendar_events",
    "description": (
        "Lists calendar events. Use when the user asks what's scheduled, whether "
        "a day is free, or wants to see the calendar."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "date": {
                "type": "string",
                "description": (
                    "Filters by an exact date in YYYY-MM-DD format. "
                    "If omitted, returns all upcoming events."
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
        return {"error": True, "message": "Event title cannot be empty."}
    if not _validate_date(event_date):
        return {"error": True, "message": "Invalid date, use YYYY-MM-DD format."}

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
        return {"error": True, "message": "Invalid date, use YYYY-MM-DD format."}

    async with _lock:
        events = _read_events()

    if date_filter:
        events = [e for e in events if e["date"] == date_filter]
    else:
        today_str = date.today().isoformat()
        events = [e for e in events if e["date"] >= today_str][:20]

    return {"count": len(events), "events": events}
