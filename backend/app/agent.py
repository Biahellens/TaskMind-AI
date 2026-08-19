import asyncio
import json
from typing import AsyncGenerator

from anthropic import AsyncAnthropic

from app.config import settings
from app.tools import EXECUTORS, TOOLS

SYSTEM_PROMPT = (
    "You are TaskMind, a personal assistant for content creators. "
    "You have real tools available (weather, web search, calendar and email) — "
    "use them whenever the user's question depends on external or current data, "
    "or on taking a concrete action (creating an event, sending an email). "
    "Don't make up data that a tool could check. Reply in English, directly and "
    "helpfully. After using tools, always close with a text response explaining "
    "the result to the user."
)

client = AsyncAnthropic(api_key=settings.anthropic_api_key)


async def _run_tool(name: str, tool_input: dict) -> dict:
    executor = EXECUTORS.get(name)
    if executor is None:
        return {"error": True, "message": f"Unknown tool: {name}"}
    try:
        return await asyncio.wait_for(
            executor(tool_input), timeout=settings.tool_timeout_seconds + 2
        )
    except asyncio.TimeoutError:
        return {"error": True, "message": f"Tool '{name}' timed out."}
    except Exception as exc:  # tool bugs shouldn't crash the agent loop
        return {"error": True, "message": f"Unexpected error in '{name}': {exc}"}


async def stream_agent_response(messages: list[dict]) -> AsyncGenerator[dict, None]:
    """
    Runs the Anthropic tool use loop, emitting events as it progresses:
    tool_call -> tool_result -> ... -> text -> done.
    `messages` is mutated in-place to accumulate the turn's full history.
    """
    for _ in range(settings.max_agent_rounds):
        try:
            response = await client.messages.create(
                model=settings.model_name,
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=messages,
            )
        except Exception as exc:
            yield {"type": "error", "message": f"Error calling the model: {exc}"}
            return

        text_blocks = [b for b in response.content if b.type == "text"]
        tool_blocks = [b for b in response.content if b.type == "tool_use"]

        for block in text_blocks:
            if block.text.strip():
                yield {"type": "text", "text": block.text}

        # Serialize content blocks into plain dicts, so `messages` stays
        # JSON-safe end to end (needed to return the history to the frontend).
        messages.append(
            {"role": "assistant", "content": [b.model_dump() for b in response.content]}
        )

        if response.stop_reason != "tool_use":
            yield {"type": "done", "messages": messages}
            return

        tool_result_contents = []
        for block in tool_blocks:
            yield {"type": "tool_call", "id": block.id, "name": block.name, "input": block.input}

            result = await _run_tool(block.name, block.input)

            yield {"type": "tool_result", "id": block.id, "name": block.name, "output": result}

            tool_result_contents.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result, ensure_ascii=False),
                    "is_error": bool(result.get("error")),
                }
            )

        messages.append({"role": "user", "content": tool_result_contents})

    yield {"type": "error", "message": "Agent iteration limit reached."}
