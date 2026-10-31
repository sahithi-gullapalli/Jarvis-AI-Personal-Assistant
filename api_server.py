"""Optional FastAPI HTTP interface for Jarvis. Run with:
python -m uvicorn api_server:app --host 127.0.0.1 --port 8000
Keep it bound to localhost unless you deliberately configure authentication.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import jarvis_brain

app = FastAPI(title="Jarvis Personal Assistant API", version="0.1.0")

class AskRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)

class AskResponse(BaseModel):
    answer: str

@app.get("/health")
def health():
    return {"status": "ok", "service": "jarvis"}

@app.post("/ask", response_model=AskResponse)
def ask(payload: AskRequest):
    try:
        answer = jarvis_brain.think(payload.query.strip())
        return AskResponse(answer=answer)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Jarvis could not process the request.") from exc
