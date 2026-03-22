"""Integration tests for the FastAPI route handlers."""

from __future__ import annotations

import pytest


class TestHealth:
    def test_health_returns_ok(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

    def test_health_no_auth_required(self, client_with_key):
        # /health must be accessible even without an API key
        resp = client_with_key.get("/health")
        assert resp.status_code == 200


class TestModerateText:
    def test_safe_text_returns_allow(self, client):
        resp = client.post("/moderate_text", json={"text": "hello world"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["verdict"] == "allow"
        assert "scores" in body
        assert set(body["scores"].keys()) == {"violence", "sexual_violence", "nsfw", "deepfake_suspect"}

    def test_empty_text_rejected(self, client):
        resp = client.post("/moderate_text", json={"text": ""})
        assert resp.status_code == 422  # Pydantic min_length=1

    def test_missing_text_field_rejected(self, client):
        resp = client.post("/moderate_text", json={})
        assert resp.status_code == 422

    def test_response_schema(self, client):
        resp = client.post("/moderate_text", json={"text": "test"})
        body = resp.json()
        assert "verdict" in body
        assert "reasons" in body
        assert "scores" in body
        assert body["verdict"] in ("allow", "flag", "delete")
        assert isinstance(body["reasons"], list)


class TestModerateImage:
    def test_valid_base64_image(self, client, small_image_b64):
        resp = client.post("/moderate_image", json={"image_base64": small_image_b64})
        assert resp.status_code == 200
        body = resp.json()
        assert body["verdict"] in ("allow", "flag", "delete")

    def test_missing_image_fields_rejected(self, client):
        resp = client.post("/moderate_image", json={})
        assert resp.status_code == 400
        assert "image_base64" in resp.json()["detail"] or "image_url" in resp.json()["detail"]

    def test_response_has_deepfake_score(self, client, small_image_b64):
        resp = client.post("/moderate_image", json={"image_base64": small_image_b64})
        assert resp.status_code == 200
        # Deepfake stub always returns 0.05
        assert resp.json()["scores"]["deepfake_suspect"] == pytest.approx(0.05)


class TestModerateVideo:
    def test_stub_returns_allow(self, client):
        resp = client.post("/moderate_video", json={"video_base64": "dGVzdA=="})
        assert resp.status_code == 200
        body = resp.json()
        # Video is still a stub — always allow
        assert body["verdict"] == "allow"
        assert body["scores"]["violence"] == 0.0

    def test_missing_video_fields_rejected(self, client):
        resp = client.post("/moderate_video", json={})
        assert resp.status_code == 400


class TestApiKeyAuth:
    def test_request_without_key_rejected(self, client_with_key):
        resp = client_with_key.post("/moderate_text", json={"text": "hello"})
        assert resp.status_code == 401

    def test_request_with_wrong_key_rejected(self, client_with_key):
        resp = client_with_key.post(
            "/moderate_text",
            json={"text": "hello"},
            headers={"X-API-Key": "wrong-key"},
        )
        assert resp.status_code == 401

    def test_request_with_correct_key_succeeds(self, client_with_key):
        resp = client_with_key.post(
            "/moderate_text",
            json={"text": "hello"},
            headers={"X-API-Key": "test-secret-key"},
        )
        assert resp.status_code == 200

    def test_health_bypasses_auth(self, client_with_key):
        resp = client_with_key.get("/health")
        assert resp.status_code == 200
