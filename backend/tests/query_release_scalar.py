"""Native, read-only isolation query; Docker Desktop exec output is unreliable.

Called only by the browser preflight. Credentials stay inside this process;
only the requested scalar is returned. Disposable ownership is checked before
connecting, and the persistent connection is always read-only.
"""
import json
import os
from pathlib import Path
import subprocess
import sys

import psycopg
from psycopg.conninfo import make_conninfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def query(container, user, database, statement):
    if not statement.lstrip().upper().startswith("SELECT "):
        raise ValueError("Isolation preflight only accepts read-only SELECT queries")
    if container == "dbcas-db":
        if (user, database) != ("dbcas", "dbcas"):
            raise ValueError("Unexpected persistent identity")
        from app.config import Settings
        dsn = Settings().database_url.replace("postgresql+psycopg://", "postgresql://", 1)
    else:
        manifest = json.loads(Path(os.environ["DBCAS_TEST_MANIFEST"]).read_text())
        if container not in manifest["containers"] or (user, database) != ("postgres", "dbcas_test"):
            raise ValueError("Unexpected disposable identity")
        inspected = subprocess.run(["docker", "inspect", container], capture_output=True, text=True, check=True)
        row = json.loads(inspected.stdout)[0]
        if row["Config"].get("Labels", {}).get("dbcas.test-run") != manifest["run_id"]:
            raise ValueError("Disposable ownership mismatch")
        if not row["State"]["Running"] or row["HostConfig"].get("Tmpfs", {}).get("/var/lib/postgresql/data") is None:
            raise ValueError("Disposable PostgreSQL is not running on tmpfs")
        port = row["NetworkSettings"]["Ports"]["5432/tcp"][0]["HostPort"]
        environment = dict(item.split("=", 1) for item in row["Config"]["Env"] if "=" in item)
        if environment.get("POSTGRES_DB") != database or environment.get("POSTGRES_USER", "postgres") != user:
            raise ValueError("Disposable database credentials have unexpected identity")
        dsn = make_conninfo(host="127.0.0.1", port=port, dbname=database, user=user,
                            password=environment["POSTGRES_PASSWORD"])
    with psycopg.connect(dsn, connect_timeout=10,
                         options="-c default_transaction_read_only=on -c statement_timeout=10000") as connection:
        connection.execute("SET TRANSACTION READ ONLY")
        if connection.execute("SELECT current_database()").fetchone()[0] != database:
            raise ValueError("Connected to an unexpected database")
        result = connection.execute(statement).fetchone()
        if result is None or result[0] is None:
            raise ValueError("Isolation query returned no scalar")
        return str(result[0])


if __name__ == "__main__":
    try:
        print(json.dumps({"scalar": query(*sys.argv[1:])}))
    except Exception as exc:
        # Do not expose DSNs, passwords, query parameters or auth tokens.
        print(json.dumps({"error": type(exc).__name__}), file=sys.stderr)
        sys.exit(1)
