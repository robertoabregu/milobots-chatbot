from fastapi import APIRouter, Header, HTTPException
from dateutil import tz
from datetime import datetime, timedelta, timezone
from config import settings
from firestore.dao import FirestoreDAO
from services.twilio_io import send_whatsapp

router = APIRouter()

@router.get("/idle-check")
def idle_check(x_cron_secret: str | None = Header(default=None)):
    if settings.CRON_SECRET and x_cron_secret != settings.CRON_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")
    dao = FirestoreDAO()
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(minutes=settings.SESSION_IDLE_MINUTES)
    sessions = dao.find_idle_open_sessions(cutoff=cutoff)

    count = 0
    for s in sessions:
        # solo alertar si no hubo lead
        if not s.get("lead_completed") and not s.get("alert_no_advance_sent"):
            user_phone = s.get("user_phone")
            msg = f"⚠️ Aviso: contacto sin avance.\nCliente: {user_phone}\nÚltima actividad: {s.get('last_msg_at')}"
            send_whatsapp(settings.LEADS_WHATSAPP_NUMBER or settings.ALERTS_WHATSAPP_NUMBER, msg)
            dao.mark_alert_no_advance_sent(s["id"])
            count += 1

    return {"ok": True, "alerts_sent": count}
