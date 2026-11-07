import time
import pytest

from security.approval_manager import request_approval, list_pending, approve, reject


def test_request_returns_preview_without_payload():
    item = request_approval("send_email", "Email to test@example.com", {"body": "secret"})
    assert item["status"] == "pending"
    assert "payload" not in item
    assert item in list_pending()


def test_approve_returns_intent_without_execution():
    payload = {"body": "hello"}
    item = request_approval("send_whatsapp", "WhatsApp to contact", payload)
    result = approve(item["approval_id"])
    assert result["status"] == "approved"
    assert result["payload"] == payload


def test_reject():
    item = request_approval("place_call", "Call contact", {"phone": "000"})
    assert reject(item["approval_id"])["status"] == "rejected"


def test_expiration():
    item = request_approval("send_sms", "SMS preview", {"text": "x"}, ttl_seconds=1)
    time.sleep(1.1)
    with pytest.raises(ValueError, match="expired"):
        approve(item["approval_id"])


def test_disallowed_action():
    with pytest.raises(ValueError):
        request_approval("delete_files", "Delete", {})


def test_ttl_bounds():
    with pytest.raises(ValueError):
        request_approval("send_email", "Preview", {}, ttl_seconds=0)
