import { useCallback, useState } from "react";
import { streamChat } from "../lib/api";
import type { DisplayMessage, HistoryMessage } from "../types";

export function useChat() {
  const [messages, setMessages] = useState<DisplayMessage[]>([]);
  const [history, setHistory] = useState<HistoryMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);

  const sendMessage = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || isStreaming) return;

      const userMsg: DisplayMessage = {
        id: crypto.randomUUID(),
        role: "user",
        parts: [{ type: "text", text: trimmed }],
      };
      const assistantId = crypto.randomUUID();
      const assistantMsg: DisplayMessage = {
        id: assistantId,
        role: "assistant",
        parts: [],
        pending: true,
      };

      setMessages((prev) => [...prev, userMsg, assistantMsg]);
      setIsStreaming(true);

      try {
        await streamChat(trimmed, history, (event) => {
          if (event.type === "done") {
            setHistory(event.messages);
          }

          setMessages((prev) =>
            prev.map((m) => {
              if (m.id !== assistantId) return m;

              switch (event.type) {
                case "text":
                  return { ...m, parts: [...m.parts, { type: "text", text: event.text }] };

                case "tool_call":
                  return {
                    ...m,
                    parts: [
                      ...m.parts,
                      {
                        type: "tool",
                        id: event.id,
                        name: event.name,
                        input: event.input,
                        status: "running",
                      },
                    ],
                  };

                case "tool_result":
                  return {
                    ...m,
                    parts: m.parts.map((p) =>
                      p.type === "tool" && p.id === event.id
                        ? {
                            ...p,
                            status:
                              typeof event.output === "object" &&
                              event.output !== null &&
                              (event.output as { error?: boolean }).error
                                ? "error"
                                : "done",
                            output: event.output,
                          }
                        : p,
                    ),
                  };

                case "done":
                  return { ...m, pending: false };

                case "error":
                  return { ...m, pending: false, error: event.message };

                default:
                  return m;
              }
            }),
          );
        });
      } catch (err) {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? { ...m, pending: false, error: err instanceof Error ? err.message : "Unknown error" }
              : m,
          ),
        );
      } finally {
        setIsStreaming(false);
      }
    },
    [history, isStreaming],
  );

  return { messages, sendMessage, isStreaming };
}
