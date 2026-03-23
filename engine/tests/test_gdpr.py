"""Tests for GDPR endpoints and hashing utilities."""
from __future__ import annotations

import pytest


class TestHashId:
    def test_hash_id_returns_hex_string(self, client):
        from gdpr import hash_id

        result = hash_id("telegram", "12345")
        assert isinstance(result, str)
        assert len(result) == 64  # SHA-256 hex digest

    def test_same_inputs_produce_same_hash(self, client):
        from gdpr import hash_id

        h1 = hash_id("telegram", "12345")
        h2 = hash_id("telegram", "12345")
        assert h1 == h2

    def test_different_platforms_produce_different_hashes(self, client):
        from gdpr import hash_id

        h_tg = hash_id("telegram", "12345")
        h_wa = hash_id("whatsapp", "12345")
        assert h_tg != h_wa

    def test_different_ids_produce_different_hashes(self, client):
        from gdpr import hash_id

        h1 = hash_id("telegram", "111")
        h2 = hash_id("telegram", "222")
        assert h1 != h2


class TestGDPRExport:
    def test_export_returns_empty_data_for_unknown_user(self, client):
        resp = client.post("/gdpr/export", json={"user_id": "unknown-999", "platform": "telegram"})
        assert resp.status_code == 200
        body = resp.json()
        assert "user_id_hash" in body
        assert body["moderation_events"] == []
        assert body["warning_records"] == []
        assert body["deletion_requests"] == []

    def test_export_response_contains_expected_keys(self, client):
        resp = client.post("/gdpr/export", json={"user_id": "test-user", "platform": "telegram"})
        assert resp.status_code == 200
        body = resp.json()
        assert set(body.keys()) == {
            "user_id_hash",
            "moderation_events",
            "warning_records",
            "deletion_requests",
        }

    def test_export_hash_is_deterministic(self, client):
        resp1 = client.post("/gdpr/export", json={"user_id": "u42", "platform": "telegram"})
        resp2 = client.post("/gdpr/export", json={"user_id": "u42", "platform": "telegram"})
        assert resp1.json()["user_id_hash"] == resp2.json()["user_id_hash"]


class TestGDPRDeleteRequest:
    def test_submit_delete_request_succeeds(self, client):
        resp = client.post(
            "/gdpr/delete_request",
            json={"user_id": "del-user-1", "platform": "telegram"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "pending"
        assert "request_id" in body
        assert isinstance(body["request_id"], int)
        assert "30 days" in body["message"]

    def test_duplicate_request_returns_existing(self, client):
        # First request
        r1 = client.post(
            "/gdpr/delete_request",
            json={"user_id": "del-user-dup", "platform": "telegram"},
        )
        assert r1.status_code == 200
        id1 = r1.json()["request_id"]

        # Second request for same user — should return the existing one
        r2 = client.post(
            "/gdpr/delete_request",
            json={"user_id": "del-user-dup", "platform": "telegram"},
        )
        assert r2.status_code == 200
        assert r2.json()["request_id"] == id1

    def test_get_delete_request_status(self, client):
        create = client.post(
            "/gdpr/delete_request",
            json={"user_id": "del-status-user", "platform": "telegram"},
        )
        req_id = create.json()["request_id"]

        status_resp = client.get(f"/gdpr/delete_request/{req_id}")
        assert status_resp.status_code == 200
        body = status_resp.json()
        assert body["request_id"] == req_id
        assert body["status"] == "pending"

    def test_get_nonexistent_delete_request_returns_404(self, client):
        resp = client.get("/gdpr/delete_request/999999")
        assert resp.status_code == 404

    def test_delete_request_with_notes(self, client):
        resp = client.post(
            "/gdpr/delete_request",
            json={
                "user_id": "del-notes-user",
                "platform": "telegram",
                "notes": "requested via /delete_my_data",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "pending"
