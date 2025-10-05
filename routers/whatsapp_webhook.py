from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from config import settings
from services.twilio_io import send_whatsapp, send_whatsapp_template, validate_twilio_signature
from services.memory import MemoryService
from services.rag import answer_with_rag
from services.prompts import classify_intent, Intent, build_lead_questions, build_lead_summary
from firestore.dao import FirestoreDAO
from datetime import datetime, timezone
import logging

router = APIRouter()


@router.post("/webhook")
async def whatsapp_webhook(request: Request):
    # Validación opcional de firma Twilio
    if settings.VALIDATE_TWILIO_SIGNATURE and not await validate_twilio_signature(request):
        raise HTTPException(status_code=401, detail="Invalid Twilio signature")

    form = await request.form()
    body = (form.get("Body") or "").strip()
    from_raw = (form.get("From") or "")
    profile_name = form.get("ProfileName") or ""
    wa_id = form.get("WaId") or ""

    if not body or not from_raw:
        return JSONResponse({"ok": True, "ignored": True})

    # Estandarizo el número del usuario (sin 'whatsapp:')
    user_phone = from_raw.replace("whatsapp:", "")
    dao = FirestoreDAO()
    memory = MemoryService(dao=dao)

    # Obtener/crear sesión
    session = memory.get_or_create_session(user_phone=user_phone)
    session_id = session["id"]

    # Guardar mensaje entrante
    dao.save_message(session_id=session_id, role="user", text=body, extra={"profile_name": profile_name, "wa_id": wa_id})

    # Si estamos en flujo de LEAD (mini-form), gestionar pasos
    lead_state = session.get("lead_state", {})
    if lead_state.get("active"):
        next_q, updated_state, finished = build_lead_questions(lead_state, user_input=body)
        memory.update_session(session_id, {"lead_state": updated_state})

        if finished:
            # Generar resumen del lead
            summary = build_lead_summary(session, updated_state)
            lead_data = updated_state.get("answers", {})

            # Parámetros de plantilla (deben coincidir con {{1}}..{{5}})
            params = [
                user_phone,
                lead_data.get("q0", "-"),
                lead_data.get("q1", "-"),
                lead_data.get("q2", "-"),
                lead_data.get("q3", "-"),
            ]

            notify_to = settings.LEADS_WHATSAPP_NUMBER or settings.ALERTS_WHATSAPP_NUMBER

            if notify_to:
                try:
                    logging.debug(f"[DEBUG] Enviando plantilla milobots_nuevo_lead_alerta2 a {notify_to} con params: {params}")
                    send_whatsapp_template(notify_to, params)
                except Exception as e:
                    logging.error(f"[ERROR] Falló envío de plantilla a {notify_to}: {e}")
                    # Fallback → texto plano
                    send_whatsapp(notify_to, summary)

            memory.update_session(session_id, {"lead_completed": True, "status": "lead"})
            reply = "¡Gracias! 🙌 Con estos datos ya te contactamos a la brevedad."
            send_whatsapp(user_phone, reply)
            dao.save_message(session_id=session_id, role="bot", text=reply, extra={"lead_completed": True})
            return JSONResponse({"ok": True})

        else:
            send_whatsapp(user_phone, next_q)
            dao.save_message(session_id=session_id, role="bot", text=next_q, extra={"lead_flow": True})
            return JSONResponse({"ok": True})

    # No estamos en flujo lead → clasificar intención
    intent = classify_intent(body)

    if intent == Intent.GOODBYE:
        if not session.get("lead_completed"):
            notify_to = settings.ALERTS_WHATSAPP_NUMBER or settings.LEADS_WHATSAPP_NUMBER
            if notify_to and not session.get("alert_no_advance_sent"):
                msg = f"👋 El cliente {user_phone} se despidió sin pedir cotización."
                send_whatsapp(notify_to, msg)
                memory.update_session(session_id, {"alert_no_advance_sent": True})
        reply = "¡Gracias por escribirnos! Cuando quieras seguimos por acá 🙂"
        send_whatsapp(user_phone, reply)
        dao.save_message(session_id=session_id, role="bot", text=reply)
        memory.update_session(session_id, {"status": "closed"})
        return JSONResponse({"ok": True})

    if intent == Intent.LEAD_INTENT:
        # Inicializar flujo lead
        memory.update_session(session_id, {"lead_state": {"active": True, "step": 0, "answers": {}}, "status": "lead"})
        q, _, _ = build_lead_questions({"active": True, "step": 0, "answers": {}}, user_input=None)
        send_whatsapp(user_phone, q)
        dao.save_message(session_id=session_id, role="bot", text=q, extra={"lead_flow": True})
        return JSONResponse({"ok": True})

    # Caso INFO_QUERY → RAG
    reply, used_chunks = answer_with_rag(user_phone=user_phone, question=body)
    send_whatsapp(user_phone, reply)
    dao.save_message(session_id=session_id, role="bot", text=reply, extra={"chunks_used": used_chunks})
    memory.touch_session(session_id)
    return JSONResponse({"ok": True})
