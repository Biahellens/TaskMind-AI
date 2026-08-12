export type ToolStatus = "running" | "done" | "error";

export interface ToolCallPart {
  type: "tool";
  id: string;
  name: string;
  input: Record<string, unknown>;
  status: ToolStatus;
  output?: unknown;
}

export interface TextPart {
  type: "text";
  text: string;
}

export type MessagePart = TextPart | ToolCallPart;

export interface DisplayMessage {
  id: string;
  role: "user" | "assistant";
  parts: MessagePart[];
  pending?: boolean;
  error?: string;
}

export interface HistoryMessage {
  role: string;
  content: unknown;
}

export type AgentEvent =
  | { type: "text"; text: string }
  | { type: "tool_call"; id: string; name: string; input: Record<string, unknown> }
  | { type: "tool_result"; id: string; name: string; output: unknown }
  | { type: "done"; messages: HistoryMessage[] }
  | { type: "error"; message: string };
