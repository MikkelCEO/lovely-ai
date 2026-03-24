import importlib
import subprocess
import sys
import os
from typing import Dict, List

# =========================================================
# AUTO INSTALL MISSING PACKAGES
# =========================================================
def ensure_package(package_name: str, import_name: str = None):
    import_name = import_name or package_name
    try:
        importlib.import_module(import_name)
    except ImportError:
        print(f"Installing missing package: {package_name}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])

ensure_package("fastapi")
ensure_package("uvicorn")
ensure_package("python-multipart", "multipart")
ensure_package("ollama")

# =========================================================
# IMPORTS
# =========================================================
from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import Response, JSONResponse
import ollama

# =========================================================
# CONFIG
# =========================================================
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
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