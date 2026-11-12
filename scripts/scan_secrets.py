"""Scan Git's working tree or staged blobs; failures report paths, never values."""
import argparse
from dataclasses import dataclass
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ALLOWLIST = 'scripts/secret_scan_allowlist.json'
MAX_ARCHIVE_BYTES = 128 * 1024 * 1024
PATTERNS = {
    'jwt': re.compile(rb'\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b'),
    'provider-key': re.compile(rb'\bsk-[A-Za-z0-9_-]{20,}\b'),
    'github-token': re.compile(rb'\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b'),
    'aws-key': re.compile(rb'\bAKIA[0-9A-Z]{16}\b'),
    'private-key': re.compile(rb'-----BEGIN (?:[A-Z0-9]+ )?PRIVATE KEY-----'),
    'client-secret': re.compile(
        rb'''(?i)\b(?:[a-z0-9]+_)*client_secret["']?\s*[:=]\s*["']([^"'\r\n]+)["']'''),
    'client-secret-unquoted': re.compile(
        rb'''(?im)^\s*(?:[a-z0-9]+_)*client_secret\s*[:=]\s*([^\s"'#${][^\s#]*)'''),
}


@dataclass(frozen=True)
class Finding:
    path: str
    rule: str
    line: int
    digest: str


def git(root, *args):
    return subprocess.check_output(['git', *args], cwd=root, stderr=subprocess.DEVNULL)


def load_allowlist(data):
    entries = json.loads(data)
    allowed = set()
    for entry in entries:
        if (set(entry) != {'path', 'rule', 'sha256', 'reason'} or
                entry['rule'] not in PATTERNS or
                not re.fullmatch(r'[a-f0-9]{64}', entry['sha256']) or
                any(part in entry['path'] for part in ('*', '..', '\\')) or
                not entry['reason'].startswith('Fake fixture:')):
            raise ValueError('Invalid fixture allowlist entry')
        allowed.add((entry['path'], entry['rule'], entry['sha256']))
    return allowed


def scan_bytes(path, data, allowed=frozenset(), depth=0):
    found = []
    for rule, pattern in PATTERNS.items():
        if rule == 'client-secret-unquoted' and not (
                '.env' in Path(path).name or Path(path).suffix.lower() in {'.yml', '.yaml', '.ini', '.cfg', '.properties'}):
            continue
        for match in pattern.finditer(data):
            value = match.group(1) if rule.startswith('client-secret') else match.group(0)
            if not value.strip():
                continue
            digest = hashlib.sha256(value).hexdigest()
            if (path, rule, digest) not in allowed:
                found.append(Finding(path, rule, data.count(b'\n', 0, match.start()) + 1, digest))
    if data.startswith(b'PK\x03\x04') or Path(path).suffix.lower() in {'.zip', '.docx', '.xlsx', '.pptx'}:
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                members = archive.infolist()
                if depth >= 3 or sum(member.file_size for member in members) > MAX_ARCHIVE_BYTES:
                    raise ValueError('Archive exceeds inspection limit')
                for member in members:
                    if not member.is_dir():
                        found.extend(scan_bytes(path + '!' + member.filename, archive.read(member), allowed, depth + 1))
        except (ValueError, OSError, RuntimeError, zipfile.BadZipFile, NotImplementedError):
            found.append(Finding(path, 'unreadable-archive', 0, ''))
    return found


def scan_repository(root=ROOT, staged=False):
    if staged:
        names = git(root, 'diff', '--cached', '--name-only', '--diff-filter=ACMR', '-z').split(b'\0')
        reader = lambda name: git(root, 'show', ':' + name)
    else:
        names = git(root, 'ls-files', '--cached', '--others', '--exclude-standard', '-z').split(b'\0')
        reader = lambda name: (root / name).read_bytes()
    try:
        allow_data = git(root, 'show', ':' + ALLOWLIST) if staged else (root / ALLOWLIST).read_bytes()
        allowed = load_allowlist(allow_data)
    except FileNotFoundError:
        allowed = set()
    found, count = [], 0
    for name in sorted(set(name.decode('utf-8') for name in names if name)):
        if not staged and not (root / name).exists():
            continue  # unstaged deletion; the staged gate still inspects its blob
        try:
            found.extend(scan_bytes(name, reader(name), allowed))
        except OSError:
            found.append(Finding(name, 'unreadable-file', 0, ''))
        count += 1
    return count, found


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--staged', action='store_true', help='Read changed Git index blobs, not working copies')
    args = parser.parse_args()
    try:
        count, found = scan_repository(staged=args.staged)
    except (ValueError, OSError, subprocess.SubprocessError, json.JSONDecodeError):
        print('Secret scan configuration/index error; no credential contents were printed.')
        return 2
    for path, rule, line in sorted({(item.path, item.rule, item.line) for item in found}):
        print(f'FAIL {path}:{line} [{rule}]')
    print(f'Secret scan: {count} files; {len(found)} findings; mode={"staged" if args.staged else "tree"}.')
    return 1 if found else 0


if __name__ == '__main__':
    raise SystemExit(main())
