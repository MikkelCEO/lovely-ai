import subprocess
import sys
import time
import msvcrt
import os

# Auto-install Twilio
try:
    from twilio.rest import Client
except ImportError:
    print("Installing Twilio...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "twilio"])
    from twilio.rest import Client

# Load config.txt
config_path = os.path.join(os.path.dirname(__file__), "config.txt")
with open(config_path, "r", encoding="utf-8") as f:
    exec(f.read())

client = Client(ACCOUNT_SID, AUTH_TOKEN)

target = input("Enter phone number to call: ").strip()

print(f"Calling {target} now...")
call = client.calls.create(
    to=target,
    from_=TWILIO_NUMBER
)

print(f"Call started - SID: {call.sid}")
print("Press 'q' to hang up.\n")

while True:
    if msvcrt.kbhit():
        if msvcrt.getch().decode('utf-8', errors='ignore').lower() == 'q':
            client.calls(call.sid).update(status="completed")
            print("Call ended.")
            break
    time.sleep(0.2)