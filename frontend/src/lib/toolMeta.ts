export interface ToolMeta {
  icon: string;
  running: string;
  done: string;
}

export const TOOL_META: Record<string, ToolMeta> = {
  get_weather: { icon: "🌤️", running: "Consultando clima...", done: "Clima consultado" },
  web_search: { icon: "🔍", running: "Buscando na web...", done: "Busca concluída" },
  create_calendar_event: { icon: "📅", running: "Criando evento na agenda...", done: "Evento criado" },
  list_calendar_events: { icon: "📅", running: "Consultando agenda...", done: "Agenda consultada" },
  send_email_summary: { icon: "✉️", running: "Enviando e-mail...", done: "E-mail enviado" },
};

export const DEFAULT_TOOL_META: ToolMeta = {
  icon: "🔧",
  running: "Executando ferramenta...",
  done: "Ferramenta concluída",
};

export function getToolMeta(name: string): ToolMeta {
  return TOOL_META[name] ?? DEFAULT_TOOL_META;
}
