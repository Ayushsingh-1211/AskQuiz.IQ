import sys
from pathlib import Path

# Ensure repo root is on sys.path
repo_root = Path(__file__).resolve().parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from apps.api.app.routes.health import run_all_self_checks


def main() -> int:
    print("=" * 60)
    print("AskQuiz.IQ Preflight Self-Check")
    print("=" * 60)

    results = run_all_self_checks()
    checks = results["checks"]
    failed = False

    for name, res in checks.items():
        ok = res.get("ok", False)
        status_tag = "[OK]  " if ok else "[FAIL]"
        details = []
        for k, v in res.items():
            if k != "ok":
                details.append(f"{k}={v}")
        detail_str = f" ({', '.join(details)})" if details else ""
        print(f"{status_tag} {name:<12}{detail_str}")
        if not ok:
            failed = True

    print("=" * 60)
    if failed:
        print("Preflight check FAILED: One or more dependencies are missing or unhealthy.")
        return 1
    else:
        print("Preflight check PASSED: All foundational services and dependencies ready.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
