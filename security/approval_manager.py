"""Explicit, time-limited approval gate for consequential Jarvis actions.

This module only records/retrieves approval decisions. It does NOT send messages,
emails, or place calls. A trusted integration must verify the returned approved
action and execute it separately. Keep API routes authenticated before exposing
these functions beyond localhost.
"""
from __future__ import annotations

import json
import os
import threading
import time
import uuid
from pathlib import Path
from typing import Any

ALLOWED_ACTIONS = frozenset({
    "send_email",
    "send_whatsapp",
    "send_sms",
    "place_call",
    "modify_calendar",
})
DEFAULT_TTL_SECONDS = 300
MAX_TTL_SECONDS = 900
MAX_DESCRIPTION_LENGTH = 500
MAX_PREVIEW_LENGTH = 300

_lock = threading.RLock()
_pending: dict[str, dict[str, Any]] = {}
_audit_path = Path(os.getenv(
    "JARVIS_APPROVAL_AUDIT_PATH",
    str(Path(__file__).parent / "data" / "approval_audit.jsonl"),
))


class ApprovalError(ValueError):
    """Raised when an approval request is invalid or cannot be resolved."""


def _audit(event: str, approval_id: str, action_type: str, target: str) -> None:
    """Append metadata-only audit entry; do not persist action body/content."""
    try:
        _audit_path.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "timestamp": int(time.time()),
            "event": event,
            "approval_id": approval_id,
            "action_type": action_type,
            "target": target[:200],
        }
        with _audit_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(entry, ensure_ascii=True) + "\n")
    except OSError as exc:
        # Fail closed for approval decisions if audit cannot be persisted.
        raise ApprovalError("Approval audit log is unavailable.") from exc


def request_approval(
    action_type: str,
    target: str,
    description: str,
    action_data: dict[str, Any],
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
) -> dict[str, Any]:
    """Create a pending approval for one exact action and return a safe preview."""
    if action_type not in ALLOWED_ACTIONS:
        raise ApprovalError("This action type is not allowed through the approval gate.")
    if not isinstance(target, str) or not target.strip():
        raise ApprovalError("A non-empty action target is required.")
    if not isinstance(description, str) or not description.strip():
        raise ApprovalError("A non-empty action description is required.")
    if not isinstance(action_data, dict):
        raise ApprovalError("Action data must be a dictionary.")
    if not isinstance(ttl_seconds, int) or not 1 <= ttl_seconds <= MAX_TTL_SECONDS:
        raise ApprovalError(f"Approval lifetime must be between 1 and {MAX_TTL_SECONDS} seconds.")

    approval_id = uuid.uuid4().hex
    expires_at = int(time.time()) + ttl_seconds
    item = {
        "approval_id": approval_id,
        "action_type": action_type,
        "target": target.strip(),
        "description": description.strip()[:MAX_DESCRIPTION_LENGTH],
        "action_data": action_data.copy(),
        "status": "pending",
        "expires_at": expires_at,
    }
    with _lock:
        _audit("requested", approval_id, action_type, target)
        _pending[approval_id] = item

    preview = action_data.get("preview", "")
    if not isinstance(preview, str):
        preview = ""
    return {
        "approval_id": approval_id,
        "status": "pending",
        "action_type": action_type,
        "target": item["target"],
        "description": item["description"],
        "preview": preview[:MAX_PREVIEW_LENGTH],
        "expires_at": expires_at,
    }


def approve_action(approval_id: str) -> dict[str, Any]:
    """Approve exactly one pending, unexpired action; return data for executor."""
    with _lock:
        item = _pending.get(approval_id)
        if item is None:
            raise ApprovalError("Approval request not found.")
        if item["status"] != "pending":
            raise ApprovalError("This approval request is no longer pending.")
        if int(time.time()) >= item["expires_at"]:
            item["status"] = "expired"
            _audit("expired", approval_id, item["action_type"], item["target"])
            raise ApprovalError("Approval request has expired.")

        _audit("approved", approval_id, item["action_type"], item["target"])
        item["status"] = "approved"
        # Return an isolated copy; execution is deliberately not performed here.
        return {
            "approval_id": approval_id,
            "status": "approved",
            "action_type": item["action_type"],
            "target": item["target"],
            "description": item["description"],
            "action_data": item["action_data"].copy(),
        }


def reject_action(approval_id: str) -> dict[str, str]:
    """Reject exactly one pending action."""
    with _lock:
        item = _pending.get(approval_id)
        if item is None:
            raise ApprovalError("Approval request not found.")
        if item["status"] != "pending":
            raise ApprovalError("This approval request is no longer pending.")
        item["status"] = "rejected"
        _audit("rejected", approval_id, item["action_type"], item["target"])
        return {"approval_id": approval_id, "status": "rejected"}


def get_pending_approvals() -> list[dict[str, Any]]:
    """Return safe previews of current, unexpired requests for approval UI."""
    now = int(time.time())
    with _lock:
        results = []
        for item in _pending.values():
            if item["status"] == "pending" and now >= item["expires_at"]:
                item["status"] = "expired"
                _audit("expired", item["approval_id"], item["action_type"], item["target"])
            if item["status"] == "pending":
                preview = item["action_data"].get("preview", "")
                if not isinstance(preview, str):
                    preview = ""
                results.append({
                    "approval_id": item["approval_id"],
                    "action_type": item["action_type"],
                    "target": item["target"],
                    "description": item["description"],
                    "preview": preview[:MAX_PREVIEW_LENGTH],
                    "expires_at": item["expires_at"],
                    "status": "pending",
                })
        return results
