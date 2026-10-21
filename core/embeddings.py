from functools import lru_cache
from typing import List
from apps.api.app.config import get_settings

_model = None


def get_embedding_model():
    global _model
    settings = get_settings()
    if settings.EMBEDDING_BACKEND.lower() == "fts":
        raise RuntimeError("SentenceTransformer model loading is disabled when EMBEDDING_BACKEND=fts")
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(settings.EMBED_MODEL)
    return _model


def embed_passages(texts: List[str], batch_size: int = 32) -> List[List[float]]:
    if not texts:
        return []
    model = get_embedding_model()
    prefixed = [f"passage: {t.strip()}" for t in texts]
    embeddings = model.encode(prefixed, batch_size=batch_size, normalize_embeddings=True, show_progress_bar=False)
    return [e.tolist() for e in embeddings]


def embed_query(query: str) -> List[float]:
    model = get_embedding_model()
    prefixed = f"query: {query.strip()}"
    embedding = model.encode([prefixed], normalize_embeddings=True, show_progress_bar=False)[0]
    return embedding.tolist()
