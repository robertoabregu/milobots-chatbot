from config import settings
from twilio.rest import Client
from fastapi import Request
from twilio.request_validator import RequestValidator

client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

def send_whatsapp(to_number: str, body: str):
    """
    Envía un mensaje de WhatsApp via Twilio.
    - to_number: puede venir como '+54911....' (agregamos 'whatsapp:' acá)
    - from_: asegúrate que tenga también el prefijo 'whatsapp:'
    """
    if not to_number.startswith("whatsapp:"):
        to = f"whatsapp:{to_number}"
    else:
        to = to_number

    from_number = settings.TWILIO_WHATSAPP_FROM
    if not from_number.startswith("whatsapp:"):
        from_number = f"whatsapp:{from_number}"

    msg = client.messages.create(
        from_=from_number,
        to=to,
        body=body,
    )

    # Log para debugging en Render
    print(f"[Twilio] Mensaje enviado a {to}: {body[:50]}... SID={msg.sid}")

async def validate_twilio_signature(request: Request) -> bool:
    """
    Validación opcional de la firma X-Twilio-Signature.
    Requiere PUBLIC_BASE_URL y TWILIO_AUTH_TOKEN.
    """
    if not settings.PUBLIC_BASE_URL or not settings.TWILIO_AUTH_TOKEN:
        return False

    validator = RequestValidator(settings.TWILIO_AUTH_TOKEN)
    signature = request.headers.get("X-Twilio-Signature", "")
    # Reconstruir URL absoluta
    url = settings.PUBLIC_BASE_URL.rstrip("/") + str(request.url.path)
    form = await request.form()
    form_data = dict(form)
    try:
        return validator.validate(url, form_data, signature)
    except Exception:
        return False
