"""Explicit approval queue for consequential Jarvis actions.

Approval only authorizes a request; it never executes or dispatches the action.
"""
from __future__ import annotations

import json
import os
import secrets
import time
from pathlib import Path
from threading import RLock
from typing import Any

ALLOWED_ACTION_TYPES = {"send_email", "send_whatsapp", "send_sms", "place_call", "modify_calendar"}
DEFAULT_TTL_SECONDS = 300
_audit_path = Path(os.getenv("JARVIS_APPROVAL_AUDIT_PATH", "logs/approval_audit.jsonl"))
_lock = RLock()
_pending: dict[str, dict[str, Any]] = {}


def _audit(event: str, approval_id: str, action_type: str) -> None:
    """Append minimal metadata only; never log payload, message body, or secrets."""
    try:
        _audit_path.parent.mkdir(parents=True, exist_ok=True)
        record = {"timestamp": int(time.time()), "event": event,
                  "approval_id": approval_id, "action_type": action_type}
        with _audit_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record) + "\n")
    except OSError:
        # Audit disk failures must not expose payloads or crash approval flow.
        pass


def request_approval(action_type: str, preview: str, payload: dict[str, Any],
                    ttl_seconds: int = DEFAULT_TTL_SECONDS) -> dict[str, Any]:
    action_type = action_type.strip().lower()
    if action_type not in ALLOWED_ACTION_TYPES:
        raise ValueError("Action type is not eligible for approval.")
    if not preview.strip() or len(preview) > 2000:
        raise ValueError("Preview must contain 1-2000 characters.")
    if not isinstance(payload, dict):
        raise ValueError("Payload must be a dictionary.")
    if not 1 <= ttl_seconds <= 3600:
        raise ValueError("TTL must be between 1 and 3600 seconds.")
    approval_id = secrets.token_urlsafe(24)
    record = {"approval_id": approval_id, "action_type": action_type,
              "preview": preview.strip(), "payload": payload,
              "created_at": int(time.time()), "expires_at": int(time.time()) + ttl_seconds,
              "status": "pending"}
    with _lock:
        _pending[approval_id] = record
    _audit("requested", approval_id, action_type)
    return {k: v for k, v in record.items() if k != "payload"}


def list_pending() -> list[dict[str, Any]]:
    now = int(time.time())
    with _lock:
        result = []
        for record in _pending.values():
            if record["status"] == "pending" and record["expires_at"] <= now:
                record["status"] = "expired"
                _audit("expired", record["approval_id"], record["action_type"])
            if record["status"] == "pending":
                result.append({k: v for k, v in record.items() if k != "payload"})
        return result


def approve(approval_id: str) -> dict[str, Any]:
    now = int(time.time())
    with _lock:
        record = _pending.get(approval_id)
        if record is None:
            raise KeyError("Approval request not found.")
        if record["status"] != "pending":
            raise ValueError("Approval request is not pending.")
        if record["expires_at"] <= now:
            record["status"] = "expired"
            _audit("expired", approval_id, record["action_type"])
            raise ValueError("Approval request has expired.")
        record["status"] = "approved"
        _audit("approved", approval_id, record["action_type"])
        # Returns the approved intent to the caller. Does not execute it.
        return {"approval_id": approval_id, "action_type": record["action_type"],
                "status": "approved", "payload": record["payload"]}


def reject(approval_id: str) -> dict[str, Any]:
    with _lock:
        record = _pending.get(approval_id)
        if record is None:
            raise KeyError("Approval request not found.")
        if record["status"] != "pending":
            raise ValueError("Approval request is not pending.")
        record["status"] = "rejected"
        _audit("rejected", approval_id, record["action_type"])
        return {"approval_id": approval_id, "status": "rejected"}
