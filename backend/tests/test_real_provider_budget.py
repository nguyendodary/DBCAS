"""Deterministic equivalents always run; no provider access is needed."""
import json
from concurrent.futures import ThreadPoolExecutor
import pytest
from real_provider_qa import CallLedger, BudgetExceeded, install_meter


@pytest.mark.parametrize('prior', [None, -1, 60, '27', True])
def test_real_budget_requires_verified_integer_history(tmp_path, prior):
    with pytest.raises(ValueError):
        CallLedger(tmp_path / 'ledger.json', prior)


def test_real_budget_counts_timeouts_and_survives_restart_without_secrets(tmp_path):
    path = tmp_path / 'ledger.json'
    ledger = CallLedger(path, 27)
    index = ledger.reserve(b'synthetic request with a private answer')
    assert json.loads(path.read_text())['calls'][0]['status'] == 'started'
    ledger.finish(index, 'ReadTimeout', 1500)
    ledger = CallLedger(path, 27)
    index = ledger.reserve(b'retry')
    ledger.finish(index, 200, 1200, {'model': 'test-model', 'usage': {'total_tokens': 12},
                                  'choices': [{'content': 'private response'}], 'secret': 'private credential'})
    data = json.loads(path.read_text())
    assert [entry['number'] for entry in data['calls']] == [28, 29]
    assert data['calls'][1]['usage'] == {'total_tokens': 12}
    assert 'private' not in path.read_text()
    with pytest.raises(ValueError):
        CallLedger(path, 0)


def test_real_budget_remains_below_sixty_with_concurrent_workers(tmp_path):
    ledger = CallLedger(tmp_path / 'ledger.json', 57)
    def send(_):
        try:
            return ledger.reserve(b'synthetic')
        except BudgetExceeded:
            return None
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(send, range(20)))
    assert sum(result is not None for result in results) == 2
    assert ledger.state['calls'][-1]['number'] == 59


@pytest.mark.parametrize('status', [200, 503, 'timeout'])
def test_meter_counts_wire_attempt_before_timeout_and_blocks_retry(tmp_path, monkeypatch, status):
    import httpx
    forwarded = []
    def wire(transport, request):
        forwarded.append(request)
        if status == 'timeout':
            raise httpx.ReadTimeout('synthetic timeout')
        return httpx.Response(status, json={'model': 'test-model', 'usage': {'total_tokens': 12},
                                           'choices': [{'message': {'content': 'private response'}}]})
    monkeypatch.setattr(httpx.HTTPTransport, 'handle_request', wire)
    ledger = CallLedger(tmp_path / 'ledger.json', 58)
    install_meter(ledger, 'provider.test')
    with httpx.Client() as client:
        if status == 'timeout':
            with pytest.raises(httpx.ReadTimeout):
                client.post('https://provider.test/v1/chat/completions', json={'private': 'answer'})
        else:
            response = client.post('https://provider.test/v1/chat/completions', json={'private': 'answer'})
            assert response.status_code == status
            assert response.json()['choices'][0]['message']['content'] == 'private response'
        with pytest.raises(httpx.ConnectError, match='budget exhausted'):
            client.post('https://provider.test/v1/chat/completions', json={'private': 'answer'})
    assert len(forwarded) == 1
    assert len(ledger.state['calls']) == 1
    assert ledger.state['calls'][0]['status'] == ('ReadTimeout' if status == 'timeout' else status)
    assert 'private' not in ledger.path.read_text()
