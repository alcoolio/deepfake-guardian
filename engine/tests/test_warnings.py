"""Tests for the warning/escalation system."""
from __future__ import annotations

import pytest


class TestEscalationAction:
    def test_first_violation_is_notice(self, client):
        from warn import escalation_action

        assert escalation_action(1) == "notice"

    def test_second_violation_is_admin_notification(self, client):
        from warn import escalation_action

        assert escalation_action(2) == "admin_notification"

    def test_third_violation_is_supervisor_escalation(self, client):
        from warn import escalation_action

        assert escalation_action(3) == "supervisor_escalation"

    def test_beyond_third_is_still_supervisor_escalation(self, client):
        from warn import escalation_action

        assert escalation_action(10) == "supervisor_escalation"


class TestRecordViolation:
    def test_first_violation_returns_notice(self, client):
        resp = client.post(
            "/warnings/record",
            json={
                "user_id": "warn-user-1",
                "group_id": "group-100",
                "platform": "telegram",
                "reasons": ["violence"],
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["warning_count"] == 1
        assert body["action"] == "notice"
        assert "user_id_hash" in body
        assert "group_id_hash" in body

    def test_second_violation_returns_admin_notification(self, client):
        user = "warn-user-seq"
        group = "group-seq"
        client.post(
            "/warnings/record",
            json={"user_id": user, "group_id": group, "platform": "telegram"},
        )
        resp = client.post(
            "/warnings/record",
            json={"user_id": user, "group_id": group, "platform": "telegram"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["warning_count"] == 2
        assert body["action"] == "admin_notification"

    def test_third_violation_returns_supervisor_escalation(self, client):
        user = "warn-user-3x"
        group = "group-3x"
        for _ in range(2):
            client.post(
                "/warnings/record",
                json={"user_id": user, "group_id": group, "platform": "telegram"},
            )
        resp = client.post(
            "/warnings/record",
            json={"user_id": user, "group_id": group, "platform": "telegram"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["warning_count"] == 3
        assert body["action"] == "supervisor_escalation"

    def test_hashes_are_deterministic(self, client):
        r1 = client.post(
            "/warnings/record",
            json={"user_id": "hash-det-user", "group_id": "hash-det-group", "platform": "telegram"},
        )
        r2 = client.post(
            "/warnings/record",
            json={"user_id": "hash-det-user", "group_id": "hash-det-group", "platform": "telegram"},
        )
        assert r1.json()["user_id_hash"] == r2.json()["user_id_hash"]

    def test_different_groups_tracked_independently(self, client):
        user = "warn-multi-group"
        resp1 = client.post(
            "/warnings/record",
            json={"user_id": user, "group_id": "group-A", "platform": "telegram"},
        )
        resp2 = client.post(
            "/warnings/record",
            json={"user_id": user, "group_id": "group-B", "platform": "telegram"},
        )
        # Each group starts at 1
        assert resp1.json()["warning_count"] == 1
        assert resp2.json()["warning_count"] == 1
        # Different group hashes
        assert resp1.json()["group_id_hash"] != resp2.json()["group_id_hash"]


class TestGetUserWarnings:
    def test_get_warnings_returns_list(self, client):
        user = "warn-get-user"
        r = client.post(
            "/warnings/record",
            json={"user_id": user, "group_id": "group-get", "platform": "telegram"},
        )
        user_hash = r.json()["user_id_hash"]

        resp = client.get(f"/warnings/{user_hash}")
        assert resp.status_code == 200
        records = resp.json()
        assert isinstance(records, list)
        assert len(records) >= 1
        assert records[0]["warning_count"] >= 1
        assert records[0]["action"] in ("notice", "admin_notification", "supervisor_escalation")

    def test_get_warnings_unknown_hash_returns_empty(self, client):
        resp = client.get("/warnings/aaaa1111bbbb2222cccc3333dddd4444eeee5555ffff6666aaaa1111bbbb2222")
        assert resp.status_code == 200
        assert resp.json() == []
