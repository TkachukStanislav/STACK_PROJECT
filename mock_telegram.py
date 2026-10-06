import random

from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()


@app.post("/send")
async def send(payload: dict):
    if random.random() < 0.5:
        print("💥 Збій 502")
        return JSONResponse(status_code=502, content={"ok": False})
    print("📩 Отримав повідомлення:", payload)
    return {"ok": True}
