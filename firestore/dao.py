from __future__ import annotations
from typing import Dict, List, Optional
from datetime import datetime, timedelta, timezone
import firebase_admin
from firebase_admin import credentials, firestore
from config import settings

# Inicializar Firebase app (singleton)
if not firebase_admin._apps:
    cred = credentials.Certificate(settings.GOOGLE_APPLICATION_CREDENTIALS)
    firebase_admin.initialize_app(cred, {
        "projectId": settings.GOOGLE_PROJECT_ID
    })

db = firestore.client()
COL_PREFIX = settings.FIRESTORE_COLLECTION_PREFIX

def _col(name: str):
    return f"{COL_PREFIX}_{name}" if COL_PREFIX else name

class FirestoreDAO:
    def __init__(self):
        self.conv_col = db.collection(_col("conversations"))
        self.leads_col = db.collection(_col("leads"))

    def create_session(self, data: Dict) -> Dict:
        doc_ref = self.conv_col.document()
        data["id"] = doc_ref.id
        now = datetime.now(timezone.utc)
        expire_at = now + timedelta(days=30*settings.RETENTION_MONTHS)
        data["expire_at"] = expire_at
        doc_ref.set(data)
        return data

    def update_session(self, session_id: str, patch: Dict):
        doc_ref = self.conv_col.document(session_id)
        patch["updated_at"] = datetime.now(timezone.utc)
        doc_ref.set(patch, merge=True)
        d = doc_ref.get().to_dict() or {}
        d["id"] = session_id
        return d

    def get_open_session_by_phone(self, user_phone: str) -> Optional[Dict]:
        qs = self.conv_col.where("user_phone", "==", user_phone).where("status", "in", ["open", "lead"]).limit(1).stream()
        for doc in qs:
            d = doc.to_dict()
            d["id"] = doc.id
            return d
        return None

    def save_message(self, session_id: str, role: str, text: str, extra: Dict | None = None):
        ref = self.conv_col.document(session_id).collection("messages").document()
        payload = {
            "role": role,
            "text": text,
            "created_at": datetime.now(timezone.utc),
        }
        if extra:
            payload.update(extra)
        ref.set(payload)
        # touch last_msg_at
        self.update_session(session_id, {"last_msg_at": datetime.now(timezone.utc).isoformat()})

    def find_idle_open_sessions(self, cutoff):
        qs = self.conv_col.where("status", "in", ["open", "lead"]).where("last_msg_at", "<", cutoff.isoformat()).stream()
        results = []
        for doc in qs:
            d = doc.to_dict()
            d["id"] = doc.id
            results.append(d)
        return results

    def mark_alert_no_advance_sent(self, session_id: str):
        self.update_session(session_id, {"alert_no_advance_sent": True})
