import type { AgentEvent, HistoryMessage } from "../types";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function streamChat(
  message: string,
  history: HistoryMessage[],
  onEvent: (event: AgentEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const res = await fetch(`${API_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, history }),
    signal,
  });

  if (!res.ok || !res.body) {
    throw new Error(`Backend respondeu ${res.status}`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    let sepIndex: number;
    while ((sepIndex = buffer.indexOf("\n\n")) !== -1) {
      const chunk = buffer.slice(0, sepIndex);
      buffer = buffer.slice(sepIndex + 2);

      const line = chunk.split("\n").find((l) => l.startsWith("data: "));
      if (!line) continue;

      const payload = line.slice("data: ".length);
      try {
        onEvent(JSON.parse(payload) as AgentEvent);
      } catch {
        // ignora chunk malformado, não derruba o stream inteiro
      }
    }
  }
}
