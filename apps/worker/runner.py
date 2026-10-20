import argparse
import sys
import time
from pathlib import Path

# Ensure repo root is on sys.path
repo_root = Path(__file__).resolve().parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from apps.api.app.logging import get_logger, setup_logging
from apps.worker.jobs import claim_and_execute_next_job

setup_logging()
logger = get_logger("apps.worker.runner")


def run_worker_loop(poll_interval_s: float = 2.0, once: bool = False):
    logger.info("Worker started, waiting for jobs...")
    while True:
        try:
            handled = claim_and_execute_next_job()
            if once:
                if not handled:
                    logger.info("No more queued jobs to process.")
                    break
            elif not handled:
                time.sleep(poll_interval_s)
        except KeyboardInterrupt:
            logger.info("Worker stopping on interrupt.")
            break
        except Exception as exc:
            logger.exception(f"Unexpected error in worker loop: {exc}")
            time.sleep(poll_interval_s)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AskQuiz.IQ Background Worker")
    parser.add_argument("--once", action="store_true", help="Process all currently queued jobs and exit")
    args = parser.parse_args()
    run_worker_loop(once=args.once)
