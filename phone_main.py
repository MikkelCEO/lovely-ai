import os
from typing import Dict, List
from fastapi import FastAPI, Request
from fastapi.responses import Response
import subprocess
import requests
import time
import warnings

SCRIPT_VERSION = "2026-03-26 v8"

print(f"=== TWILIO PHONE SCRIPT STARTED - VERSION {SCRIPT_VERSION} ===")

BASE_DIR = os.path.dirname(__file__)

# =========================================
# LOAD FILES
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
# LOAD RUNTIME CONFIG (NAS)
# =========================================

def load_runtime_config():
    config = {}
    path = "/volume1/Projects/ai-chat/Phone/config.txt"
    if os.path.exists(path):
        with open(path, "r") as f:
            for line in f:
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    config[k] = v
    return config

RUNTIME_CONFIG = load_runtime_config()

# =========================================
# SETTINGS
# =========================================

SYSTEM_PROMPT = load_file("phone_prompt.txt", "You are a helpful assistant.")
SETTINGS = load_settings()

OLLAMA_MODEL = SETTINGS.get("model", "qwen2.5:3b")
TEMPERATURE = float(SETTINGS.get("temperature", "0.2"))
TIMEOUT = int(SETTINGS.get("timeout", "60"))

# =========================================
# OLLAMA START
# =========================================

def start_ollama():
    try:
        requests.get("http://localhost:11434", timeout=2)
        print("Ollama already running")
        return
    except:
        pass

    print("Starting Ollama...")
    subprocess.Popen(
        ["ollama", "serve"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    for _ in range(30):
        try:
            requests.get("http://localhost:11434", timeout=2)
            print("Ollama started")
            return
        except:
            time.sleep(1)

    raise RuntimeError("Ollama failed to start")

# =========================================
# WHISPER (STT)
# =========================================

from faster_whisper import WhisperModel

print("Loading Whisper model...")
whisper_model = WhisperModel("base", compute_type="int8")
print("Whisper ready")

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
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )

def build_twiml(say_text: str = "", action_url: str = "/twilio/respond", end_call: bool = False) -> str:
    say_text = xml_escape(say_text)

    if end_call:
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response><Say voice="alice">{say_text}</Say><Hangup/></Response>"""

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">{say_text}</Say>
    <Gather input="speech" action="{action_url}" method="POST" speechTimeout="auto" timeout="5" bargeIn="true"></Gather>
    <Redirect method="POST">{action_url}</Redirect>
</Response>"""

# =========================================
# LLM CALL
# =========================================

def get_qwen_reply(call_sid: str, user_text: str) -> str:
    if call_sid not in CALL_SESSIONS:
        CALL_SESSIONS[call_sid] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

    CALL_SESSIONS[call_sid].append(
        {"role": "user", "content": user_text}
    )

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

        data = response.json()

        reply = (
            data.get("message", {}).get("content")
            or data.get("response")
            or "Sorry, something went wrong."
        )

        if isinstance(reply, dict):
            reply = str(reply)

        reply = reply.strip()

    except Exception as e:
        print("OLLAMA ERROR:", e)
        reply = "Sorry, something went wrong."

    CALL_SESSIONS[call_sid].append(
        {"role": "assistant", "content": reply}
    )

    return reply

# =========================================
# ROUTES
# =========================================

@app.get("/")
def root():
    return {
        "status": "ok",
        "model": OLLAMA_MODEL,
        "version": SCRIPT_VERSION,
        "runtime": RUNTIME_CONFIG
    }

@app.api_route("/twilio", methods=["GET", "POST"])
async def twilio_start():
    return Response(
        """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Connect>
        <Stream url="wss://yoq3lb2gydc1oy-8000.proxy.runpod.net/audio" />
    </Connect>
</Response>""",
        media_type="application/xml"
    )

@app.post("/twilio/respond")
async def twilio_respond(request: Request):
    form = await request.form()

    call_sid = str(form.get("CallSid", "default_call"))
    speech = str(form.get("SpeechResult", "")).strip()

    if not speech:
        return Response(
            build_twiml("I didn't catch that. Please speak again."),
            media_type="application/xml"
        )

    if speech.lower() in {"bye", "goodbye", "stop", "hang up"}:
        CALL_SESSIONS.pop(call_sid, None)
        return Response(
            build_twiml("Goodbye.", end_call=True),
            media_type="application/xml"
        )

    reply = get_qwen_reply(call_sid, speech)

    return Response(
        build_twiml(reply),
        media_type="application/xml"
    )

# =========================================
# AUDIO (KEEP STREAM ALIVE)
# =========================================

from fastapi import WebSocket, WebSocketDisconnect
import json
import base64
import time

@app.websocket("/audio")
async def audio_stream(ws: WebSocket):
    await ws.accept()
    print("🔌 Twilio Media Stream connected")

    last_ping = time.time()

    try:
        while True:
            data = await ws.receive_text()

            # 👇 IMPORTANT: keep connection alive
            if time.time() - last_ping > 5:
                await ws.send_text(json.dumps({"event": "ping"}))
                last_ping = time.time()

            msg = json.loads(data)
            event = msg.get("event")

            if event == "start":
                print("📞 Call started")

            elif event == "media":
                # just consume audio (no processing for now)
                pass

            elif event == "stop":
                print("📴 Call ended")
                break

    except WebSocketDisconnect:
        print("❌ WebSocket disconnected")

# =========================================
# START SERVICES
# =========================================

start_ollama()

# =========================================
# DASHBOARD (LIVE CALL LOG UI)
# =========================================

from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

DASHBOARD_DIR = os.path.join(BASE_DIR, "dashboard")

app.mount("/dashboard/static", StaticFiles(directory=DASHBOARD_DIR), name="dashboard_static")

@app.get("/dashboard")
def dashboard():
    return FileResponse(os.path.join(DASHBOARD_DIR, "index.html"))

@app.get("/dashboard/data")
def dashboard_data():
    return CALL_SESSIONS