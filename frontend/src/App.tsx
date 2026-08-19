import { useEffect, useRef } from "react";
import { ChatInput } from "./components/ChatInput";
import { Header } from "./components/Header";
import { MessageBubble } from "./components/MessageBubble";
import { useChat } from "./hooks/useChat";

const QUICK_PROMPTS = [
  "What's the weather like in Lisbon today?",
  "Search for AI content trends this week",
  "Schedule a shoot for Friday at 3pm and send me a summary by email",
];

function App() {
  const { messages, sendMessage, isStreaming } = useChat();
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="mx-auto flex h-screen max-w-2xl flex-col">
      <Header />

      <div className="flex-1 space-y-3 overflow-y-auto px-4 py-4">
        {messages.length === 0 && (
          <div className="flex h-full flex-col items-center justify-center gap-4 text-center">
            <p className="text-sm text-neutral-500">
              Ask something that requires a real action — weather, web search, calendar or email.
            </p>
            <div className="flex flex-wrap justify-center gap-2">
              {QUICK_PROMPTS.map((prompt) => (
                <button
                  key={prompt}
                  onClick={() => sendMessage(prompt)}
                  className="rounded-full border border-neutral-800 bg-neutral-900 px-3 py-1.5 text-xs text-neutral-300 transition hover:border-indigo-500 hover:text-white"
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m) => (
          <MessageBubble key={m.id} message={m} />
        ))}
        <div ref={bottomRef} />
      </div>

      <ChatInput onSend={sendMessage} disabled={isStreaming} />
    </div>
  );
}

export default App;
