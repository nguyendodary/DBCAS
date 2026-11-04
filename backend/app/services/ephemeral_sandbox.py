"""Disposable offline PostgreSQL execution through Docker exec, with no published ports."""
import json
import logging
import os
import secrets
import shutil
import subprocess
import threading
import time
import uuid
from contextlib import contextmanager

from .dataset_setup import validated_setup_statements
from .sandbox_runner import SandboxError, SandboxResult
from .sql_validator import validate_learner_sql

logger = logging.getLogger(__name__)
_SLOTS = threading.BoundedSemaphore(2)
_LABEL = "com.dbcas.ephemeral"


def docker_cli():
    executable = shutil.which("docker") or "docker"
    # A Windows batch wrapper can lose exec stdin/JSON across cmd parsing.
    return ["wsl.exe", "-e", "docker"] if os.name == "nt" and executable.lower().endswith(".cmd") else [executable]


class EphemeralSandboxRunner:
    def __init__(self, settings):
        self.settings = settings
        self.owner = uuid.uuid4().hex
        self.leases = {}
        self.deadlines = {}
        self._capacity = threading.local()

    @contextmanager
    def grading_capacity(self):
        """Admit one grading job before its database retry budget is consumed."""
        if getattr(self._capacity, "reserved", False):
            yield True
            return
        admitted = _SLOTS.acquire(blocking=False)
        if not admitted:
            yield False
            return
        self._capacity.reserved = True
        try:
            yield True
        finally:
            self._capacity.reserved = False
            _SLOTS.release()

    def _docker(self, *args, timeout=10, input=None):
        try:
            return subprocess.run([*docker_cli(), *args], input=input, capture_output=True,
                                  text=True, encoding="utf-8", timeout=timeout, check=True).stdout.strip()
        except (subprocess.SubprocessError, OSError):
            raise SandboxError("sandbox_unavailable", "The isolated SQL executor is temporarily unavailable") from None

    def is_ready(self):
        try:
            labels = json.loads(self._docker("image", "inspect", "--format", "{{json .Config.Labels}}",
                                            self.settings.sandbox_container_image))
            return (labels or {}).get("com.dbcas.sandbox-protocol") == "1"
        except (SandboxError, ValueError, TypeError):
            return False

    def _cleanup(self, name):
        try:
            labels = json.loads(self._docker("inspect", "--format", "{{json .Config.Labels}}", name))
            if (labels or {}).get(_LABEL) != self.owner:
                raise SandboxError("sandbox_cleanup_refused", "SQL executor ownership verification failed")
            self._docker("rm", "-f", name)
        except SandboxError as exc:
            # A watchdog/--rm may already have removed it. The bounded in-container
            # watchdog is also the cleanup fallback if the host process dies.
            logger.warning("Ephemeral cleanup deferred to watchdog: %s", exc.code)
        finally:
            self.deadlines.pop(name, None)
            if not getattr(self._capacity, "reserved", False):
                _SLOTS.release()

    def _create(self):
        wall = self.settings.sandbox_container_lifetime_seconds
        if not getattr(self._capacity, "reserved", False) and not _SLOTS.acquire(timeout=5):
            raise SandboxError("sandbox_busy", "SQL executor capacity is temporarily full")
        name = "dbcas-sql-" + uuid.uuid4().hex
        self.deadlines[name] = time.monotonic() + wall
        try:
            # The child watchdog inherits the executor UID and kills only PID 1
            # in its own PID namespace. --rm removes the container on exit.
            command = f"(sleep {wall}; kill -TERM 1) & exec docker-entrypoint.sh postgres -c shared_buffers=16MB -c max_connections=10 -c max_wal_size=64MB -c min_wal_size=32MB -c listen_addresses=127.0.0.1"
            self._docker("create", "--rm", "--name", name, "--label", f"{_LABEL}={self.owner}",
                         "--network", "none", "--memory", "256m", "--memory-swap", "256m", "--cpus", "1",
                         "--pids-limit", "128", "--read-only", "--user", "10001:10001",
                         "--cap-drop", "ALL", "--security-opt", "no-new-privileges:true", "--stop-timeout", "3",
                         "--tmpfs", "/var/lib/postgresql/data:rw,uid=10001,gid=10001,mode=0700,size=192m",
                         "--tmpfs", "/var/run/postgresql:rw,uid=10001,gid=10001,mode=0700,size=4m",
                         "--tmpfs", "/tmp:rw,noexec,nosuid,size=8m",
                         "-e", "POSTGRES_PASSWORD=" + secrets.token_urlsafe(32),
                         "-e", "SANDBOX_LEARNER_PASSWORD=" + secrets.token_urlsafe(32),
                         "-e", "SANDBOX_STATEMENT_TIMEOUT_MS=" + str(self.settings.sandbox_statement_timeout_ms),
                         "--entrypoint", "/bin/sh", self.settings.sandbox_container_image, "-c", command)
            self._docker("start", name)
            while time.monotonic() < self.deadlines[name] - 5:
                try:
                    self._docker("exec", name, "pg_isready", "-h", "127.0.0.1", "-U", "postgres", timeout=3)
                    return name
                except SandboxError:
                    time.sleep(0.2)
            raise SandboxError("sandbox_unavailable", "SQL executor startup deadline exceeded")
        except BaseException:
            self._cleanup(name)
            raise

    def _call(self, name, operation, sql="", schema=None):
        remaining = self.deadlines[name] - time.monotonic()
        if remaining <= 0:
            raise SandboxError("sandbox_unavailable", "SQL executor lifetime exceeded")
        keys = ("sandbox_statement_timeout_ms", "sandbox_max_rows", "sandbox_max_sql_bytes",
                "sandbox_max_result_bytes", "sandbox_max_cell_bytes", "sandbox_max_setup_bytes",
                "sandbox_connect_timeout_seconds")
        payload = {"operation": operation, "sql": sql, "schema": schema,
                   "limits": {key: getattr(self.settings, key) for key in keys}}
        output = self._docker("exec", "-i", name, "/opt/runner/bin/python", "-m", "app.sandbox_job",
                              input=json.dumps(payload, ensure_ascii=False) + "\n", timeout=min(remaining, 15))
        try:
            result = json.loads(output)
        except ValueError:
            raise SandboxError("sandbox_unavailable", "SQL executor returned an invalid response") from None
        if "error" in result:
            raise SandboxError(result["error"]["code"], result["error"]["message"])
        return result["result"]

    def provision_dataset(self, setup_sql):
        try:
            validated_setup_statements(setup_sql, self.settings.sandbox_max_setup_bytes)
        except ValueError as exc:
            raise SandboxError("dataset_setup_failed", str(exc)) from None
        name = self._create()
        try:
            schema = self._call(name, "provision", setup_sql)
            self.leases[schema] = name
            return schema
        except BaseException:
            self._cleanup(name)
            raise

    def execute(self, sql_text, *, schema=None):
        sql_text = (sql_text or "").strip()
        if len(sql_text.encode()) > self.settings.sandbox_max_sql_bytes:
            return SandboxResult(False, error_type="query_too_large", error_message="SQL exceeds the input limit")
        error = validate_learner_sql(sql_text, allowed_schemas=frozenset({schema}) if schema else frozenset())
        if error:
            return SandboxResult(False, error_type=error[0], error_message=error[1])
        name = self.leases.get(schema) if schema else self._create()
        if not name:
            raise SandboxError("sandbox_unavailable", "SQL dataset lease is no longer available")
        try:
            return SandboxResult(**self._call(name, "execute", sql_text, schema))
        finally:
            if schema is None:
                self._cleanup(name)

    def drop_dataset(self, schema):
        name = self.leases.pop(schema, None)
        if name:
            self._cleanup(name)

    def cleanup_datasets(self):
        count = len(self.leases)
        for schema in list(self.leases):
            self.drop_dataset(schema)
        return count

    def health_check(self):
        try:
            return self.execute("SELECT 1").success
        except SandboxError:
            return False

    def validate_environment(self):
        name = self._create()
        try:
            return self._call(name, "validate")
        finally:
            self._cleanup(name)
