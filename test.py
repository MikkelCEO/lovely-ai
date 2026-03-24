import websocket
import json
import base64
import pyaudio
import audioop

WS_URL = "ws://localhost:8000/audio"

CHUNK = 160  # Twilio uses 20ms = 160 samples @ 8kHz
RATE = 8000

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

print("Connected to server")

# Start event
ws.send(json.dumps({"event": "start"}))

try:
    while True:
        data = stream.read(CHUNK)

        # Convert PCM → mulaw
        mulaw = audioop.lin2ulaw(data, 2)

        payload = base64.b64encode(mulaw).decode()

        ws.send(json.dumps({
            "event": "media",
            "media": {"payload": payload}
        }))

except KeyboardInterrupt:
    print("Stopping...")

ws.send(json.dumps({"event": "stop"}))
ws.close()

stream.stop_stream()
stream.close()
p.terminate()