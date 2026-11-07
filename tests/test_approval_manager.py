"""Unit tests for the explicit approval gate (pytest)."""
import time

import pytest

from security import approval_manager as approvals


@pytest.fixture(autouse=True)
def isolated_audit_log(tmp_path, monkeypatch):
    monkeypatch.setattr(approvals, "_audit_path", tmp_path / "audit.jsonl")
    with approvals._lock:
        approvals._pending.clear()


def sample_request():
    return approvals.request_approval(
        action_type="send_email",
        target="recipient@example.com",
        description="Send a test email",
        action_data={"subject": "Test", "body": "Hello", "preview": "Hello"},
    )


def test_request_is_pending_and_preview_is_safe():
    result = sample_request()
    assert result["status"] == "pending"
    assert result["action_type"] == "send_email"
    assert result["preview"] == "Hello"
    assert len(approvals.get_pending_approvals()) == 1


def test_approve_returns_payload_but_does_not_execute():
    result = sample_request()
    approved = approvals.approve_action(result["approval_id"])
    assert approved["status"] == "approved"
    assert approved["action_data"]["body"] == "Hello"
    assert approvals.get_pending_approvals() == []


def test_reject_pending_action():
    result = sample_request()
    rejected = approvals.reject_action(result["approval_id"])
    assert rejected["status"] == "rejected"
    with pytest.raises(approvals.ApprovalError):
        approvals.approve_action(result["approval_id"])


def test_expired_request_cannot_be_approved():
    result = approvals.request_approval(
        action_type="place_call",
        target="contact",
        description="Call contact",
        action_data={"preview": "Call contact"},
        ttl_seconds=1,
    )
    with approvals._lock:
        approvals._pending[result["approval_id"]]["expires_at"] = int(time.time()) - 1
    with pytest.raises(approvals.ApprovalError, match="expired"):
        approvals.approve_action(result["approval_id"])


@pytest.mark.parametrize("action_type", ["shell_command", "delete_files", "unknown"])
def test_disallowed_action_type_is_rejected(action_type):
    with pytest.raises(approvals.ApprovalError):
        approvals.request_approval(
            action_type=action_type,
            target="target",
            description="description",
            action_data={},
        )


def test_invalid_ttl_is_rejected():
    with pytest.raises(approvals.ApprovalError):
        approvals.request_approval(
            action_type="send_sms",
            target="phone",
            description="Send SMS",
            action_data={},
            ttl_seconds=999999,
        )
