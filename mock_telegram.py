from fastapi import FastAPI

app = FastAPI()


@app.post("/send")
async def send(payload: dict):
    print("📩 Отримав повідомлення:", payload)
    return {"ok": True}