"""Four concurrent real sandbox executions, separate from the HTTP burst."""
import asyncio
import json
from pathlib import Path
import time
import httpx
from release_load import summary


async def main():
    base = 'http://127.0.0.1:8100'
    # Match the HTTP load gate's fresh-connection protocol. Native Windows
    # worker socket sharing can leave a reused keep-alive connection stalled.
    with httpx.Client(base_url=base, timeout=120, trust_env=False, headers={'Connection': 'close'}) as setup:
        login = setup.post('/api/v1/auth/login', json={'email': 'release-admin@test.dev', 'password': 'ReleaseTest123!'})
        login.raise_for_status()
        fixture = setup.post('/__test/load-fixture?count=4&sql=true', headers={'Authorization': 'Bearer ' + login.json()['access_token']})
        fixture.raise_for_status()
        learners = fixture.json()
    assert len(learners) == 4 and all(u['question']['question_type'] == 'sql' for u in learners)
    samples = []
    async with httpx.AsyncClient(base_url=base, timeout=60, trust_env=False, headers={'Connection': 'close'}) as client:
        async def run(user):
            began = time.perf_counter()
            error = None
            try:
                result = await client.post(f"/api/v1/sessions/{user['session_id']}/sql-run",
                    headers={'Authorization': 'Bearer ' + user['token']},
                    json={'question_id': user['question']['question_id'], 'sql': user['sql_answer']})
                if result.status_code != 200:
                    error = f'HTTP {result.status_code}'
                else:
                    body = result.json()
                    if body.get('error') or not body.get('columns'):
                        error = 'Invalid sandbox result'
            except Exception as exc:
                error = type(exc).__name__
            return {'ms': (time.perf_counter() - began) * 1000, 'ok': error is None, 'error': error}
        for _ in range(3):
            samples.extend(await asyncio.gather(*(run(u) for u in learners)))
    report = {'concurrency': 4, 'rounds': 3, 'backend': 'two API workers, real disposable PostgreSQL sandbox', **summary(samples)}
    output = Path(__file__).resolve().parents[3] / '_review/remediation/sql-load-results.json'
    output.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report))
    if report['failures']:
        raise SystemExit(1)


if __name__ == '__main__':
    asyncio.run(main())
