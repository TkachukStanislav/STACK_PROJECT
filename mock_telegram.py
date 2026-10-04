import random

from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="Mock Telegram")

 
@app.post("/send")
async def send(payload: dict):
    if random.random() < 0.5:
        print("💥 Імітую збій 502")
        return JSONResponse(status_code=502, content={"ok": False})

    print("✅ Отримав:", payload)
    return {"ok": True}