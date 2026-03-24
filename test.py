import requests
import time

BASE_URL = "http://195.26.232.177:57011"  # your RunPod HTTP endpoint
CALL_SID = "test_call_123"

def send_speech(text):
    response = requests.post(
        f"{BASE_URL}/twilio/respond",
        data={
            "CallSid": CALL_SID,
            "SpeechResult": text
        }
    )

    print("\n--- USER ---")
    print(text)

    print("\n--- TWIML RESPONSE ---")
    print(response.text)

def main():
    print("Simulated call started. Type messages like a phone call.")
    print("Type 'exit' to end.\n")

    while True:
        user_input = input("You: ")

        if user_input.lower() in ["exit", "quit"]:
            print("Call ended.")
            break

        send_speech(user_input)
        time.sleep(0.5)

if __name__ == "__main__":
    main()