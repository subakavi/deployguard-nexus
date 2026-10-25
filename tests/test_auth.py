import os
import sys

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "app"
        )
    )
)

import app as app_module

flask_app = app_module.app

ALICE = {"sub": "sub-alice", "email": "alice@example.com"}
BOB = {"sub": "sub-bob", "email": "bob@example.com"}

RECORDS = [
    {"id": "B-2", "ownerId": "sub-bob", "riskScore": 70,
     "riskLevel": "HIGH", "decision": "BLOCKED"},
    {"id": "A-2", "ownerId": "sub-alice", "riskScore": 40,
     "riskLevel": "CAUTION", "decision": "VALIDATION_REQUIRED"},
    {"id": "A-1", "ownerId": "sub-alice", "riskScore": 10,
     "riskLevel": "SAFE", "decision": "APPROVED"},
    {"id": "OLD-1", "riskScore": 5,
     "riskLevel": "SAFE", "decision": "APPROVED"},
]


def login_client(monkeypatch, user=None):
    monkeypatch.setenv("AUTH_ENABLED", "true")
    monkeypatch.setattr(app_module, "get_deployments", lambda: list(RECORDS))
    monkeypatch.setattr(
        app_module, "get_deployment",
        lambda i: next((r for r in RECORDS if r["id"] == i), None)
    )
    client = flask_app.test_client()
    if user:
        with client.session_transaction() as session:
            session["user"] = user
    return client


def test_auth_disabled_by_default():
    client = flask_app.test_client()
    assert client.get("/api/summary").status_code == 200
    assert client.get("/auth/me").get_json()["authEnabled"] is False


def test_api_requires_login(monkeypatch):
    client = login_client(monkeypatch)
    assert client.get("/api/summary").status_code == 401
    assert client.get("/api/deployments").status_code == 401
    assert client.post("/api/analyze", json={"repository": "x"}).status_code == 401


def test_dashboard_redirects_to_login(monkeypatch):
    client = login_client(monkeypatch)
    response = client.get("/")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


def test_health_stays_public(monkeypatch):
    client = login_client(monkeypatch)
    assert client.get("/health").status_code == 200


def test_user_sees_only_own_deployments(monkeypatch):
    client = login_client(monkeypatch, ALICE)
    data = client.get("/api/deployments").get_json()
    ids = [d["id"] for d in data["deployments"]]
    assert ids == ["A-2", "A-1"]
    assert data["summary"]["riskScore"] == 40


def test_summary_is_per_user(monkeypatch):
    client = login_client(monkeypatch, BOB)
    assert client.get("/api/summary").get_json()["decision"] == "BLOCKED"


def test_new_user_has_empty_history(monkeypatch):
    client = login_client(
        monkeypatch, {"sub": "sub-new", "email": "new@example.com"}
    )
    data = client.get("/api/deployments").get_json()
    assert data["deployments"] == []
    assert data["summary"]["riskScore"] is None


def test_cannot_read_other_users_deployment(monkeypatch):
    client = login_client(monkeypatch, ALICE)
    assert client.get("/api/deployments/A-1").status_code == 200
    assert client.get("/api/deployments/B-2").status_code == 404
    assert client.get("/api/deployments/OLD-1").status_code == 404


def test_create_deployment_forces_owner(monkeypatch):
    saved = {}
    client = login_client(monkeypatch, ALICE)
    monkeypatch.setattr(
        app_module, "save_deployment",
        lambda data: saved.update(data) or data
    )
    response = client.post("/api/deployments", json={
        "id": "X", "riskScore": 1, "riskLevel": "SAFE",
        "decision": "APPROVED", "status": "SUCCESS",
        "ownerId": "sub-bob", "ownerEmail": "bob@example.com"
    })
    assert response.status_code == 201
    assert saved["ownerId"] == "sub-alice"
    assert saved["ownerEmail"] == "alice@example.com"


def test_callback_rejects_bad_state(monkeypatch):
    client = login_client(monkeypatch)
    response = client.get("/auth/callback?code=abc&state=wrong")
    assert response.status_code == 400


def test_alert_sent_only_for_risky_decisions(monkeypatch):
    sent = []
    monkeypatch.setattr(
        app_module, "send_notification",
        lambda subject, message, owner=None: sent.append((subject, owner))
    )
    with flask_app.test_request_context():
        from flask import g
        g.user = ALICE
        app_module._send_alert({"id": "1", "decision": "APPROVED"})
        app_module._send_alert({"id": "2", "decision": "BLOCKED", "riskScore": 80})
        app_module._send_alert(
            {"id": "3", "decision": "VALIDATION_REQUIRED", "riskScore": 40}
        )
    assert [owner for _, owner in sent] == ["alice@example.com"] * 2
    assert "BLOCKED" in sent[0][0]