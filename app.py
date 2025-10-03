from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.whatsapp_webhook import router as whatsapp_router
from routers.cron import router as cron_router

app = FastAPI(title="MiloBots Chatbot", version="1.0.0")

# CORS (por si querés exponer algo a frontends)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"ok": True}

# Routers
app.include_router(whatsapp_router, prefix="/twilio", tags=["twilio"])
app.include_router(cron_router, prefix="/cron", tags=["cron"])
