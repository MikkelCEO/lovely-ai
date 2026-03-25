import subprocess
import sys

# Auto-install pywin32 if missing
try:
    import win32com.client
except ImportError:
    print("Installing pywin32 for speech...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pywin32"])
    import win32com.client

import requests

BASE_URL = "https://6s6a2k05nk52l4-8000.proxy.runpod.net"
CALL_SID = "test_call_123"

def speak(text):
    try:
        speaker = win32com.client.Dispatch("SAPI.SpVoice")
        speaker.Speak(text)
    except:
        pass

def send_speech(text):
    response = requests.post(
        f"{BASE_URL}/twilio/respond",
        data={"CallSid": CALL_SID, "SpeechResult": text}
    )
    if "<Say voice=\"alice\">" in response.text:
        reply = response.text.split("<Say voice=\"alice\">")[1].split("</Say>")[0]
        print(f"\nAssistant: {reply}")
        speak(reply)
    else:
        print("\nAssistant: (no reply)")

def main():
    print("=== Twilio Voice Simulator (with speech) ===\n")
    
    resp = requests.post(f"{BASE_URL}/twilio")
    if "<Say voice=\"alice\">" in resp.text:
        reply = resp.text.split("<Say voice=\"alice\">")[1].split("</Say>")[0]
        print(f"Assistant: {reply}")
        speak(reply)
    
    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() in ["exit", "quit"]:
            print("Call ended.")
            break
        if user_input:
            send_speech(user_input)

if __name__ == "__main__":
    main()