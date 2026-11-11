"""Complete request frames must not depend on Docker forwarding stdin EOF."""
import io
import json
import os
from types import SimpleNamespace
import threading
import time

import pytest
from app import sandbox_job
from app.config import get_settings
from app.services.ephemeral_sandbox import EphemeralSandboxRunner


def test_complete_frame_does_not_wait_for_stdin_eof(monkeypatch):
    read_fd, write_fd = os.pipe()
    reader, writer = os.fdopen(read_fd, 'rb'), os.fdopen(write_fd, 'wb')
    monkeypatch.setattr(sandbox_job.sys, 'stdin', SimpleNamespace(buffer=reader))
    monkeypatch.setattr(sandbox_job, 'SandboxRunner', lambda _: SimpleNamespace(validate_environment=lambda: []))
    errors = []
    def run():
        try:
            sandbox_job.main()
        except Exception as exc:
            errors.append(exc)
    thread = threading.Thread(target=run, daemon=True)
    try:
        thread.start()
        writer.write(b'{"operation":"validate","limits":{}}\n')
        writer.flush()
        thread.join(timeout=1)
        assert not thread.is_alive(), 'A complete JSON line must execute while the stdin writer remains open'
        assert not errors
    finally:
        writer.close()
        thread.join(timeout=5)
        reader.close()


def test_protocol_rejects_oversized_frame(monkeypatch):
    monkeypatch.setattr(sandbox_job.sys, 'stdin', SimpleNamespace(buffer=io.BytesIO(b'x' * 100_001 + b'\n')))
    with pytest.raises(ValueError, match='protocol limit'):
        sandbox_job.main()


@pytest.mark.parametrize('ending', [b'\n', b'\r\n'])
@pytest.mark.parametrize('size', [99_999, 100_000])
def test_framing_preserves_the_payload_byte_limit(monkeypatch, ending, size):
    payload = b'{"operation":"validate","limits":{}}'
    raw = b' ' * (size - len(payload)) + payload + ending
    monkeypatch.setattr(sandbox_job.sys, 'stdin', SimpleNamespace(buffer=io.BytesIO(raw)))
    monkeypatch.setattr(sandbox_job, 'SandboxRunner', lambda _: SimpleNamespace(validate_environment=lambda: []))
    if size == 100_000:
        with pytest.raises(ValueError, match='protocol limit'):
            sandbox_job.main()
    else:
        sandbox_job.main()


def test_caller_frames_unicode_and_embedded_newlines_without_shell_arguments(monkeypatch):
    runner = EphemeralSandboxRunner(get_settings())
    runner.deadlines['fixture'] = time.monotonic() + 30
    requests = []
    def docker(*args, **kwargs):
        requests.append((args, kwargs['input']))
        return '{"result": []}'
    monkeypatch.setattr(runner, '_docker', docker)
    sql = "SELECT 'Tiếng Việt';\nSELECT 2"
    assert runner._call('fixture', 'execute', sql) == []
    args, frame = requests[0]
    assert sql not in args
    assert frame.endswith('\n') and frame.count('\n') == 1
    assert json.loads(frame)['sql'] == sql
