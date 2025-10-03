from enum import Enum
from typing import Dict, Tuple

SYSTEM_PERSONA = """
Sos un asistente de Milo Bots, una agencia que crea chatbots con IA generativa.
Estilo: amable, cercano, profesional, con voseo argentino. Usá **negritas** con moderación.
Nunca inventes precios o promesas fuera del contexto. Si no hay info, pedí aclaración.
"""

ANSWER_INSTRUCTIONS = """
- Respondé en español rioplatense (voseo).
- Sé claro y breve al inicio, y si hace falta ampliá con viñetas.
- Citá **puntos clave** en negrita para resaltar.
- Si el usuario pide una **cotización** o contacto, detectá intención de LEAD.
"""

class Intent(str, Enum):
    INFO_QUERY = "INFO_QUERY"
    LEAD_INTENT = "LEAD_INTENT"
    GOODBYE = "GOODBYE"

GOODBYE_KEYWORDS = [
    "gracias", "muchas gracias", "listo", "saludos", "nos vemos", "chau", "adiós", "hasta luego"
]

LEAD_KEYWORDS = [
    "cotización", "cotizacion", "presupuesto", "quiero un demo", "demo", "contactame", "contactarme",
    "quiero avanzar", "quiero contratar", "me contacten", "quiero que me contacten"
]

def classify_intent(text: str) -> Intent:
    t = text.lower()
    if any(k in t for k in LEAD_KEYWORDS):
        return Intent.LEAD_INTENT
    if any(k in t for k in GOODBYE_KEYWORDS):
        return Intent.GOODBYE
    return Intent.INFO_QUERY

# === Lead mini-form (4 pasos) ===
QUESTIONS = [
    "Dale, avanzamos 😊 ¿Cómo te llamás y cómo se llama tu negocio?",
    "Contame tu *rubro* y el *canal principal* de contacto (por ej., e‑commerce y WhatsApp).",
    "Aproximadamente, ¿cuántos contactos por día reciben?",
    "¿Qué plan te interesa? Elegí: **Plan Base** o **Plan Avanzado**.",
]

def build_lead_questions(state: Dict, user_input: str | None):
    """
    Devuelve: (next_question, new_state, finished)
    state = {"active": True, "step": int, "answers": {}}
    """
    step = state.get("step", 0)
    answers = state.get("answers", {})

    if user_input is not None:
        answers[f"q{step}"] = user_input

    step = step if user_input is None else step + 1

    if step >= len(QUESTIONS):
        # terminado
        return ("", {"active": False, "step": step, "answers": answers}, True)

    return (QUESTIONS[step], {"active": True, "step": step, "answers": answers}, False)

def build_lead_summary(session: Dict, state: Dict) -> str:
    a = state.get("answers", {})
    name_biz = a.get("q0", "-")
    industry = a.get("q1", "-")
    contacts = a.get("q2", "-")
    plan = a.get("q3", "-")

    user_phone = session.get("user_phone", "")
    return (
        "📣 *Nuevo lead para Milo Bots*\n"
        f"- Cliente: {user_phone}\n"
        f"- Nombre y negocio: {name_biz}\n"
        f"- Rubro/canal: {industry}\n"
        f"- Contactos/día: {contacts}\n"
        f"- Plan: {plan}\n"
        f"- Session ID: {session.get('id')}"
    )
