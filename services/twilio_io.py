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
    Envía un mensaje de WhatsApp via Twilio.
    - 'to_number' puede venir como '+54911....' (se agrega 'whatsapp:' automáticamente)
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
        logging.info(f"[Twilio] Mensaje enviado a {to}: {body} – SID={msg.sid}")
    except Exception as e:
        logging.error(f"[Twilio ERROR] No se pudo enviar mensaje a {to}: {e}")


def send_whatsapp_template(to_number: str, params: list):
    """
    Envía una plantilla de WhatsApp (Content Template) usando Twilio.
    Usa el content_sid del template 'milobots_nuevo_lead_alerta2'.
    Los parámetros deben coincidir con las variables {{1}}, {{2}}, etc.
    """
    if not to_number.startswith("whatsapp:"):
        to = f"whatsapp:{to_number}"
    else:
        to = to_number

    # SID del template aprobado en Twilio
    CONTENT_SID = "HX80dccae55dcbfc0cce3a3ae87e28b3fa"  # ⚠️ reemplazá con el SID completo exacto de tu plantilla

    # Variables dinámicas del template (JSON string)
    content_variables = {
        "1": params[0],  # Cliente WhatsApp
        "2": params[1],  # Nombre y negocio
        "3": params[2],  # Rubro/canal
        "4": params[3],  # Contactos por día
        "5": params[4],  # Plan
    }

    try:
        message = client.messages.create(
            from_=settings.TWILIO_WHATSAPP_FROM,
            to=to,
            content_sid=CONTENT_SID,
            content_variables=json.dumps(content_variables),
        )

        logging.info(
            f"[Twilio] ✅ Plantilla 'milobots_nuevo_lead_alerta2' enviada correctamente a {to} con parámetros {params} – SID={message.sid}"
        )

    except Exception as e:
        logging.error(
            f"[Twilio ERROR] No se pudo enviar plantilla 'milobots_nuevo_lead_alerta2' a {to}: {e}"
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
