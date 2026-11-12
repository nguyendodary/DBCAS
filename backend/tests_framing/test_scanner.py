"""PII/secret scanner tests; fake credentials are built at runtime."""
from __future__ import annotations

import base64
import json

from app.services.framing.scanner import has_pii_or_secret, rule_codes, scan_text


def fake_jwt() -> str:
    encode = lambda value: base64.urlsafe_b64encode(json.dumps(value).encode()).rstrip(b"=").decode()
    return ".".join([encode({"alg": "fake-only"}), encode({"exp": 1, "iat": 0}), "not-a-real-signature"])


def test_common_pii_is_detected():
    text = "Email learner.private@example.edu, gọi 090-123-4567, xem https://example.invalid/x"
    assert {"email", "phone", "url"} <= set(rule_codes(scan_text(text)))


def test_vietnamese_labels_and_ids_are_detected():
    text = "Mã sinh viên: SV2026001; CCCD 012345678901; số điện thoại 0912345678"
    codes = set(rule_codes(scan_text(text)))
    assert "labelled-id" in codes
    assert "phone" in codes


def test_secret_patterns_are_detected_without_returning_values():
    samples = [
        ("jwt", fake_jwt()),
        ("provider-key", "sk-" + "a" * 24),
        ("github-token", "ghp_" + "X" * 30),
        ("aws-key", "AKIA" + "X" * 16),
        ("private-key", "-----BEGIN " + "PRIVATE KEY-----"),
        ("client-secret", "client_" + "secret=" + '"' + "synthetic-secret" + '"'),
        ("bearer", "Bearer " + "a" * 20),
    ]
    for expected, sample in samples:
        findings = scan_text(sample)
        assert expected in {finding.rule for finding in findings}, expected
        rendered = " ".join(str(finding) for finding in findings)
        assert sample.split("=")[-1].strip("\"'") not in rendered
        assert sample not in rendered


def test_clean_educational_text_is_not_flagged():
    text = "Khóa chính xác định duy nhất mỗi bản ghi; dạng chuẩn 3NF giảm dư thừa."
    assert not has_pii_or_secret(text)
    assert scan_text(text) == []


def test_extra_terms_are_boundary_aware():
    text = "Học viên Nguyễn Văn A đã nộp bài; Nguyễn Văn An không liên quan."
    findings = scan_text(text, extra_terms=["Nguyễn Văn A"])
    assert findings
    assert all(finding.rule == "pii-term" for finding in findings)
    assert "Nguyễn Văn A" not in repr(findings)
