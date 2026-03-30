# =========================================
# IMPORTS & SETUP
# =========================================
import os
from typing import Dict, List
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import Response, FileResponse
from fastapi.staticfiles import StaticFiles
import subprocess
import requests
import time
import warnings
import json
import logging

SCRIPT_VERSION = "2026-03-30 v15"
print(f"\n=== PHONE AI STARTED - VERSION {SCRIPT_VERSION} ===\n")

BASE_DIR = os.path.dirname(__file__)

# =========================================
# LOGGING (VISIBLE + CLEAN)
# =========================================
import sys
import logging

logging.getLogger("uvicorn.access").disabled = True
logging.getLogger("uvicorn.error").setLevel(logging.WARNING)

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

# =========================================
# FILE LOADERS
# =========================================
def load_file(filename: str, default: str = "") -> str:
    path = os.path.join(BASE_DIR, filename)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    return default

def load_settings():
    settings = {}
    path = os.path.join(BASE_DIR, "phone_settings.txt")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    settings[k.strip()] = v.strip()
    return settings

# =========================================
# CONFIG
# =========================================
SYSTEM_PROMPT = load_file("phone_prompt.txt", "You are a helpful assistant.")
SETTINGS = load_settings()

OLLAMA_MODEL = SETTINGS.get("model", "qwen2.5:1.5b")
TEMPERATURE = float(SETTINGS.get("temperature", "0.2"))
TIMEOUT = int(SETTINGS.get("timeout", "60"))

# =========================================
# OLLAMA START
# =========================================
def start_ollama():
    try:
        requests.get("http://localhost:11434", timeout=2)
        log("Ollama already running")
        return
    except:
        pass

    log("Starting Ollama...")
    subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    for _ in range(30):
        try:
            requests.get("http://localhost:11434", timeout=2)
            log("Ollama started")
            return
        except:
            time.sleep(1)

    raise RuntimeError("Ollama failed to start")

# =========================================
# FASTAPI INIT
# =========================================
app = FastAPI()
warnings.filterwarnings("ignore", message="Unsupported upgrade request")

CALL_SESSIONS: Dict[str, List[dict]] = {}

# =========================================
# HELPERS
# =========================================
def xml_escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&apos;")

# =========================================
# TWIML BUILDER (FIXED TIMING)
# =========================================
def build_twiml(say_text: str = "", end_call: bool = False) -> str:
    say_text = xml_escape(say_text)

    if end_call:
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response><Say voice="alice">{say_text}</Say><Hangup/></Response>"""

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">{say_text}</Say>
    <Gather input="speech" action="/twilio/respond" method="POST"
            speechTimeout="1" timeout="3" bargeIn="true"
            actionOnEmptyResult="true"></Gather>
    <Redirect method="POST">/twilio/respond</Redirect>
</Response>"""

# =========================================
# OLLAMA CHAT
# =========================================
def get_qwen_reply(call_sid: str, user_text: str) -> str:
    if call_sid not in CALL_SESSIONS:
        CALL_SESSIONS[call_sid] = [{"role": "system", "content": SYSTEM_PROMPT}]

    CALL_SESSIONS[call_sid].append({"role": "user", "content": user_text})

    start = time.time()

    try:
        response = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": OLLAMA_MODEL,
                "messages": CALL_SESSIONS[call_sid],
                "options": {"temperature": TEMPERATURE},
                "stream": False
            },
            timeout=TIMEOUT
        )

        duration = round(time.time() - start, 2)

        data = response.json()
        reply = data.get("message", {}).get("content") or data.get("response") or "Sorry, something went wrong."
        reply = reply.strip()

        log(f"{call_sid} | AI ({duration}s): {reply}")

    except Exception as e:
        log(f"{call_sid} | OLLAMA ERROR: {e}")
        reply = "Sorry, something went wrong."

    CALL_SESSIONS[call_sid].append({"role": "assistant", "content": reply})

    return reply

# =========================================
# ROUTES
# =========================================
@app.get("/")
def root():
    return {"status": "ok", "model": OLLAMA_MODEL, "version": SCRIPT_VERSION}

@app.api_route("/twilio", methods=["GET", "POST"])
async def twilio_start():
    log("Incoming call")

    return Response(
        """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">Hello. How can I help you?</Say>
    <Gather input="speech" action="/twilio/respond" method="POST"
            speechTimeout="1" timeout="3" bargeIn="true"
            actionOnEmptyResult="true"></Gather>
    <Redirect method="POST">/twilio/respond</Redirect>
</Response>""",
        media_type="application/xml"
    )

@app.post("/twilio/respond")
async def twilio_respond(request: Request):
    form = await request.form()

    call_sid = str(form.get("CallSid", "default_call"))
    speech = str(form.get("SpeechResult", "")).strip()

    if not speech:
        log(f"{call_sid} | No speech detected")
        return Response(build_twiml("I didn't catch that. Please repeat."), media_type="application/xml")

    log(f"{call_sid} | User: {speech}")

    if speech.lower() in {"bye", "goodbye", "stop", "hang up"}:
        CALL_SESSIONS.pop(call_sid, None)
        log(f"{call_sid} | Call ended")
        return Response(build_twiml("Goodbye.", end_call=True), media_type="application/xml")

    reply = get_qwen_reply(call_sid, speech)

    return Response(build_twiml(reply), media_type="application/xml")

# =========================================
# WEBSOCKET (UNCHANGED)
# =========================================
@app.websocket("/audio")
async def audio_stream(ws: WebSocket):
    await ws.accept()
    log("Media stream connected")

    try:
        while True:
            data = await ws.receive_text()
            msg = json.loads(data)

            if msg.get("event") == "start":
                log("Stream started")

            elif msg.get("event") == "stop":
                log("Stream stopped")
                break

    except WebSocketDisconnect:
        log("WebSocket disconnected")

# =========================================
# DASHBOARD
# =========================================
DASHBOARD_DIR = os.path.join(BASE_DIR, "dashboard")

app.mount("/dashboard/static", StaticFiles(directory=DASHBOARD_DIR), name="dashboard_static")

@app.get("/dashboard")
def dashboard():
    return FileResponse(os.path.join(DASHBOARD_DIR, "index.html"))

@app.get("/dashboard/data")
def dashboard_data():
    return CALL_SESSIONS

# =========================================
# START
# =========================================
start_ollama()