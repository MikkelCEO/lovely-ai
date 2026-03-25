import subprocess
import sys
import time
import msvcrt

# Auto-install Twilio
try:
    from twilio.rest import Client
except ImportError:
    print("Installing Twilio...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "twilio"])
    from twilio.rest import Client

# === CONFIG ===
ACCOUNT_SID = "AC0c94c6664032a772dbec729dba49ecb9"   # your Account SID
AUTH_TOKEN = "070adb4a65fe8a1d879bcc862439ba1e"                 # put your real Auth Token
TWILIO_NUMBER = "+18392616244"                    # your Twilio number
YOUR_PHONE = "+4915888654546"                        # the number you want to call

client = Client(ACCOUNT_SID, AUTH_TOKEN)

print("Making call...")
call = client.calls.create(
    to=YOUR_PHONE,
    from_=TWILIO_NUMBER,
    url="https://6s6a2k05nk52l4-8000.proxy.runpod.net/twilio"
)

print(f"Call started - SID: {call.sid}")
print("Call is active. Press 'q' key to hang up instantly.\n")

while True:
    if msvcrt.kbhit():
        key = msvcrt.getch().decode('utf-8', errors='ignore').lower()
        if key == 'q':
            print("\nHanging up...")
            client.calls(call.sid).update(status="completed")
            print("Call ended.")
            break
    time.sleep(0.1)