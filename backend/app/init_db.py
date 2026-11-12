"""Initialize a fresh database or additively upgrade it; never reset data."""
import argparse

import psycopg

from .config import ROOT_DIR, get_settings
from .migrate import apply_migrations


def initialize(conn, *, seed_development: bool = False, deployment_mode: str = "production") -> list[str]:
    if seed_development and deployment_mode != "development":
        raise ValueError("Development seed is forbidden outside development")
    with conn.transaction():
        conn.execute("SELECT pg_advisory_xact_lock(20261011)")
        present = conn.execute("SELECT to_regclass('account')").fetchone()[0]
        if present is None:
            count = conn.execute("SELECT count(*) FROM pg_tables WHERE schemaname=current_schema()").fetchone()[0]
            if count:
                raise RuntimeError("Initialization refused: target schema is not empty")
            conn.execute((ROOT_DIR / "db/schema.sql").read_text(encoding="utf-8"), prepare=False)
        applied = apply_migrations(conn)
        conn.execute("INSERT INTO role(role_name) VALUES ('Learner'),('Administrator') ON CONFLICT DO NOTHING")
        if seed_development:
            conn.execute((ROOT_DIR / "db/seed.sql").read_text(encoding="utf-8"), prepare=False)
    return applied


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed-development", action="store_true")
    args = parser.parse_args()
    settings = get_settings()
    url = settings.database_url.replace("postgresql+psycopg://", "postgresql://", 1)
    with psycopg.connect(url) as conn:
        applied = initialize(conn, seed_development=args.seed_development,
                             deployment_mode=settings.deployment_mode)
    print(f"Database ready; {len(applied)} migrations applied")


if __name__ == "__main__":
    main()
