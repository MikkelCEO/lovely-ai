# =========================================
# AUTO INSTALL PYTHON DEPENDENCIES
# =========================================
import subprocess
import sys
import os
import threading
import webbrowser
import time

def pip_install(packages):
    subprocess.check_call([sys.executable, "-m", "pip", "install"] + packages)

try:
    import flask
    import twilio
    import flask_cors
except ImportError:
    pip_install(["flask", "twilio", "flask-cors"])

# =========================================
# IMPORTS
# =========================================
from flask import Flask, jsonify
from flask_cors import CORS
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import VoiceGrant
from werkzeug.middleware.proxy_fix import ProxyFix

# =========================================
# LOAD CONFIG
# =========================================
config_path = os.path.join(os.path.dirname(__file__), "config.txt")
with open(config_path, "r", encoding="utf-8") as f:
    exec(f.read())

# =========================================
# INIT APP
# =========================================
BASE_DIR = os.path.dirname(__file__)
STATIC_DIR = os.path.join(BASE_DIR, "phone_tester", "dist")

app = Flask(__name__, static_folder=STATIC_DIR, static_url_path="")
CORS(app)

app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# =========================================
# ROUTES
# =========================================

@app.route("/token")
def token():
    identity = "pc-user"

    token = AccessToken(ACCOUNT_SID, API_KEY, API_SECRET, identity=identity)
    voice_grant = VoiceGrant(outgoing_application_sid=TWIML_APP_SID)
    token.add_grant(voice_grant)

    return jsonify(token=token.to_jwt())

# Serve frontend (SPA)
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    dist_path = os.path.join(os.path.dirname(__file__), "phone_tester", "dist")

    file_path = os.path.join(dist_path, path)

    if path != "" and os.path.exists(file_path):
        return app.send_static_file(path)

    return app.send_static_file("index.html")

# =========================================
# ENSURE NODE + INSTALL FRONTEND
# =========================================
def setup_frontend():
    frontend_path = os.path.join(os.path.dirname(__file__), "phone_tester")

    try:
        subprocess.check_output(["npm", "--version"], shell=True)
    except:
        print("❌ Node.js / npm not installed")
        return

    print("Installing frontend dependencies...")
    subprocess.call("npm install", cwd=frontend_path, shell=True)

# =========================================
# START FRONTEND (VITE)
# =========================================
def start_frontend():
    frontend_path = os.path.join(os.path.dirname(__file__), "phone_tester")
    subprocess.Popen("npm run dev -- --host 0.0.0.0", cwd=frontend_path, shell=True)

# =========================================
# OPEN BROWSER
# =========================================
def open_browser():
    time.sleep(4)
    webbrowser.open("http://localhost:5173")

# =========================================
# MAIN
# =========================================
if __name__ == "__main__":
    print("Starting Flask (API only)...")
    app.run(host="0.0.0.0", port=5050)
