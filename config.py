import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_WHATSAPP_FROM: str = os.getenv("TWILIO_WHATSAPP_FROM", "")
    PUBLIC_BASE_URL: str = os.getenv("PUBLIC_BASE_URL", "")

    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    OPENAI_EMBEDDING_MODEL: str = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

    GOOGLE_PROJECT_ID: str = os.getenv("GOOGLE_PROJECT_ID", "")
    GOOGLE_APPLICATION_CREDENTIALS: str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    FIRESTORE_COLLECTION_PREFIX: str = os.getenv("FIRESTORE_COLLECTION_PREFIX", "milobots")

    VECTORSTORE_PATH: str = os.getenv("VECTORSTORE_PATH", "./vectorstore/index.faiss")
    DOCS_PATH: str = os.getenv("DOCS_PATH", "./data")

    ALERTS_WHATSAPP_NUMBER: str = os.getenv("ALERTS_WHATSAPP_NUMBER", "")
    LEADS_WHATSAPP_NUMBER: str = os.getenv("LEADS_WHATSAPP_NUMBER", "")
    SESSION_IDLE_MINUTES: int = int(os.getenv("SESSION_IDLE_MINUTES", "30"))
    RETENTION_MONTHS: int = int(os.getenv("RETENTION_MONTHS", "24"))

    CRON_SECRET: str = os.getenv("CRON_SECRET", "")
    VALIDATE_TWILIO_SIGNATURE: bool = os.getenv("VALIDATE_TWILIO_SIGNATURE", "false").lower() == "true"

settings = Settings()
