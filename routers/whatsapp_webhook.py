from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from config import settings
from services.twilio_io import send_whatsapp, send_whatsapp_template, validate_twilio_signature
from services.memory import MemoryService
from services.rag import answer_with_rag
from services.prompts import classify_intent, Intent, build_lead_questions, build_lead_summary
from firestore.dao import FirestoreDAO
from datetime import datetime, timezone
import re

router = APIRouter()


@router.post("/webhook")
async def whatsapp_webhook(request: Request):
    # Validación opcional de firma Twilio
    if settings.VALIDATE_TWILIO_SIGNATURE and not await validate_twilio_signature(request):
        raise HTTPException(status_code=401, detail="Invalid Twilio signature")

    form = await request.form()
    body = (form.get("Body") or "").strip()
    from_raw = (form.get("From") or "")
    to_raw = (form.get("To") or "")
    profile_name = form.get("ProfileName") or ""
    wa_id = form.get("WaId") or ""

    if not body or not from_raw:
        return JSONResponse({"ok": True, "ignored": True})

    user_phone = from_raw.replace("whatsapp:", "")
    dao = FirestoreDAO()
    memory = MemoryService(dao=dao)
    session = memory.get_or_create_session(user_phone=user_phone)
    session_id = session["id"]

    # Guardar mensaje entrante
    dao.save_message(session_id=session_id, role="user", text=body, extra={"profile_name": profile_name, "wa_id": wa_id})

    # Primera interacción → bienvenida personalizada
    if session.get("turns", 0) == 0:
        bienvenida = "¡Hola! Soy *Milo*, el asistente de *Milo Bots 🤖*. ¿En qué puedo ayudarte hoy?"
        send_whatsapp(user_phone, bienvenida)
        dao.save_message(session_id=session_id, role="bot", text=bienvenida)
        memory.update_session(session_id, {"turns": 1})
        return JSONResponse({"ok": True})

    # Flujo de lead activo
    lead_state = session.get("lead_state", {})
    if lead_state.get("active"):
        next_q, updated_state, finished = build_lead_questions(lead_state, user_input=body)
        memory.update_session(session_id, {"lead_state": updated_state})
        if finished:
            summary = build_lead_summary(session, updated_state)
            notify_to = settings.LEADS_WHATSAPP_NUMBER or settings.ALERTS_WHATSAPP_NUMBER

            # Intentar enviar mensaje libre y fallback a plantilla
            if notify_to:
                sid = send_whatsapp(notify_to, summary)
                if not sid:
                    send_whatsapp_template(notify_to, "milobots_nuevo_lead_alerta2", [summary])

            memory.update_session(session_id, {"lead_completed": True, "status": "lead"})
            reply = "¡Gracias! 🙌 Con estos datos ya te contactamos a la brevedad."
            send_whatsapp(user_phone, reply)
            dao.save_message(session_id=session_id, role="bot", text=reply, extra={"lead_completed": True})
            return JSONResponse({"ok": True})
        else:
            send_whatsapp(user_phone, next_q)
            dao.save_message(session_id=session_id, role="bot", text=next_q, extra={"lead_flow": True})
            return JSONResponse({"ok": True})

    # Clasificación de intención
    intent = classify_intent(body)

    # Despedida
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

    # Inicio de lead
    if intent == Intent.LEAD_INTENT:
        memory.update_session(session_id, {"lead_state": {"active": True, "step": 0, "answers": {}}, "status": "lead"})
        q, _, _ = build_lead_questions({"active": True, "step": 0, "answers": {}}, user_input=None)
        send_whatsapp(user_phone, q)
        dao.save_message(session_id=session_id, role="bot", text=q, extra={"lead_flow": True})
        return JSONResponse({"ok": True})

    # Consultas informativas (RAG)
    reply, used_chunks = answer_with_rag(user_phone=user_phone, question=body)

    # Validar si el RAG encontró info relevante o si fue tema fuera de contexto
    if not reply or re.search(r"no tengo información|no puedo ayudarte", reply, re.IGNORECASE):
        reply = (
            "No tengo información sobre ese tema 🤔. "
            "Puedo ayudarte con *consultas sobre Milo Bots*, o si querés que te contacten "
            "para una *cotización* de tu chatbot."
        )

    send_whatsapp(user_phone, reply)
    dao.save_message(session_id=session_id, role="bot", text=reply, extra={"chunks_used": used_chunks})
    memory.touch_session(session_id)
    return JSONResponse({"ok": True})
