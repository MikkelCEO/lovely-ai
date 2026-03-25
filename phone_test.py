import subprocess
import sys

# Auto-install Twilio if missing
try:
    from twilio.rest import Client
except ImportError:
    print("Installing Twilio package...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "twilio"])
    from twilio.rest import Client

# === CONFIG ===
ACCOUNT_SID = "AC0c94c6664032a772dbec729dba49ecb9"   # your Account SID
AUTH_TOKEN = "070adb4a65fe8a1d879bcc862439ba1e"                 # put your real Auth Token
TWILIO_NUMBER = "+4915888654546"                    # your Twilio number
YOUR_PHONE = "+18392616244"                        # the number you want to call

client = Client(ACCOUNT_SID, AUTH_TOKEN)

call = client.calls.create(
    to=YOUR_PHONE,
    from_=TWILIO_NUMBER,
    url="https://6s6a2k05nk52l4-8000.proxy.runpod.net/twilio"
)

print("✅ Calling your phone now...")
print("Call SID:", call.sid)