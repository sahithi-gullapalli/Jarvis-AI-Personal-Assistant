"""Local HTTP routes for the approval queue.

All routes require JARVIS_API_TOKEN. Set a long random token in the environment
before starting the API. Keep the server bound to localhost until HTTPS and
network authentication are deliberately configured.
"""
from __future__ import annotations

import hmac
import os
from typing import Any

from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel, Field

from security.approval_manager import (
    ApprovalError,
    approve_action,
    get_pending_approvals,
    reject_action,
    request_approval,
)

router = APIRouter(prefix="/approvals", tags=["approvals"])


def _verify_token(authorization: str | None) -> None:
    configured = os.getenv("JARVIS_API_TOKEN", "").strip()
    if not configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Approval API is disabled: configure JARVIS_API_TOKEN.",
        )
    expected = f"Bearer {configured}"
    if not authorization or not hmac.compare_digest(authorization, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API token.",
            headers={"WWW-Authenticate": "Bearer"},
        )


class ApprovalRequest(BaseModel):
    action_type: str = Field(min_length=1, max_length=50)
    target: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=500)
    action_data: dict[str, Any]
    ttl_seconds: int = Field(default=300, ge=1, le=900)


class ApprovalDecision(BaseModel):
    approval_id: str = Field(min_length=1, max_length=64)


@router.get("/pending")
def pending(authorization: str | None = Header(default=None)):
    _verify_token(authorization)
    return {"items": get_pending_approvals()}


@router.post("/request")
def create_request(
    payload: ApprovalRequest,
    authorization: str | None = Header(default=None),
):
    _verify_token(authorization)
    try:
        return request_approval(
            action_type=payload.action_type,
            target=payload.target,
            description=payload.description,
            action_data=payload.action_data,
            ttl_seconds=payload.ttl_seconds,
        )
    except ApprovalError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/approve")
def approve(
    payload: ApprovalDecision,
    authorization: str | None = Header(default=None),
):
    _verify_token(authorization)
    try:
        # This only marks the exact request approved and returns its payload.
        # It does not dispatch messages, emails, calls, or calendar changes.
        return approve_action(payload.approval_id)
    except ApprovalError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/reject")
def reject(
    payload: ApprovalDecision,
    authorization: str | None = Header(default=None),
):
    _verify_token(authorization)
    try:
        return reject_action(payload.approval_id)
    except ApprovalError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
