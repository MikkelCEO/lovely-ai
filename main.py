import os
from typing import Dict, List

from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import Response, JSONResponse
import ollama
import subprocess
import time
import requests

# =========================================================
# CONFIG
# =========================================================
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

SYSTEM_PROMPT = """
You are a phone assistant.
Reply naturally, clearly, and briefly.
Keep answers short enough to sound good when spoken aloud.
If the caller asks multiple things, answer in the simplest possible way.
Do not use bullet points.
""".strip()

# =========================================================
# START / INSTALL OLLAMA
# =========================================================
def start_ollama():
    import shutil

    # 1. Check if ollama binary exists
    ollama_path = shutil.which("ollama")

    if not ollama_path:
        print("Ollama not found → installing...")

        subprocess.run(
            "apt-get update && apt-get install -y curl && curl -fsSL https://ollama.com/install.sh | sh",
            shell=True,
            check=True
        )

        ollama_path = shutil.which("ollama")

        if not ollama_path:
            raise RuntimeError("Ollama installation failed")

    print(f"Ollama binary found at: {ollama_path}")

    # 2. Check if ollama server is already running
    try:
        requests.get("http://127.0.0.1:11434", timeout=1)
        print("Ollama already running")
    except:
        print("Starting Ollama server...")

        subprocess.Popen(
            [ollama_path, "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        for _ in range(15):
            try:
                requests.get("http://127.0.0.1:11434", timeout=1)
                print("Ollama started")
                break
            except:
                time.sleep(1)
        else:
            raise RuntimeError("Ollama failed to start")

    # 3. Ensure model exists (pull if missing)
    try:
        tags = requests.get("http://127.0.0.1:11434/api/tags").json()
        models = [m["name"] for m in tags.get("models", [])]

        if OLLAMA_MODEL not in models:
            print(f"Model {OLLAMA_MODEL} not found → pulling...")
            subprocess.run([ollama_path, "pull", OLLAMA_MODEL], check=True)
        else:
            print(f"Model {OLLAMA_MODEL} already available")

    except Exception as e:
        print("Model check failed:", e)

# =========================================================
# APP
# =========================================================
app = FastAPI()

# =========================================================
# IN-MEMORY CALL SESSIONS
# =========================================================
CALL_SESSIONS: Dict[str, List[dict]] = {}

# =========================================================
# HELPERS
# =========================================================
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
<Response>
    <Say voice="alice">{say_text}</Say>
    <Hangup/>
</Response>"""

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">{say_text}</Say>
    <Gather input="speech" action="{action_url}" method="POST" speechTimeout="auto" timeout="5">
        <Say voice="alice">Please speak after the tone.</Say>
    </Gather>
    <Redirect method="POST">/twilio/respond</Redirect>
</Response>"""

def get_qwen_reply(call_sid: str, user_text: str) -> str:
    if call_sid not in CALL_SESSIONS:
        CALL_SESSIONS[call_sid] = [{"role": "system", "content": SYSTEM_PROMPT}]

    CALL_SESSIONS[call_sid].append({"role": "user", "content": user_text})

    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=CALL_SESSIONS[call_sid],
        options={
            "temperature": 0.2
        }
    )

    reply = response["message"]["content"].strip()
    CALL_SESSIONS[call_sid].append({"role": "assistant", "content": reply})
    return reply

# =========================================================
# ROUTES
# =========================================================
@app.get("/")
def root():
    return {
        "status": "ok",
        "mode": "twilio-voice-qwen",
        "model": OLLAMA_MODEL
    }

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    content = await file.read()
    with open("main.py", "wb") as f:
        f.write(content)
    return {"status": "updated"}

@app.api_route("/twilio", methods=["GET", "POST"])
async def twilio_start():
    greeting = "Hello. You are connected. How may I help you?"
    twiml = build_twiml(say_text=greeting, action_url="/twilio/respond", end_call=False)
    return Response(content=twiml, media_type="application/xml")

@app.post("/twilio/respond")
async def twilio_respond(request: Request):
    form = await request.form()

    call_sid = str(form.get("CallSid", "default_call"))
    speech_result = str(form.get("SpeechResult", "")).strip()

    print(f"CallSid: {call_sid}")
    print(f"User said: {speech_result}")

    if not speech_result:
        twiml = build_twiml(
            say_text="I did not hear anything. Please say that again.",
            action_url="/twilio/respond",
            end_call=False
        )
        return Response(content=twiml, media_type="application/xml")

    lowered = speech_result.lower()
    if lowered in {"goodbye", "bye", "hang up", "stop", "end call"}:
        twiml = build_twiml(
            say_text="Goodbye.",
            end_call=True
        )
        CALL_SESSIONS.pop(call_sid, None)
        return Response(content=twiml, media_type="application/xml")

    try:
        reply = get_qwen_reply(call_sid, speech_result)
        print(f"Agent: {reply}")

        twiml = build_twiml(
            say_text=reply,
            action_url="/twilio/respond",
            end_call=False
        )
        return Response(content=twiml, media_type="application/xml")

    except Exception as e:
        print("Error:", e)
        twiml = build_twiml(
            say_text="Sorry, something went wrong. Please try again.",
            action_url="/twilio/respond",
            end_call=False
        )
        return Response(content=twiml, media_type="application/xml")

@app.post("/twilio/hangup")
async def twilio_hangup(request: Request):
    form = await request.form()
    call_sid = str(form.get("CallSid", "default_call"))
    CALL_SESSIONS.pop(call_sid, None)
    return JSONResponse({"status": "cleared", "call_sid": call_sid})

# ========================================================
# RUN
# =========================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)