from fastapi import FastAPI, Request
import uvicorn

app = FastAPI()

CONFIG_PATH = "/volume1/Projects/ai-chat/Phone/config.txt"

@app.post("/update-config")
async def update_config(request: Request):
    content = await request.body()
    
    with open(CONFIG_PATH, "wb") as f:
        f.write(content)
    
    return {"status": "ok"}

@app.get("/")
def root():
    return {"status": "config server running"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5055)