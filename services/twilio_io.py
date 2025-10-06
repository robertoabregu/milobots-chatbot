from config import settings
from twilio.rest import Client
from fastapi import Request
from twilio.request_validator import RequestValidator
import logging
import json

# Inicializo cliente Twilio
client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)


def send_whatsapp(to_number: str, body: str):
    """
    Envía un mensaje de WhatsApp libre via Twilio (solo válido dentro de la ventana de 24 hs).
    """
    if not to_number.startswith("whatsapp:"):
        to = f"whatsapp:{to_number}"
    else:
        to = to_number

    try:
        msg = client.messages.create(
            from_=settings.TWILIO_WHATSAPP_FROM,
            to=to,
            body=body,
        )
        logging.info(f"[Twilio] Mensaje libre enviado a {to}: {body} – SID={msg.sid}")
    except Exception as e:
        logging.error(f"[Twilio ERROR] No se pudo enviar mensaje libre a {to}: {e}")


def send_whatsapp_template(to_number: str, params: list):
    """
    Envía una plantilla de WhatsApp (Content Template) usando Twilio.
    Usa el template aprobado 'milobots_nuevo_lead_alerta5' (tipo Utility).
    Solo requiere dos parámetros:
      params[0] = número del cliente WhatsApp
      params[1] = nombre y negocio
    """
    if not to_number.startswith("whatsapp:"):
        to = f"whatsapp:{to_number}"
    else:
        to = to_number

    # SID del template aprobado en Twilio (Utility)
    CONTENT_SID = "HXdb8083414adc340bcb3bb6094784513e"  # ⚠️ reemplazá con el SID exacto que aparece en Twilio

    # Variables dinámicas del template
    content_variables = {
        "1": params[0],  # Cliente WhatsApp
        "2": params[1],  # Nombre y negocio
    }

    try:
        message = client.messages.create(
            from_=settings.TWILIO_WHATSAPP_FROM,
            to=to,
            content_sid=CONTENT_SID,
            content_variables=json.dumps(content_variables),
        )

        logging.info(
            f"[Twilio] ✅ Plantilla 'milobots_nuevo_lead_alerta6' enviada correctamente a {to} con parámetros {params} – SID={message.sid}"
        )

    except Exception as e:
        logging.error(
            f"[Twilio ERROR] ❌ No se pudo enviar plantilla 'milobots_nuevo_lead_alerta6' a {to}: {e}"
        )


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
