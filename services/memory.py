from datetime import datetime, timezone
from firestore.dao import FirestoreDAO

class MemoryService:
    def __init__(self, dao: FirestoreDAO):
        self.dao = dao

    def get_or_create_session(self, user_phone: str):
        s = self.dao.get_open_session_by_phone(user_phone)
        if s:
            return s
        now = datetime.now(timezone.utc)
        s = {
            "user_phone": user_phone,
            "status": "open",
            "lead_completed": False,
            "alert_no_advance_sent": False,
            "lead_state": {"active": False, "step": 0, "answers": {}},
            "started_at": now.isoformat(),
            "last_msg_at": now.isoformat(),
        }
        return self.dao.create_session(s)

    def update_session(self, session_id: str, data: dict):
        return self.dao.update_session(session_id, data)

    def touch_session(self, session_id: str):
        now = datetime.now(timezone.utc).isoformat()
        return self.dao.update_session(session_id, {"last_msg_at": now})
