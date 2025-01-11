from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def connect():
    return {"status": "Successful"}

