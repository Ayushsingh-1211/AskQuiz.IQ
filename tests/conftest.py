import os
import pytest
from fastapi.testclient import TestClient
from apps.api.app.auth import create_access_token, hash_password
from apps.api.app.config import get_settings
from apps.api.app.db.session import get_db_context, run_migrations
from apps.api.app.main import app


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    run_migrations()
    yield


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def test_user():
    email = "fixture_user@askquiz.iq"
    pwd = "fixture_password123"
    hashed = hash_password(pwd)
    with get_db_context() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (email, hashed_password, full_name, is_active)
                VALUES (%s, %s, %s, true)
                ON CONFLICT (email) DO UPDATE SET hashed_password = EXCLUDED.hashed_password
                RETURNING id, email, full_name, is_active
                """,
                (email, hashed, "Fixture Learner"),
            )
            user = cur.fetchone()
        conn.commit()
    token = create_access_token({"sub": str(user["id"]), "email": user["email"]})
    return {
        "id": str(user["id"]),
        "email": user["email"],
        "password": pwd,
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"},
    }


def test_health_endpoint(client):
    response = client.get("/api/v1/health")
    assert response.status_code in (200, 503)
    data = response.json()
    assert "status" in data
    assert "checks" in data
    assert "database" in data["checks"]
    assert "ffmpeg" in data["checks"]
    assert "tesseract" in data["checks"]


def test_auth_login_and_token(client, test_user):
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": test_user["email"], "password": test_user["password"]},
    )
    assert login_resp.status_code == 200
    login_data = login_resp.json()
    assert "access_token" in login_data
    assert login_data["token_type"] == "bearer"
    assert login_data["user"]["email"] == test_user["email"]


def test_error_envelope_structure(client):
    response = client.post("/api/v1/auth/login", json={"email": "wrong@example.com", "password": "wrong"})
    assert response.status_code == 401
    err = response.json()
    assert "code" in err
    assert "message" in err
    assert "hint" in err
    assert "request_id" in err
    assert err["code"] == "UNAUTHORIZED"
