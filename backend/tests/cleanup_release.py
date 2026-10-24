"""Remove only the disposable containers recorded by this browser test run."""
import json
import os
from pathlib import Path
from docker_runtime import cleanup_owned

manifest = Path(os.environ.get("DBCAS_TEST_MANIFEST", str(Path(__file__).resolve().parents[3] / "_review/remediation/release-containers.json")))
if manifest.exists():
    owned = json.loads(manifest.read_text(encoding="utf-8"))
    failures = []
    for name in owned["containers"]:
        try:
            cleanup_owned(name, owned["run_id"])
        except Exception as exc:
            failures.append(f"{name}: {exc}")
    if failures:
        raise RuntimeError("Disposable browser cleanup incomplete: " + "; ".join(failures))
