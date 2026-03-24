# =========================================================
# AUTO INSTALL REQUIRED PACKAGES (INCLUDING WEBSOCKETS)
# =========================================================
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

# REQUIRED FOR WEBSOCKET SUPPORT IN UVICORN
ensure_package("websockets")
ensure_package("uvicorn[standard]")

# =========================================================
# YOUR NORMAL IMPORTS BELOW
# =========================================================

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
ensure_package("sounddevice")
ensure_package("numpy")

# =========================================================
# IMPORTS
# =========================================================
import websocket
import json
import base64
import numpy as np
import sounddevice as sd

# =========================================================
# CONFIG
# =========================================================
WS_URL = "ws://195.26.232.177:57011/audio"
RATE = 8000
CHUNK = 160

# =========================================================
# PCM → MULAW (replacement for audioop)
# =========================================================
def pcm_to_mulaw(signal, mu=255):
    signal = signal.astype(np.float32) / 32768.0
    magnitude = np.log1p(mu * np.abs(signal)) / np.log1p(mu)
    signal = np.sign(signal) * magnitude
    return ((signal + 1) / 2 * mu).astype(np.uint8)

# =========================================================
# MAIN
# =========================================================
def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    print("Starting mic test client...")
    print(f"Connecting to {WS_URL}")

    ws = websocket.WebSocket()
    ws.connect(WS_URL)

    print("Connected. Speak into your microphone.")
    print("Press CTRL+C to stop.\n")

    ws.send(json.dumps({"event": "start"}))

    try:
        def callback(indata, frames, time, status):
            audio = indata[:, 0]  # mono
            pcm = (audio * 32768).astype(np.int16)

            mulaw = pcm_to_mulaw(pcm)
            payload = base64.b64encode(mulaw.tobytes()).decode()

            ws.send(json.dumps({
                "event": "media",
                "media": {"payload": payload}
            }))

        with sd.InputStream(samplerate=RATE, channels=1, callback=callback, blocksize=CHUNK):
            while True:
                pass

    except KeyboardInterrupt:
        print("\nStopping...")

    finally:
        ws.send(json.dumps({"event": "stop"}))
        ws.close()

# =========================================================
# ENTRY POINT
# =========================================================
if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("\nERROR OCCURRED:\n")
        traceback.print_exc()

    input("\nPress ENTER to exit...")