import asyncio
import json
from typing import AsyncGenerator

from anthropic import AsyncAnthropic

from app.config import settings
from app.tools import EXECUTORS, TOOLS

SYSTEM_PROMPT = (
    "Você é o TaskMind, um assistente pessoal para criadores de conteúdo. "
    "Você tem ferramentas reais disponíveis (clima, busca na web, agenda e envio de "
    "e-mail) — use-as sempre que a pergunta do usuário depender de dados externos, "
    "atuais, ou de uma ação concreta (criar evento, enviar e-mail). Não invente dados "
    "que uma ferramenta poderia checar. Responda em português do Brasil, de forma "
    "direta e útil. Depois de usar ferramentas, sempre feche com uma resposta em "
    "texto explicando o resultado para o usuário."
)

client = AsyncAnthropic(api_key=settings.anthropic_api_key)


async def _run_tool(name: str, tool_input: dict) -> dict:
    executor = EXECUTORS.get(name)
    if executor is None:
        return {"error": True, "message": f"Ferramenta desconhecida: {name}"}
    try:
        return await asyncio.wait_for(
            executor(tool_input), timeout=settings.tool_timeout_seconds + 2
        )
    except asyncio.TimeoutError:
        return {"error": True, "message": f"Ferramenta '{name}' excedeu o tempo limite."}
    except Exception as exc:  # tool bugs shouldn't crash the agent loop
        return {"error": True, "message": f"Erro inesperado em '{name}': {exc}"}


async def stream_agent_response(messages: list[dict]) -> AsyncGenerator[dict, None]:
    """
    Roda o loop de tool use da Anthropic, emitindo eventos conforme progride:
    tool_call -> tool_result -> ... -> text -> done.
    `messages` é mutado in-place para acumular o histórico completo do turno.
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
            yield {"type": "error", "message": f"Erro chamando o modelo: {exc}"}
            return

        text_blocks = [b for b in response.content if b.type == "text"]
        tool_blocks = [b for b in response.content if b.type == "tool_use"]

        for block in text_blocks:
            if block.text.strip():
                yield {"type": "text", "text": block.text}

        # Serializa os content blocks pra dict puro, assim `messages` fica
        # JSON-safe do início ao fim (útil pra devolver o histórico ao frontend).
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

    yield {"type": "error", "message": "Limite de iterações do agente atingido."}
