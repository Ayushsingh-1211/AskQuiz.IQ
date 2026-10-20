import os
import sys
from pathlib import Path

# Ensure repo root is on sys.path
repo_root = Path(__file__).resolve().parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from apps.api.app.auth import hash_password
from apps.api.app.config import get_settings
from apps.api.app.db.session import get_db_context, run_migrations


def seed_users():
    run_migrations()
    settings = get_settings()

    default_users = [
        {
            "email": os.getenv("DEMO_USER_EMAIL", "demo@askquiz.iq"),
            "password": os.getenv("DEMO_USER_PASSWORD", "demo12345"),
            "full_name": "Demo Learner",
        },
        {
            "email": os.getenv("TEST_USER_EMAIL", "test@askquiz.iq"),
            "password": os.getenv("TEST_USER_PASSWORD", "test12345"),
            "full_name": "Test Candidate",
        },
        {
            "email": os.getenv("ADMIN_USER_EMAIL", "admin@askquiz.iq"),
            "password": os.getenv("ADMIN_USER_PASSWORD", "admin12345"),
            "full_name": "System Admin",
        },
    ]

    with get_db_context() as conn:
        with conn.cursor() as cur:
            for u in default_users:
                cur.execute("SELECT id FROM users WHERE email = %s", (u["email"],))
                existing = cur.fetchone()
                if existing:
                    print(f"User already exists: {u['email']} (id: {existing['id']})")
                else:
                    hashed = hash_password(u["password"])
                    cur.execute(
                        """
                        INSERT INTO users (email, hashed_password, full_name, is_active)
                        VALUES (%s, %s, %s, true)
                        RETURNING id
                        """,
                        (u["email"], hashed, u["full_name"]),
                    )
                    user_id = cur.fetchone()["id"]
                    print(f"Created user: {u['email']} (id: {user_id})")
        conn.commit()


if __name__ == "__main__":
    seed_users()
