# =========================================
# AUTO INSTALL DEPENDENCIES
# =========================================
import subprocess
import sys

try:
    import flask
    import twilio
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "flask", "twilio"])

# =========================================
# IMPORTS
# =========================================
from flask import Flask, jsonify
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import VoiceGrant
import os

# =========================================
# LOAD CONFIG
# =========================================
config_path = os.path.join(os.path.dirname(__file__), "config.txt")
with open(config_path, "r", encoding="utf-8") as f:
    exec(f.read())

# =========================================
# INIT APP
# =========================================
app = Flask(__name__)

# =========================================
# TOKEN ENDPOINT
# =========================================
@app.route("/token")
def token():
    identity = "pc-user"

    token = AccessToken(ACCOUNT_SID, API_KEY, API_SECRET, identity=identity)
    voice_grant = VoiceGrant(outgoing_application_sid=TWIML_APP_SID)
    token.add_grant(voice_grant)

    return jsonify(token=token.to_jwt())

# =========================================
# RUN SERVER
# =========================================
if __name__ == "__main__":
    app.run(port=5000)