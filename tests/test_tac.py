import pytest
from core.chunking import chunk_words
from core.tac import assert_no_future, get_tac_sql_clause, trim_at_word


def test_tac_sql_clause():
    clause = get_tac_sql_clause()
    assert "video_id" in clause
    assert "visible_from_s <=" in clause


def test_exact_word_cut_and_pause_at_10s():
    # Words spanning from 7s to 12s
    words = [
        {"word": "welcome", "start": 7.0, "end": 7.5},
        {"word": "to", "start": 8.0, "end": 8.3},
        {"word": "the", "start": 8.5, "end": 8.8},
        {"word": "lecture", "start": 9.2, "end": 9.8},
        {"word": "on", "start": 10.1, "end": 10.3},
        {"word": "algorithms", "start": 10.5, "end": 11.5},
    ]

    pause_t = 10.0  # Pause at exactly 0:10

    trimmed = trim_at_word(words, pause_t)
    trimmed_words = [w["word"] for w in trimmed]

    assert trimmed_words == ["welcome", "to", "the", "lecture"]
    assert "on" not in trimmed_words
    assert "algorithms" not in trimmed_words


def test_assert_no_future_enforcement():
    pause_t = 10.0

    # Legal context pack
    legal_pack = {
        "chunks": [
            {"id": "c1", "visible_from_s": 5.0, "text": "intro"},
            {"id": "c2", "visible_from_s": 9.9, "text": "review"},
        ],
        "recent_window": {
            "words": [
                {"word": "hello", "start": 8.0},
                {"word": "world", "start": 9.8},
            ]
        },
    }
    # Must not raise
    assert_no_future(legal_pack, pause_t)

    # Illegal context pack (chunk visible from future)
    illegal_pack = {
        "chunks": [
            {"id": "c1", "visible_from_s": 5.0, "text": "intro"},
            {"id": "c2", "visible_from_s": 10.5, "text": "future spoiler"},
        ]
    }
    with pytest.raises(AssertionError) as exc_info:
        assert_no_future(illegal_pack, pause_t)
    assert "TAC VIOLATION" in str(exc_info.value)
