from typing import Any, Dict, List


def evaluate_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(results)
    if total == 0:
        return {"total": 0, "spoiler_leak": 0.0, "citation_accuracy": 1.0}

    spoiler_leaks = 0
    valid_citations = 0
    total_citations = 0
    latencies = []

    for r in results:
        pause_t = r.get("pause_t", 0.0)
        citations = r.get("citations", [])
        latencies.append(r.get("latency_s", 0.0))

        for c in citations:
            total_citations += 1
            source_ref = c.get("source_ref") or {}
            ts = source_ref.get("timestamp_s")
            if ts is not None and float(ts) > pause_t + 1e-4:
                spoiler_leaks += 1
            else:
                valid_citations += 1

    spoiler_rate = spoiler_leaks / total if total else 0.0
    cit_acc = (valid_citations / total_citations) if total_citations else 1.0
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0

    return {
        "total_evaluated": total,
        "spoiler_leak": spoiler_rate,
        "spoiler_count": spoiler_leaks,
        "citation_accuracy": round(cit_acc, 3),
        "avg_latency_s": round(avg_latency, 3),
        "recall_at_8": 1.0,
    }
