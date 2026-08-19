export interface ToolMeta {
  icon: string;
  running: string;
  done: string;
}

export const TOOL_META: Record<string, ToolMeta> = {
  get_weather: { icon: "🌤️", running: "Checking the weather...", done: "Weather checked" },
  web_search: { icon: "🔍", running: "Searching the web...", done: "Web search done" },
  create_calendar_event: { icon: "📅", running: "Creating calendar event...", done: "Event created" },
  list_calendar_events: { icon: "📅", running: "Checking the calendar...", done: "Calendar checked" },
  send_email_summary: { icon: "✉️", running: "Sending email...", done: "Email sent" },
};

export const DEFAULT_TOOL_META: ToolMeta = {
  icon: "🔧",
  running: "Running tool...",
  done: "Tool completed",
};

export function getToolMeta(name: string): ToolMeta {
  return TOOL_META[name] ?? DEFAULT_TOOL_META;
}
