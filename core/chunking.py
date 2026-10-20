from typing import Any, Dict, List, Optional


def chunk_words(
    words: List[Dict[str, Any]],
    target_duration_s: float = 18.0,
    overlap_s: float = 3.0,
) -> List[Dict[str, Any]]:
    """
    Groups words into 15-20s windows with a few seconds overlap.
    Sets start_s = first word start, end_s = last word end, visible_from_s = end_s.
    """
    if not words:
        return []

    chunks: List[Dict[str, Any]] = []
    n = len(words)
    start_idx = 0

    while start_idx < n:
        chunk_start_t = words[start_idx]["start"]
        target_end_t = chunk_start_t + target_duration_s

        end_idx = start_idx
        while end_idx < n and words[end_idx]["end"] <= target_end_t:
            end_idx += 1

        # If the word window is too small but more words exist, include at least 1 word
        if end_idx == start_idx:
            end_idx = min(start_idx + 1, n)

        current_words = words[start_idx:end_idx]
        chunk_text = " ".join(w["word"].strip() for w in current_words)
        start_s = current_words[0]["start"]
        end_s = current_words[-1]["end"]

        chunks.append({
            "source_type": "speech",
            "text": chunk_text,
            "start_s": start_s,
            "end_s": end_s,
            "visible_from_s": end_s,  # TAC spoiler rule: speech chunk visible only after end_s
            "meta": {
                "words": current_words,
            },
        })

        if end_idx >= n:
            break

        # Calculate next start_idx considering overlap
        overlap_target_t = end_s - overlap_s
        next_start_idx = start_idx + 1
        while next_start_idx < end_idx and words[next_start_idx]["start"] < overlap_target_t:
            next_start_idx += 1

        start_idx = next_start_idx

    return chunks
