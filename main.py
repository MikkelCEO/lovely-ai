# --- AUTO INSTALL WEBSOCKETS IF MISSING ---
import importlib
import subprocess
import sys

def ensure_package(package_name, import_name=None):
    import_name = import_name or package_name
    try:
        importlib.import_module(import_name)
    except ImportError:
        print(f"Installing missing package: {package_name}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])

ensure_package("websockets")
# --- END AUTO INSTALL ---


from fastapi import FastAPI, WebSocket, UploadFile, File
import base64
import numpy as np
import audioop
from faster_whisper import WhisperModel

app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok"}

model = WhisperModel("base", compute_type="int8")
audio_buffer = bytearray()

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    content = await file.read()
    with open("main.py", "wb") as f:
        f.write(content)
    return {"status": "updated"}

@app.websocket("/audio")
async def audio_ws(websocket: WebSocket):
    await websocket.accept()
    print("Client connected")

    global audio_buffer
    audio_buffer = bytearray()

    try:
        while True:
            data = await websocket.receive_json()

            if data["event"] == "start":
                print("Stream started")

            elif data["event"] == "media":
                payload = data["media"]["payload"]
                mulaw_audio = base64.b64decode(payload)
                pcm_audio = audioop.ulaw2lin(mulaw_audio, 2)
                audio_np = np.frombuffer(pcm_audio, dtype=np.int16)
                audio_buffer.extend(audio_np.tobytes())

                if len(audio_buffer) > 32000 * 2:
                    samples = np.frombuffer(audio_buffer, dtype=np.int16).astype(np.float32) / 32768.0
                    segments, _ = model.transcribe(samples)

                    for segment in segments:
                        print("User said:", segment.text)

                    audio_buffer = bytearray()

            elif data["event"] == "stop":
                print("Stream stopped")

    except Exception as e:
        print("Client disconnected:", e)