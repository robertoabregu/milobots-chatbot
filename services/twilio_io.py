from config import settings
from twilio.rest import Client
from fastapi import Request
from twilio.request_validator import RequestValidator

client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

def send_whatsapp(to_number: str, body: str):
    """
    Envía un mensaje de WhatsApp libre (freeform) via Twilio.
    Solo funciona dentro de la ventana de 24 hs desde la última interacción del usuario.
    """
    if not to_number.startswith("whatsapp:"):
        to_number = f"whatsapp:{to_number}"

    try:
        msg = client.messages.create(
            from_=settings.TWILIO_WHATSAPP_FROM,
            to=to_number,
            body=body,
        )
        print(f"[Twilio] Mensaje enviado a {to_number}: {body} — SID={msg.sid}")
        return msg.sid
    except Exception as e:
        print(f"[Twilio ERROR] No se pudo enviar mensaje a {to_number}: {e}")
        return None


def send_whatsapp_template(to_number: str, template_name: str, parameters: list):
    """
    Envía un mensaje usando una plantilla aprobada de WhatsApp.
    Útil cuando se quiere contactar a un usuario fuera de la ventana de 24 hs.
    - template_name: nombre de la plantilla configurada en Meta/Twilio.
    - parameters: lista de valores que reemplazan los {{1}}, {{2}}, etc.
    """
    if not to_number.startswith("whatsapp:"):
        to_number = f"whatsapp:{to_number}"

    try:
        msg = client.messages.create(
            from_=settings.TWILIO_WHATSAPP_FROM,
            to=to_number,
            messaging_product="whatsapp",
            # Formato de plantilla (HSM)
            template={
                "name": template_name,
                "language": {"code": "es"},
                "components": [
                    {
                        "type": "body",
                        "parameters": [{"type": "text", "text": p} for p in parameters],
                    }
                ],
            },
        )
        print(f"[Twilio] Plantilla '{template_name}' enviada a {to_number} — SID={msg.sid}")
        return msg.sid
    except Exception as e:
        print(f"[Twilio ERROR] No se pudo enviar plantilla '{template_name}' a {to_number}: {e}")
        return None


async def validate_twilio_signature(request: Request) -> bool:
    """
    Validación opcional de la firma X-Twilio-Signature.
    Requiere PUBLIC_BASE_URL y TWILIO_AUTH_TOKEN.
    """
    if not settings.PUBLIC_BASE_URL or not settings.TWILIO_AUTH_TOKEN:
        return False

    validator = RequestValidator(settings.TWILIO_AUTH_TOKEN)
    signature = request.headers.get("X-Twilio-Signature", "")
    url = settings.PUBLIC_BASE_URL.rstrip("/") + str(request.url.path)
    form = await request.form()
    form_data = dict(form)
    try:
        return validator.validate(url, form_data, signature)
    except Exception:
        return False
