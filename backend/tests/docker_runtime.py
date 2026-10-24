"""Bounded Docker commands and ownership-checked disposable-container cleanup."""
import json
import subprocess
import sys
import atexit
import re


def docker_command(*args, timeout=30, **kwargs):
    try:
        return subprocess.run(["docker", *args], capture_output=True, check=True,
                              timeout=timeout, **kwargs)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"Docker {args[0]} timed out after {timeout}s") from exc
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr or b""
        if isinstance(detail, bytes):
            detail = detail.decode("utf-8", errors="replace")
        raise RuntimeError(f"Docker {args[0]} failed ({exc.returncode}): {detail.strip()[:2000]}") from exc


def cleanup_owned(name, run_id):
    """Never remove a foreign container or its volumes, even on error paths."""
    inspected = subprocess.run(["docker", "inspect", name], capture_output=True,
                               timeout=10, check=False)
    if inspected.returncode:
        detail = inspected.stderr.decode("utf-8", errors="replace")
        if re.search(r"\bNo such (?:object|container)\b", detail, re.IGNORECASE):
            return
        raise RuntimeError(f"Cannot verify ownership of disposable container {name}")
    row = json.loads(inspected.stdout)[0]
    if row["Config"].get("Labels", {}).get("dbcas.test-run") != run_id:
        raise RuntimeError(f"Cleanup refused: ownership label mismatch for {name}")
    # Every new harness container uses tmpfs. No named or anonymous data volume
    # is required; refuse unexpected persistent mounts rather than deleting it.
    if any(m.get("Type") in ("volume", "bind") for m in row.get("Mounts", [])):
        raise RuntimeError(f"Cleanup refused: unexpected persistent mount for {name}")
    docker_command("rm", "-f", name, timeout=15)


def cleanup_at_exit(name, run_id):
    try:
        cleanup_owned(name, run_id)
    except Exception as exc:
        print(f"Disposable test cleanup incomplete: {exc}", file=sys.stderr)


def create_owned(name, run_id, owned, receipt, args):
    """Record intent before the daemon can create anything, including timeouts."""
    owned.append(name)
    atexit.register(cleanup_at_exit, name, run_id)
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(json.dumps({"run_id": run_id, "containers": owned}), encoding="utf-8")
    docker_command("create", *args)
    docker_command("start", name)
