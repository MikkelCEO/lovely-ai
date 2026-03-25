import requests

BASE_URL = "https://6s6a2k05nk52l4-8000.proxy.runpod.net"
CALL_SID = "test_call_123"

def send_speech(text):
    response = requests.post(
        f"{BASE_URL}/twilio/respond",
        data={"CallSid": CALL_SID, "SpeechResult": text}
    )
    print(f"\nYou: {text}")
    print("Assistant:", response.text.split("<Say voice=\"alice\">")[1].split("</Say>")[0] if "<Say" in response.text else "No reply")

def main():
    print("=== Twilio Voice Simulator ===\n")
    
    # Start call
    resp = requests.post(f"{BASE_URL}/twilio")
    print("Assistant:", resp.text.split("<Say voice=\"alice\">")[1].split("</Say>")[0])
    
    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() in ["exit", "quit"]:
            print("Call ended.")
            break
        if user_input:
            send_speech(user_input)

if __name__ == "__main__":
    main()