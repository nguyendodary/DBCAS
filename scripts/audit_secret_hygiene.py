"""Scan local secret material against tracked files and reachable Git blobs.

Only filenames, counts and booleans are emitted; never matching content.
"""
import argparse
import json
from pathlib import Path
import re
import subprocess


def git(root, *args, **kwargs):
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, check=True, **kwargs).stdout


def audit(root, env_paths):
    secrets = set()
    files = []
    placeholders = set()
    for path in env_paths:
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            match = re.match(r"\s*([A-Z][A-Z0-9_]*)\s*=\s*(.*?)\s*$", line)
            if match and re.search(r"API_KEY|CLIENT_SECRET|JWT_SECRET|PASSWORD", match[1]):
                value = match[2].strip('"\'')
                if re.search(r"change[_-]?me|replace[_-]?me|test-secret|your[_-]", value, re.I):
                    placeholders.add(match[1])
                elif len(value) >= 20:
                    secrets.add(value.encode())
        files.append({"file": str(path.relative_to(root)) if path.is_relative_to(root) else str(path),
                      "ignored": subprocess.run(["git", "-C", str(path.parent), "check-ignore", "-q", path.name]).returncode == 0})
    suspect = []
    blobs = 0
    objects = git(root, "rev-list", "--objects", "--all").splitlines()
    process = subprocess.Popen(["git", "-C", str(root), "cat-file", "--batch"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    key_pattern = re.compile(rb"sk-(?:proj-|or-v1-)?[A-Za-z0-9_-]{32,}")
    try:
        for entry in objects:
            oid, _, path = entry.partition(b" ")
            process.stdin.write(oid + b"\n")
            process.stdin.flush()
            header = process.stdout.readline().split()
            if len(header) != 3:
                raise RuntimeError("Git object scan did not return a complete header")
            size = int(header[2])
            data = process.stdout.read(size)
            process.stdout.read(1)
            if header[1] != b"blob":
                continue
            blobs += 1
            if any(value in data for value in secrets) or key_pattern.search(data):
                suspect.append({"object": oid.decode(), "path": path.decode(errors="replace")})
    finally:
        process.stdin.close()
        process.wait(timeout=15)
    tracked_suspects = []
    tracked = git(root, "ls-files", "-z").split(b"\0")
    for item in filter(None, tracked):
        path = root / item.decode()
        if path.is_file():
            data = path.read_bytes()
            if any(value in data for value in secrets) or key_pattern.search(data):
                tracked_suspects.append(str(path.relative_to(root)))
    return {"environment_files": files, "secret_material_count": len(secrets),
            "public_placeholder_names_excluded": sorted(placeholders), "history_blobs_scanned": blobs,
            "history_findings": suspect, "tracked_findings": tracked_suspects,
            "pass": not suspect and not tracked_suspects and all(f["ignored"] for f in files)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", action="append", type=Path, default=[])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    result = audit(root, [root / ".env", *[p.resolve() for p in args.env_file]])
    payload = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload)
    raise SystemExit(0 if result["pass"] else 1)
