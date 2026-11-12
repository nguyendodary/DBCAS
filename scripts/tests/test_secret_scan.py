"""Synthetic values are constructed at runtime; no real credentials are fixtures."""
import base64
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

SPEC = importlib.util.spec_from_file_location('scan_secrets', Path(__file__).resolve().parents[1] / 'scan_secrets.py')
scanner = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = scanner
SPEC.loader.exec_module(scanner)


def fake_jwt():
    encode = lambda value: base64.urlsafe_b64encode(json.dumps(value).encode()).rstrip(b'=')
    return b'.'.join([encode({'alg': 'fake-only'}), encode({'exp': 1, 'iat': 0}), b'not-a-real-signature'])


class SecretScanTests(unittest.TestCase):
    def test_required_patterns_are_detected_without_returning_values(self):
        samples = [fake_jwt(), b'sk-' + b'fake' * 8, b'ghp_' + b'X' * 30,
                   b'AKIA' + b'X' * 16, b'-----BEGIN ' + b'PRIVATE KEY-----',
                   (b'client_' + b'secret="synthetic-secret"')]
        for sample in samples:
            with self.subTest(length=len(sample)):
                result = scanner.scan_bytes('fixture.txt', sample)
                self.assertEqual(len(result), 1)
                self.assertNotIn(sample.decode(), repr(result))

    def test_exact_fixture_allowlist_does_not_allow_other_values_or_paths(self):
        value = fake_jwt()
        entry = {'path': 'tests/fake.txt', 'rule': 'jwt', 'sha256': hashlib.sha256(value).hexdigest(),
                 'reason': 'Fake fixture: deliberately invalid runtime JWT for scanner testing.'}
        allowed = scanner.load_allowlist(json.dumps([entry]))
        self.assertEqual(scanner.scan_bytes('tests/fake.txt', value, allowed), [])
        self.assertEqual(len(scanner.scan_bytes('source.txt', value, allowed)), 1)
        self.assertEqual(len(scanner.scan_bytes('tests/fake.txt', value + b'changed', allowed)), 1)

    def test_wildcard_or_unexplained_allowlist_is_rejected(self):
        for path, reason in [('tests/*', 'Fake fixture: sample'), ('tests/fake', 'ignore this')]:
            with self.assertRaises(ValueError):
                scanner.load_allowlist(json.dumps([{'path': path, 'rule': 'jwt', 'sha256': 'a' * 64, 'reason': reason}]))

    def test_zip_and_office_members_are_inspected(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
            archive.writestr('word/document.xml', fake_jwt())
        result = scanner.scan_bytes('document.docx', buffer.getvalue())
        self.assertTrue(any(item.path == 'document.docx!word/document.xml' and item.rule == 'jwt' for item in result))

    def test_bad_or_oversized_archives_fail_closed(self):
        self.assertEqual(scanner.scan_bytes('trace.zip', b'invalid')[0].rule, 'unreadable-archive')
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as archive:
            archive.writestr('sample.txt', b'data')
        original = scanner.MAX_ARCHIVE_BYTES
        try:
            scanner.MAX_ARCHIVE_BYTES = 1
            self.assertEqual(scanner.scan_bytes('trace.zip', buffer.getvalue())[0].rule, 'unreadable-archive')
        finally:
            scanner.MAX_ARCHIVE_BYTES = original

    def test_empty_or_variable_client_secret_is_not_a_literal(self):
        self.assertEqual(scanner.scan_bytes('config.py', b'client_' + b'secret=""\nclient_' + b'secret=settings.provider'), [])

    def test_unquoted_config_literals_are_detected_but_variable_expansions_are_not(self):
        self.assertEqual(len(scanner.scan_bytes('.env.fixture', b'CLIENT_' + b'SECRET=synthetic-only')), 1)
        self.assertEqual(scanner.scan_bytes('compose.yml', b'CLIENT_' + b'SECRET: ${FROM_ENV}'), [])

    def test_staged_blob_cannot_be_hidden_by_clean_working_copy(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(['git', 'init', '-q', str(root)], check=True)
            (root / 'scripts').mkdir()
            (root / scanner.ALLOWLIST).write_text('[]')
            path = root / 'sample.txt'
            path.write_bytes(fake_jwt())
            subprocess.run(['git', '-C', str(root), 'add', '.'], check=True, capture_output=True)
            path.write_text('clean working copy')
            _, findings = scanner.scan_repository(root, staged=True)
            self.assertEqual(len(findings), 1)
            self.assertEqual(findings[0].path, 'sample.txt')


if __name__ == '__main__':
    unittest.main()
