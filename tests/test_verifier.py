from core.verifier import format_timestamp, verify_and_build_citations


def test_format_timestamp():
    assert format_timestamp(0.0) == "00:00"
    assert format_timestamp(65.0) == "01:05"
    assert format_timestamp(125.4) == "02:05"


def test_verify_valid_citation():
    id_map = {
        "c1": {
            "id": "11111111-1111-1111-1111-111111111111",
            "source_type": "speech",
            "start_s": 10.0,
            "end_s": 25.0,
            "visible_from_s": 25.0,
            "text": "Machine learning explanation",
        }
    }
    raw = [{"chunk_id": "c1"}]
    pause_t = 30.0

    verified, valid = verify_and_build_citations(raw, id_map, pause_t)
    assert valid is True
    assert len(verified) == 1
    assert verified[0]["source_ref"]["label"] == "Video 00:10-00:25"
    assert verified[0]["chunk_id"] == "11111111-1111-1111-1111-111111111111"


def test_verify_invalid_or_future_citation():
    id_map = {
        "c1": {
            "id": "11111111-1111-1111-1111-111111111111",
            "source_type": "speech",
            "start_s": 40.0,
            "end_s": 55.0,
            "visible_from_s": 55.0,
            "text": "Future content",
        }
    }
    # Pause is at 30s, but chunk is visible from 55s -> Spoiler!
    raw = [{"chunk_id": "c1"}, {"chunk_id": "c999_missing"}]
    pause_t = 30.0

    verified, valid = verify_and_build_citations(raw, id_map, pause_t)
    assert valid is False
    assert len(verified) == 0  # Rejects both future chunk and missing chunk
