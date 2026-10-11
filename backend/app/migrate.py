"""Transactional additive migrations: python -m app.migrate. No reset path."""
import hashlib
from pathlib import Path

import psycopg

from .config import ROOT_DIR, get_settings


def apply_migrations(conn, directory: Path = ROOT_DIR / "db" / "migrations") -> list[str]:
    applied = []
    with conn.transaction():
        conn.execute("SELECT pg_advisory_xact_lock(20261011)")
        conn.execute("CREATE TABLE IF NOT EXISTS schema_migration (version VARCHAR(100) PRIMARY KEY, checksum VARCHAR(64) NOT NULL, applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW())")
        for path in sorted(directory.glob("[0-9][0-9][0-9]_*.sql")):
            sql = path.read_text(encoding="utf-8")
            checksum = hashlib.sha256(sql.encode()).hexdigest()
            existing = conn.execute("SELECT checksum FROM schema_migration WHERE version=%s", (path.name,)).fetchone()
            if existing:
                if existing[0] != checksum:
                    raise RuntimeError(f"Migration changed after application: {path.name}")
                continue
            conn.execute(sql, prepare=False)
            conn.execute("INSERT INTO schema_migration(version,checksum) VALUES (%s,%s)", (path.name, checksum))
            applied.append(path.name)
    return applied


def main():
    url = get_settings().database_url.replace("postgresql+psycopg://", "postgresql://", 1)
    with psycopg.connect(url) as conn:
        applied = apply_migrations(conn)
    print("Applied migrations: " + (", ".join(applied) if applied else "already current"))


if __name__ == "__main__":
    main()
