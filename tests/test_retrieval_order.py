import pytest
from core.retrieval import hybrid_retrieve
from apps.api.app.db.session import get_pool


def test_hybrid_retrieval_tac_and_parameters():
    pool = get_pool()
    with pool.connection() as conn:
        # Retrieve chunks for python video up to pause_t=300.0
        chunks = hybrid_retrieve(
            conn=conn,
            video_id="e2c6cd67-45b8-4253-b51f-8e7752f2cefb",
            query="What is a variable?",
            pause_t=300.0,
            top_k=5,
        )
        assert len(chunks) > 0, "Expected at least one chunk retrieved"
        for c in chunks:
            assert float(c["visible_from_s"]) <= 300.0, f"TAC violation: chunk visible at {c['visible_from_s']}"
