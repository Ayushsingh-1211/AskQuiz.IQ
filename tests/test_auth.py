import pytest
from fastapi.testclient import TestClient
from apps.api.app.main import app

client = TestClient(app)


def test_auth_valid_demo12345():
    """1. Valid demo credentials (demo12345) authenticate successfully and match expected schema."""
    resp = client.post("/api/v1/auth/login", json={"email": "demo@askquiz.iq", "password": "demo12345"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"].lower() == "bearer"
    assert "user" in data
    assert data["user"]["email"] == "demo@askquiz.iq"
    assert "id" in data["user"]
    assert data["user"]["is_active"] is True


def test_auth_valid_demo_alias():
    """Valid short alias (demo) also authenticates successfully."""
    resp = client.post("/api/v1/auth/login", json={"email": "demo@askquiz.iq", "password": "demo"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["user"]["email"] == "demo@askquiz.iq"


def test_auth_invalid_password_rejected():
    """2. Incorrect password is rejected with 401."""
    resp = client.post("/api/v1/auth/login", json={"email": "demo@askquiz.iq", "password": "wrongpassword999"})
    assert resp.status_code == 401
    data = resp.json()
    assert data["code"] == "UNAUTHORIZED"
    assert "Invalid email or password" in data["message"]


def test_auth_nonexistent_account_rejected():
    """3. Nonexistent account is rejected with identical generic 401 message."""
    resp = client.post("/api/v1/auth/login", json={"email": "nonexistent_user@askquiz.iq", "password": "demo12345"})
    assert resp.status_code == 401
    data = resp.json()
    assert data["code"] == "UNAUTHORIZED"
    assert "Invalid email or password" in data["message"]
