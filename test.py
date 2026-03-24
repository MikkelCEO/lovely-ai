import httpx

url = "https://hvexdt8r2nww7h-8000.proxy.runpod.net/v1/chat/completions"

r = httpx.post(
    url,
    headers={"Content-Type": "application/json"},
    json={
        "model": "NousResearch/Nous-Hermes-2-Mistral-7B-DPO",
        "messages": [
            {"role": "user", "content": "Say hello in 5 words"}
        ],
        "max_tokens": 20
    },
    timeout=30
)

print(r.status_code)
print(r.text)