"""Authenticated HTTP routes for the approval queue.

Approving an item does not dispatch it. A future executor must independently
validate and execute approved intents under explicit safeguards.
"""
import os
import secrets
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field

from security.approval_manager import request_approval, list_pending, approve, reject

router = APIRouter(prefix="/approvals", tags=["approvals"])


def _authenticate(authorization: str | None = Header(default=None)) -> None:
    expected = os.getenv("JARVIS_API_TOKEN", "")
    if not expected:
        raise HTTPException(status_code=503, detail="Approval API token is not configured.")
    scheme, _, token = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not token or not secrets.compare_digest(token, expected):
        raise HTTPException(status_code=401, detail="Unauthorized.")


class ApprovalRequest(BaseModel):
    action_type: str = Field(min_length=1, max_length=64)
    preview: str = Field(min_length=1, max_length=2000)
    payload: dict


class ApprovalId(BaseModel):
    approval_id: str = Field(min_length=1, max_length=128)


@router.get("/pending", dependencies=[Depends(_authenticate)])
def pending():
    return {"items": list_pending()}


@router.post("/request", dependencies=[Depends(_authenticate)])
def create_request(body: ApprovalRequest):
    try:
        return request_approval(body.action_type, body.preview, body.payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/approve", dependencies=[Depends(_authenticate)])
def approve_request(body: ApprovalId):
    try:
        return approve(body.approval_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/reject", dependencies=[Depends(_authenticate)])
def reject_request(body: ApprovalId):
    try:
        return reject(body.approval_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
