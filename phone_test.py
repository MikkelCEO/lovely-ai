import subprocess
import sys
import time
import msvcrt
import os
from twilio.rest import Client

# Auto-install Twilio if missing
try:
    from twilio.rest import Client
except ImportError:
    print("Installing Twilio...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "twilio"])
    from twilio.rest import Client

# Load config from config.txt
config_path = os.path.join(os.path.dirname(__file__), "config.txt")
if not os.path.exists(config_path):
    print("Error: config.txt not found!")
    sys.exit(1)

with open(config_path, "r", encoding="utf-8") as f:
    exec(f.read())  # Loads ACCOUNT_SID, AUTH_TOKEN, TWILIO_NUMBER, YOUR_PHONE

client = Client(ACCOUNT_SID, AUTH_TOKEN)

print("Making call to your phone...")
call = client.calls.create(
    to=YOUR_PHONE,
    from_=TWILIO_NUMBER,
    url="https://6s6a2k05nk52l4-8000.proxy.runpod.net/twilio"
)

print(f"Call started - SID: {call.sid}")
print("Speak on your phone when it rings.")
print("Press 'q' key to hang up instantly.\n")

while True:
    if msvcrt.kbhit():
        key = msvcrt.getch().decode('utf-8', errors='ignore').lower()
        if key == 'q':
            print("\nHanging up...")
            client.calls(call.sid).update(status="completed")
            print("Call ended.")
            break
    time.sleep(0.1)