from core.chunking import chunk_words


def test_chunking_window_and_tac():
    # 40 seconds of words (1 word per second)
    sample_words = [{"word": f"word_{i}", "start": float(i), "end": float(i + 0.8)} for i in range(40)]

    chunks = chunk_words(sample_words, target_duration_s=15.0, overlap_s=3.0)

    assert len(chunks) >= 2

    for c in chunks:
        # Check TAC spoiler rule on every chunk
        assert c["visible_from_s"] == c["end_s"]
        assert c["start_s"] < c["end_s"]
        assert len(c["meta"]["words"]) > 0

    # First chunk covers roughly 0 to ~15s
    assert chunks[0]["start_s"] == 0.0
    assert 14.0 <= chunks[0]["end_s"] <= 16.0

    # Second chunk overlaps previous chunk (starts before first chunk ends)
    assert chunks[1]["start_s"] < chunks[0]["end_s"]
