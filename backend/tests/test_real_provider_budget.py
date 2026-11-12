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


def test_new_key_budget_is_exactly_eighty_and_survives_concurrent_reservations(tmp_path):
    ledger = CallLedger(tmp_path / 'ledger.json', 0, maximum_total=80, key='synthetic-key-0001', run='run1')
    def reserve(_):
        try:
            return ledger.reserve(b'{"response_format":{"json_schema":{"name":"evaluation"}}}')
        except BudgetExceeded:
            return None
    with ThreadPoolExecutor(max_workers=12) as pool:
        results = list(pool.map(reserve, range(100)))
    assert sum(value is not None for value in results) == 80
    assert [e['number'] for e in ledger.state['calls']] == list(range(1, 81))
    assert all(e['feature'] == 'evaluation' and e['test'] == 'run1' for e in ledger.state['calls'])
    restarted = CallLedger(ledger.path, 0, maximum_total=80, key='synthetic-key-0001')
    with pytest.raises(BudgetExceeded):
        restarted.reserve(b'retry after restart')
    with pytest.raises(ValueError, match='key does not match'):
        CallLedger(ledger.path, 0, maximum_total=80, key='different-key-0002')
    assert 'synthetic-key' not in ledger.path.read_text()


def test_ledger_records_usage_and_estimates_without_model_or_response_content(tmp_path):
    ledger = CallLedger(tmp_path / 'ledger.json', 0, maximum_total=80)
    index = ledger.reserve(b'{"private":"learner answer"}')
    ledger.finish(index, 200, 123.4, {'model': 'private-model', 'provider': 'private-provider',
        'usage': {'prompt_tokens': 17, 'completion_tokens': 9, 'total_tokens': 26},
        'choices': [{'message': {'content': 'private answer'}}]})
    entry = ledger.state['calls'][0]
    assert (entry['approximate_input_tokens'], entry['approximate_output_tokens']) == (17, 9)
    assert entry['token_method'] == 'provider-reported usage' and entry['duration_ms'] == 123
    second = ledger.reserve(b'12345678')
    ledger.finish(second, 200, 1, {'choices': [{'message': {'content': '12345678'}}]})
    assert ledger.state['calls'][second]['approximate_output_tokens'] == 2
    assert 'private' not in ledger.path.read_text()


@pytest.mark.parametrize('cap', [0, 81, True, '80'])
def test_no_job_can_increase_the_real_request_budget_above_eighty(tmp_path, cap):
    with pytest.raises(ValueError):
        CallLedger(tmp_path / 'ledger.json', 0, maximum_total=cap)


@pytest.mark.parametrize('status,message,category', [
    (404, 'No endpoints support all parameters: private', 'unsupported_parameters'),
    (400, 'Reasoning is mandatory: private', 'reasoning_required'),
    (404, 'Unknown model does not exist: private', 'model_unavailable'),
    (401, 'private', 'credentials_rejected'),
])
def test_meter_classifies_failures_without_recording_provider_messages(tmp_path, status, message, category):
    ledger = CallLedger(tmp_path / 'ledger.json', 0, maximum_total=80)
    index = ledger.reserve(b'synthetic')
    ledger.finish(index, status, 1, {'error': {'message': message}})
    assert ledger.state['calls'][0]['failure_category'] == category
    assert 'private' not in ledger.path.read_text()


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
