"""Optional FastAPI HTTP interface for Jarvis.

Run locally:
    python -m uvicorn api_server:app --host 127.0.0.1 --port 8000

Approval endpoints require JARVIS_API_TOKEN. Do not bind this server to a
public/LAN interface until you have configured TLS, authentication, and
appropriate network controls.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import jarvis_brain
from api.approval_routes import router as approval_router

app = FastAPI(title="Jarvis Personal Assistant API", version="0.2.0")
app.include_router(approval_router)


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
        raise HTTPException(
            status_code=500,
            detail="Jarvis could not process the request.",
        ) from exc
