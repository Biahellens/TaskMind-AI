import re

import httpx

from app.config import settings

TOOL_SPEC = {
    "name": "send_email_summary",
    "description": (
        "Sends a real email with a summary or report. Use when the user explicitly "
        "asks to send a summary by email to someone."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "to": {"type": "string", "description": "Recipient's email address."},
            "subject": {"type": "string", "description": "Email subject."},
            "body": {
                "type": "string",
                "description": "Email body, as plain text or light markdown.",
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
        return {"error": True, "message": f"Invalid email address: '{to}'."}
    if not subject:
        return {"error": True, "message": "Subject cannot be empty."}
    if not body:
        return {"error": True, "message": "Email body cannot be empty."}

    if not settings.resend_api_key:
        return {"error": True, "message": "RESEND_API_KEY is not configured on the server."}

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
            return {"error": True, "message": "Timed out sending the email."}
        except httpx.HTTPError as exc:
            return {"error": True, "message": f"Network error sending the email: {exc}"}

    if resp.status_code not in (200, 201):
        return {"error": True, "message": f"Resend returned an error ({resp.status_code}): {resp.text}"}

    data = resp.json()
    return {"sent": True, "to": to, "subject": subject, "provider_id": data.get("id")}
