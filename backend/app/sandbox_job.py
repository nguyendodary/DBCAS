"""Trusted stdin/stdout bridge executed inside an offline ephemeral container."""
from dataclasses import asdict
import json
import sys

from .config import Settings
from .services.sandbox_runner import SandboxError, SandboxRunner


def main():
    raw = sys.stdin.buffer.read(100_000)
    if len(raw) >= 100_000:
        raise ValueError("Sandbox request exceeds the protocol limit")
    payload = json.loads(raw)
    settings = Settings(_env_file=None, deployment_mode="development",
                        sandbox_url="postgresql://learner_ro@/postgres",
                        sandbox_admin_url="postgresql://postgres@/postgres", **payload["limits"])
    runner = SandboxRunner(settings)
    try:
        operation = payload["operation"]
        if operation == "provision":
            result = runner.provision_dataset(payload["sql"])
        elif operation == "execute":
            result = asdict(runner.execute(payload["sql"], schema=payload.get("schema")))
        elif operation == "validate":
            result = runner.validate_environment()
        else:
            raise ValueError("Unknown sandbox operation")
        print(json.dumps({"result": result}, ensure_ascii=False))
    except SandboxError as exc:
        print(json.dumps({"error": {"code": exc.code, "message": exc.message}}))


if __name__ == "__main__":
    main()
