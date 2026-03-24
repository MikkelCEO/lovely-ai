import importlib
import subprocess
import sys
import traceback

# =========================================================
# AUTO INSTALL DEPENDENCIES
# =========================================================
def ensure_package(package_name, import_name=None):
    import_name = import_name or package_name
    try:
        importlib.import_module(import_name)
    except ImportError:
        print(f"Installing missing package: {package_name}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])

ensure_package("websocket-client", "websocket")
ensure_package("pyaudio")

# =========================================================
# IMPORTS (AFTER INSTALL)
# =========================================================
import websocket
import json
import base64
import pyaudio
import audioop

# =========================================================
# CONFIG
# =========================================================
WS_URL = "ws://localhost:8000/audio"
CHUNK = 160
RATE = 8000

# =========================================================
# MAIN
# =========================================================
def main():
    print("Starting mic test client...")
    print(f"Connecting to {WS_URL}")

    p = pyaudio.PyAudio()

    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK
    )

    ws = websocket.WebSocket()
    ws.connect(WS_URL)

    print("Connected. Speak into your microphone.")
    print("Press CTRL+C to stop.\n")

    ws.send(json.dumps({"event": "start"}))

    try:
        while True:
            data = stream.read(CHUNK, exception_on_overflow=False)

            mulaw = audioop.lin2ulaw(data, 2)
            payload = base64.b64encode(mulaw).decode()

            ws.send(json.dumps({
                "event": "media",
                "media": {"payload": payload}
            }))

    except KeyboardInterrupt:
        print("\nStopping...")

    finally:
        ws.send(json.dumps({"event": "stop"}))
        ws.close()

        stream.stop_stream()
        stream.close()
        p.terminate()

# =========================================================
# ENTRY POINT (DOUBLE CLICK SAFE)
# =========================================================
if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("\nERROR OCCURRED:\n")
        traceback.print_exc()

    input("\nPress ENTER to exit...")