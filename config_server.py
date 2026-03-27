from fastapi import FastAPI, Request
import uvicorn

app = FastAPI()

CONFIG_PATH = "/volume1/Projects/ai-chat/Phone/config.txt"

@app.get("/")
def root():
    return {"status": "config server running"}

@app.post("/update-config")
async def update_config(request: Request):
    content = await request.body()

    text = content.decode("utf-8")

    print("=== RECEIVED CONFIG ===")
    print(text)

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        f.write(text)

    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5055)
