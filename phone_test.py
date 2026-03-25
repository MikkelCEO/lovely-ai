import requests
import subprocess
import sys

# Auto-install gTTS + playsound for realistic voice (closest simple match to Twilio)
try:
    from gtts import gTTS
    import playsound
except ImportError:
    print("Installing gTTS and playsound for realistic voice...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "gTTS", "playsound==1.2.2"])
    from gtts import gTTS
    import playsound

BASE_URL = "https://6s6a2k05nk52l4-8000.proxy.runpod.net"
CALL_SID = "test_call_123"

def speak(reply):
    try:
        tts = gTTS(text=reply, lang='en', slow=False)
        tts.save("reply.mp3")
        playsound.playsound("reply.mp3")
    except:
        pass  # fallback if audio fails

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
    print("=== Exact Twilio Call Simulator with Voice ===\n")
    
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