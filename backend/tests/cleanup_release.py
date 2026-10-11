"""Remove only the disposable containers recorded by this browser test run."""
import json
from pathlib import Path
import subprocess

manifest = Path(__file__).resolve().parents[3] / "_review/remediation/release-containers.json"
if manifest.exists():
    owned = json.loads(manifest.read_text(encoding="utf-8"))
    for name in owned["containers"]:
        result = subprocess.run(["docker", "inspect", "--format", '{{index .Config.Labels "dbcas.test-run"}}', name], capture_output=True, text=True)
        if result.returncode == 0:
            if result.stdout.strip() != owned["run_id"]:
                raise RuntimeError("Test cleanup refused: container ownership does not match")
            subprocess.run(["docker", "rm", "-f", name], check=True, capture_output=True)
