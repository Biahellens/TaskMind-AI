import re

import httpx

from app.config import settings

TOOL_SPEC = {
    "name": "send_email_summary",
    "description": (
        "Envia um e-mail real com um resumo ou relatório. Use quando o usuário pedir "
        "explicitamente para mandar/enviar um resumo por e-mail para alguém."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "to": {"type": "string", "description": "E-mail do destinatário."},
            "subject": {"type": "string", "description": "Assunto do e-mail."},
            "body": {
                "type": "string",
                "description": "Corpo do e-mail em texto simples ou markdown leve.",
            },
        },
        "required": ["to", "subject", "body"],
    },
}

BASE_URL = "https://api.resend.com/emails"
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


async def execute(tool_input: dict) -> dict:
    to = (tool_input.get("to") or "").strip()
    subject = (tool_input.get("subject") or "").strip()
    body = (tool_input.get("body") or "").strip()

    if not EMAIL_RE.match(to):
        return {"error": True, "message": f"Endereço de e-mail inválido: '{to}'."}
    if not subject:
        return {"error": True, "message": "Assunto não pode ser vazio."}
    if not body:
        return {"error": True, "message": "Corpo do e-mail não pode ser vazio."}

    if not settings.resend_api_key:
        return {"error": True, "message": "RESEND_API_KEY não configurada no servidor."}

    payload = {
        "from": settings.resend_from_email,
        "to": [to],
        "subject": subject,
        "text": body,
    }
    headers = {"Authorization": f"Bearer {settings.resend_api_key}"}

    async with httpx.AsyncClient(timeout=settings.tool_timeout_seconds) as client:
        try:
            resp = await client.post(BASE_URL, json=payload, headers=headers)
        except httpx.TimeoutException:
            return {"error": True, "message": "Tempo esgotado enviando o e-mail."}
        except httpx.HTTPError as exc:
            return {"error": True, "message": f"Falha de rede ao enviar e-mail: {exc}"}

    if resp.status_code not in (200, 201):
        return {"error": True, "message": f"Resend retornou erro {resp.status_code}: {resp.text}"}

    data = resp.json()
    return {"sent": True, "to": to, "subject": subject, "provider_id": data.get("id")}
