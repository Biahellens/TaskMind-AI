from app.tools import calendar, email, weather, web_search

TOOLS = [
    weather.TOOL_SPEC,
    web_search.TOOL_SPEC,
    calendar.CREATE_TOOL_SPEC,
    calendar.LIST_TOOL_SPEC,
    email.TOOL_SPEC,
]

EXECUTORS = {
    "get_weather": weather.execute,
    "web_search": web_search.execute,
    "create_calendar_event": calendar.execute_create,
    "list_calendar_events": calendar.execute_list,
    "send_email_summary": email.execute,
}
