# milobots-chatbot

Chatbot generativo para **Milo Bots** (WhatsApp + RAG + Firestore) pensado como **template** reutilizable.

## Stack
- **FastAPI** (webhook Twilio WhatsApp / endpoints internos)
- **OpenAI** (chat + embeddings)
- **FAISS** (vector store local)
- **Firestore** (memoria conversacional, logs, leads)
- **Twilio** (envío/recepción WhatsApp)
- **Render** (deploy) + **cron** vía endpoint `/cron/idle-check`

## Primeros pasos (local)
1. Python 3.11+.
2. `cp .env.example .env` y completar claves (no commitear `.env`).
3. Colocar `serviceAccountKey.json` en la ruta que definas en `GOOGLE_APPLICATION_CREDENTIALS` (ej: `./serviceAccountKey.json` o `/opt/app/serviceAccountKey.json`).
4. Instalar deps: `pip install -r requirements.txt`.
5. Ingestar el contenido inicial para el RAG:
   ```bash
   python vectorstore/ingest_txt.py --input ./data/info_milobots_vectorizable.txt
   ```
6. Correr la app: `uvicorn app:app --host 0.0.0.0 --port 8000 --reload`

## Configuración Twilio (WhatsApp)
- Configurar el **Webhook** entrante en Twilio (WhatsApp Sandbox o número aprobado) apuntando a:
  - `POST {PUBLIC_BASE_URL}/twilio/webhook`
- **FROM** debe ser `whatsapp:+NNNN` (tu línea/sandbox). Ajustarlo en `.env` (`TWILIO_WHATSAPP_FROM`).

> Nota: por tu decisión **omitimos typing/read**.

## Flujo de negocio
- **Consulta general** → RAG (FAISS) + respuesta con tono argentino (voseo).
- **Intención "cotización"** → Mini-form de 4 pasos (Nombre/negocio, Rubro/canal, Contactos por día, Plan).
  Al completar → **aviso out** a `LEADS_WHATSAPP_NUMBER` con resumen.
- **Sin avance** → Aviso out (dos casos):
  - Despedida explícita sin pedir cotización.
  - Inactividad > `SESSION_IDLE_MINUTES` (default 30). Se ejecuta con `/cron/idle-check`.
- **Persistencia** → Firestore (conversaciones, mensajes, leads).
  Se almacena `expire_at` = now + `RETENTION_MONTHS` (24). Configurar **TTL** en Firestore para purgar.

## Deploy en Render
- Crear servicio **Web Service** (Python) con `uvicorn app:app --host 0.0.0.0 --port $PORT`.
- Variables de entorno = `.env` (sin subir secretos a git).
- Montar `serviceAccountKey.json` en `/opt/app/serviceAccountKey.json` (o usar Secret Files).
- Crear un **Cron Job** (o External Cron) que llame `GET {PUBLIC_BASE_URL}/cron/idle-check` cada 5 minutos con header `X-CRON-SECRET: <CRON_SECRET>`.

## Directorios
```
app.py
config.py
routers/
  whatsapp_webhook.py
  cron.py
services/
  twilio_io.py
  rag.py
  embeddings.py
  prompts.py
  memory.py
firestore/
  dao.py
vectorstore/
  ingest_txt.py
  ingest_web.py
data/
  info_milobots_vectorizable.txt
tests/
  test_webhook.py
```

## Seguridad
- **NO** subas `serviceAccountKey.json` ni `.env` al repo.
- Opcional: habilitar `VALIDATE_TWILIO_SIGNATURE=true` y setear `PUBLIC_BASE_URL` para validar el header `X-Twilio-Signature`.

## Licencia
MIT
