"""B2 constrained runtime inside the broker (never inside the API request path).

Only the broker process calls the Docker CLI. The API keeps its existing
socket/CLI mounts until the later cutover PR; this module does not add any new
socket or image to the API or to student-SQL containers.
"""
import json
import subprocess
import threading
import time
import uuid

from .errors import BrokerError
from .service import _REQUIRED_TEMPLATE, logger


class ConstrainedRuntime:
    def __init__(self, settings, docker=None):
        self.settings = settings
        self._docker = docker or self._cli
        self._lock = threading.Lock()
        self._leases = {}

    @staticmethod
    def _cli(args, *, input=None, timeout=15):
        completed = subprocess.run(args, input=input, capture_output=True, text=True,
                                   encoding="utf-8", timeout=timeout, check=True)
        return completed.stdout.strip()

    def _allowed_image(self):
        images = self.settings.sandbox_broker_allowed_images
        digest = self.settings.sandbox_broker_image_digest
        if not images or digest not in images.values():
            raise BrokerError("broker_image_not_allowed", "Executor image digest is not allow-listed")
        return next(name for name, value in images.items() if value == digest)

    def _create_args(self, name):
        template = self.settings.sandbox_broker_template
        if template != _REQUIRED_TEMPLATE:
            raise BrokerError("broker_template_not_allowed", "Executor template is not allow-listed")
        wall = self.settings.sandbox_container_lifetime_seconds
        command = f"(sleep {wall}; kill -TERM 1) & exec docker-entrypoint.sh postgres"
        return [
            "docker", "create", "--rm", "--name", name,
            "--label", "com.dbcas.broker=1",
            "--network", template["network"], "--read-only",
            "--user", f"{template['uid']}:{template['gid']}",
            "--cap-drop", "ALL", "--security-opt", "no-new-privileges:true",
            "--pids-limit", str(template["pids_limit"]),
            "--memory", f"{template['memory_mb']}m",
            "--cpus", str(template["cpus"]),
            "--tmpfs", "/var/lib/postgresql/data:rw,uid=10001,gid=10001,mode=0700,size=192m",
            "--tmpfs", "/var/run/postgresql:rw,uid=10001,gid=10001,mode=0700,size=4m",
            "--tmpfs", "/tmp:rw,noexec,nosuid,size=8m",
            "--entrypoint", "/bin/sh", self._allowed_image(), "-c", command,
        ]

    def _call(self, name, operation, sql, schema):
        limits = {key: getattr(self.settings, key) for key in (
            "sandbox_statement_timeout_ms", "sandbox_max_rows", "sandbox_max_sql_bytes",
            "sandbox_max_result_bytes", "sandbox_max_cell_bytes", "sandbox_max_setup_bytes",
            "sandbox_connect_timeout_seconds")}
        payload = {"operation": operation, "sql": sql, "schema": schema, "limits": limits}
        output = self._docker(["docker", "exec", "-i", name, "/opt/runner/bin/python",
                               "-m", "app.sandbox_job"],
                              input=json.dumps(payload, ensure_ascii=False) + "\n")
        try:
            result = json.loads(output)
        except ValueError as exc:
            raise BrokerError("broker_runtime_invalid_response", "Executor returned invalid JSON") from exc
        if "error" in result:
            raise BrokerError(result["error"]["code"], result["error"]["message"])
        return result["result"]

    def execute(self, setup_sql, sql):
        name = "dbcas-broker-" + uuid.uuid4().hex
        deadline = time.monotonic() + self.settings.sandbox_container_lifetime_seconds
        try:
            self._docker(self._create_args(name))
            with self._lock:
                self._leases[name] = deadline
            self._docker(["docker", "start", name])
            schema = self._call(name, "provision", setup_sql, None)
            result = self._call(name, "execute", sql, schema)
            return result
        except subprocess.SubprocessError as exc:
            raise BrokerError("broker_runtime_unavailable", "Executor transport failed") from exc
        finally:
            self.reap()

    def reap(self):
        now = time.monotonic()
        with self._lock:
            expired = [name for name, deadline in self._leases.items() if deadline <= now]
            for name in expired:
                self._leases.pop(name, None)
        for name in expired:
            try:
                self._docker(["docker", "rm", "-f", name])
            except (subprocess.SubprocessError, BrokerError):
                logger.warning("broker reaper could not remove %s", name)


class FakeRuntime(ConstrainedRuntime):
    """Deterministic no-Docker runtime used by tests and the stub mode."""

    def execute(self, setup_sql, sql):
        return {"success": True, "columns": ["one"], "rows": [[1]], "row_count": 1,
                "execution_time_ms": 0, "error_type": None, "error_message": None}


def build_runtime(settings):
    if settings.sandbox_broker_runtime == "stub":
        return FakeRuntime(settings)
    return ConstrainedRuntime(settings)
