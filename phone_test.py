import requests

BASE_URL = "https://6s6a2k05nk52l4-8000.proxy.runpod.net"
CALL_SID = "test_call_123"

def send_speech(text):
    response = requests.post(
        f"{BASE_URL}/twilio/respond",
        data={"CallSid": CALL_SID, "SpeechResult": text}
    )
    print("\n--- USER ---")
    print(text)
    print("\n--- TWIML RESPONSE ---")
    print(response.text)

def main():
    print("Simulated call started.\n")
    
    # Start the call
    resp = requests.post(f"{BASE_URL}/twilio")
    print("--- INITIAL GREETING ---")
    print(resp.text)
    
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ["exit", "quit"]:
            break
        if user_input:
            send_speech(user_input)

if __name__ == "__main__":
    main()