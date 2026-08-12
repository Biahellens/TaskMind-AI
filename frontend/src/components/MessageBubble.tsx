import type { DisplayMessage } from "../types";
import { ToolChip } from "./ToolChip";

export function MessageBubble({ message }: { message: DisplayMessage }) {
  const isUser = message.role === "user";
  const isThinking = !isUser && message.pending && message.parts.length === 0;

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={[
          "max-w-[85%] rounded-2xl px-4 py-3 text-[15px] leading-relaxed",
          isUser
            ? "bg-indigo-600 text-white rounded-br-sm"
            : "bg-neutral-900 text-neutral-100 rounded-bl-sm border border-neutral-800",
        ].join(" ")}
      >
        {isThinking && (
          <div className="flex items-center gap-1 py-1">
            <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-neutral-500 [animation-delay:-0.3s]" />
            <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-neutral-500 [animation-delay:-0.15s]" />
            <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-neutral-500" />
          </div>
        )}

        {message.parts.map((part, i) =>
          part.type === "text" ? (
            <p key={i} className="whitespace-pre-wrap [&:not(:first-child)]:mt-2">
              {part.text}
            </p>
          ) : (
            <ToolChip key={part.id} part={part} />
          ),
        )}

        {message.error && (
          <p className="mt-2 text-sm text-red-400">⚠️ {message.error}</p>
        )}
      </div>
    </div>
  );
}
