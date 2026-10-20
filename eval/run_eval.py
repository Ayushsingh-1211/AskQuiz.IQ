import argparse
import json
import sys
import time
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from apps.api.app.db.session import get_db_context
from core.answer import generate_answer
from eval.metrics import evaluate_results


def run_eval(quick: bool = False) -> int:
    q_file = repo_root / "eval" / "questions.json"
    if not q_file.exists():
        print("questions.json not found")
        return 1

    questions = json.loads(q_file.read_text(encoding="utf-8"))
    if quick:
        questions = questions[:10]

    results = []

    with get_db_context() as conn:
        # Find or create a demo video ID for evaluation
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM videos LIMIT 1")
            v_row = cur.fetchone()
            video_id = str(v_row["id"]) if v_row else "00000000-0000-0000-0000-000000000000"

        for q in questions:
            pause_t = float(q["pause_t"])
            query = q["question"]

            t0 = time.time()
            ans = generate_answer(
                conn=conn,
                video_id=video_id,
                query=query,
                pause_t=pause_t,
            )
            lat = time.time() - t0

            results.append({
                "question_id": q["id"],
                "pause_t": pause_t,
                "citations": ans.get("citations", []),
                "latency_s": lat,
                "refusal": ans.get("refusal", False),
            })

    metrics = evaluate_results(results)

    print("=" * 60)
    print("AskQuiz.IQ Evaluation Summary")
    print(f"Total Evaluated:    {metrics['total_evaluated']}")
    print(f"Spoiler Leak:       {metrics['spoiler_leak']} (target: 0.0)")
    print(f"Citation Accuracy:  {metrics['citation_accuracy']}")
    print(f"Average Latency:    {metrics['avg_latency_s']}s")
    print("=" * 60)

    if metrics["spoiler_leak"] > 0:
        print("EVAL FAILED: Spoiler leak detected!")
        return 1

    print("EVAL PASSED: 0 spoiler leaks.")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true", help="Run quick 10-question evaluation")
    args = parser.parse_args()
    sys.exit(run_eval(quick=args.quick))
