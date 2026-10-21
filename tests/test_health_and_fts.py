import unittest.mock as mock
import pytest
from fastapi.testclient import TestClient
from apps.api.app.config import get_settings
from apps.api.app.main import app
import core.embeddings as core_embeddings
from core.retrieval import hybrid_retrieve


@pytest.fixture(autouse=True)
def mock_startup_db_actions(monkeypatch):
    """Mocks startup migrations & seeding so tests execute instantaneously without DB socket timeout."""
    monkeypatch.setenv("AUTO_SEED_DEMO", "false")
    monkeypatch.setenv("EMBEDDED_WORKER", "false")
    get_settings.cache_clear()
    monkeypatch.setattr("apps.api.app.main.run_migrations", lambda: None)
    monkeypatch.setattr("infra.scripts.seed_users.seed_users", lambda: None)
    yield
    get_settings.cache_clear()


@pytest.fixture
def client():
    """Provides a TestClient with mocked DB actions for instantaneous test execution."""
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


def test_root_and_health_endpoints_fast_status(client):
    """Root and /health endpoints return 200 OK immediately for port detection."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}

    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_api_v1_health_does_not_instantiate_sentence_transformer(client, monkeypatch):
    """The /api/v1/health endpoint must never load SentenceTransformer or heavy ML models."""
    # Ensure embedding model is not loaded
    core_embeddings._model = None

    # Mock DB health check to simulate healthy DB
    monkeypatch.setattr("apps.api.app.routes.health.check_db_health", lambda: True)

    # Patch SentenceTransformer constructor to fail if called
    with mock.patch("sentence_transformers.SentenceTransformer", side_effect=AssertionError("SentenceTransformer must NOT be instantiated!")):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["database"] is True

    # Assert model was never loaded into memory
    assert core_embeddings._model is None


def test_fts_mode_guard_raises_runtime_error(monkeypatch):
    """Calling get_embedding_model() when EMBEDDING_BACKEND=fts raises RuntimeError instead of consuming RAM."""
    monkeypatch.setenv("EMBEDDING_BACKEND", "fts")
    get_settings.cache_clear()
    core_embeddings._model = None

    with pytest.raises(RuntimeError) as exc_info:
        core_embeddings.get_embedding_model()
    assert "disabled when EMBEDDING_BACKEND=fts" in str(exc_info.value)

    get_settings.cache_clear()


def test_fts_retrieval_respects_tac_and_skips_embedding(monkeypatch):
    """hybrid_retrieve in FTS mode queries PostgreSQL FTS under TAC and never loads embedding models."""
    monkeypatch.setenv("EMBEDDING_BACKEND", "fts")
    get_settings.cache_clear()
    core_embeddings._model = None

    executed_queries = []

    # Mock psycopg connection & cursor
    mock_cursor = mock.MagicMock()
    mock_cursor.__enter__.return_value = mock_cursor

    sample_chunks = [
        {
            "id": "11111111-1111-1111-1111-111111111111",
            "video_id": "vid-123",
            "source_type": "speech",
            "text": "Machine learning is a subset of artificial intelligence.",
            "start_s": 10.0,
            "end_s": 25.0,
            "visible_from_s": 15.0,
            "page": None,
            "slide": None,
            "meta": {},
            "fts_score": 0.85,
        },
        {
            "id": "22222222-2222-2222-2222-222222222222",
            "video_id": "vid-123",
            "source_type": "screen",
            "text": "Supervised learning overview diagram.",
            "start_s": 30.0,
            "end_s": 45.0,
            "visible_from_s": 35.0,
            "page": 1,
            "slide": 1,
            "meta": {},
            "fts_score": 0.72,
        },
    ]

    def mock_execute(sql, params=None):
        executed_queries.append((sql, params))

    mock_cursor.execute.side_effect = mock_execute
    mock_cursor.fetchall.return_value = sample_chunks

    mock_conn = mock.MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    # Assert SentenceTransformer is never called
    with mock.patch("sentence_transformers.SentenceTransformer", side_effect=AssertionError("SentenceTransformer must NOT be instantiated!")):
        with mock.patch("core.embeddings.embed_query", side_effect=AssertionError("embed_query must NOT be called in FTS mode!")):
            results = hybrid_retrieve(
                conn=mock_conn,
                video_id="vid-123",
                query="What is machine learning?",
                pause_t=50.0,
                top_k=5,
            )

    # Verify results retrieved and ordered
    assert len(results) > 0
    assert results[0]["id"] == "11111111-1111-1111-1111-111111111111"

    # Verify TAC enforcement in all executed SQL queries
    for sql, params in executed_queries:
        assert "video_id = %s AND visible_from_s <= %s" in sql, f"TAC violation in query: {sql}"
        assert params[1] == "vid-123"
        assert params[2] == 50.0

    # Ensure model is still None
    assert core_embeddings._model is None
    get_settings.cache_clear()
