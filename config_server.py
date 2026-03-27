from fastapi import FastAPI, Request
import uvicorn
import os

app = FastAPI()

CONFIG_PATH = "/volume1/Projects/ai-chat/Phone/config.txt"

@app.get("/")
def root():
    return {"status": "config server running"}

@app.post("/update-config")
async def update_config(request: Request):
    content = (await request.body()).decode("utf-8")

    print("=== RECEIVED CONFIG ===")
    print(content)

    # Only allow these keys to be updated
    allowed_keys = {"POD_ID", "PUBLIC_IP", "LOCAL_IP", "START_TIME"}

    # Parse incoming values
    new_values = {}
    for line in content.splitlines():
        if "=" in line:
            k, v = line.strip().split("=", 1)
            if k in allowed_keys:
                new_values[k] = v

    # Read existing config
    existing = {}
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            for line in f:
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    existing[k] = v

    # Update only allowed keys
    existing.update(new_values)

    # Write back full config
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        for k, v in existing.items():
            f.write(f"{k}={v}\n")

    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5055)