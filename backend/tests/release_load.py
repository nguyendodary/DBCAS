"""Repeatable 100-learner network load gate against tests/release_server.py.

The server must own disposable containers and expose its test fixture API.
This script refuses the normal API port, does not call a real provider, and
records aggregate timings/statuses only, never tokens or learner identifiers.
"""
import argparse
import asyncio
import json
import math
from pathlib import Path
import statistics
import subprocess
import time
from urllib.parse import urlsplit
import httpx


def summary(samples):
    times = sorted(sample["ms"] for sample in samples)
    def percentile(p):
        return round(times[max(0, math.ceil(len(times) * p) - 1)], 2)
    return {"requests": len(samples), "successes": sum(s["ok"] for s in samples),
        "failures": [s["error"] for s in samples if not s["ok"]], "p50_ms": percentile(.50),
        "p95_ms": percentile(.95), "p99_ms": percentile(.99), "mean_ms": round(statistics.mean(times), 2)}


async def main(base, output, profile):
    with httpx.Client(base_url=base, timeout=180) as setup:
        logged = setup.post('/api/v1/auth/login', json={"email": "release-admin@test.dev", "password": "ReleaseTest123!"})
        logged.raise_for_status()
        admin_headers = {"Authorization": f"Bearer {logged.json()['access_token']}"}
        fixture = setup.get('/__test/fixture', headers=admin_headers)
        fixture.raise_for_status()
        users_response = setup.post('/__test/load-fixture', headers=admin_headers)
        users_response.raise_for_status()
        users = users_response.json()
    if len(users) != 100:
        raise RuntimeError("The release fixture must provision exactly 100 disposable learners")
    phases = {}
    limits = httpx.Limits(max_connections=100, max_keepalive_connections=100, keepalive_expiry=2)
    async with httpx.AsyncClient(base_url=base, limits=limits, timeout=60) as client:
        active, peak = 0, 0
        async def hit(user, phase):
            nonlocal active, peak
            sid, q = user['session_id'], user['question']
            routes = {
                'auth_validation': ('GET', '/api/v1/auth/me', None),
                'assessment_list': ('GET', '/api/v1/assessments', None),
                'session_state': ('GET', f'/api/v1/sessions/{sid}', None),
                'draft_save': ('PUT', f'/api/v1/sessions/{sid}/draft', {'question_id': q['question_id'], 'revision': 1, 'selected_option_id': q['options'][0]['option_id']}),
                'answer_submission': ('POST', f'/api/v1/sessions/{sid}/submit', {'question_id': q['question_id'], 'selected_option_id': q['options'][0]['option_id']}),
                'finalization': ('POST', f'/api/v1/sessions/{sid}/finish', None),
                'competency_read': ('GET', f'/api/v1/sessions/{sid}/competency', None),
            }
            method, route, data = routes[phase]
            began = time.perf_counter()
            active += 1
            peak = max(peak, active)
            error = None
            try:
                response = await client.request(method, route, json=data, headers={'Authorization': f"Bearer {user['token']}"})
                if response.status_code != 200:
                    error = f'{phase}: HTTP {response.status_code}'
                else:
                    body = response.json()
                    valid = {'auth_validation': lambda: 'Learner' in body['roles'],
                        'assessment_list': lambda: len(body) > 0,
                        'session_state': lambda: body['session_id'] == sid,
                        'draft_save': lambda: body['revision'] == 1,
                        'answer_submission': lambda: body['state']['answered_count'] == 1,
                        'finalization': lambda: body['status'] == 'completed',
                        'competency_read': lambda: len(body['concepts']) > 0}[phase]()
                    if not valid: error = f'{phase}: invalid domain response'
            except Exception as exc:
                error = f'{phase}: {type(exc).__name__}'
            finally:
                active -= 1
            return {'ms': (time.perf_counter() - began) * 1000, 'ok': error is None, 'error': error}
        async def scheduled(user, phase, index):
            # Normal-load protocol: 100 active identities, 20 arrivals/sec.
            # Intentional arrival delay is excluded from request latency.
            # Burst protocol starts all 100 requests together, unchanged.
            if profile == 'normal':
                await asyncio.sleep(index * .05)
            return await hit(user, phase)
        # Warm a representative path separately; warm-up is excluded from results.
        await hit(users[0], 'auth_validation')
        for phase in ['auth_validation', 'assessment_list', 'session_state', 'draft_save', 'answer_submission', 'finalization', 'competency_read']:
            samples = await asyncio.gather(*(scheduled(user, phase, i) for i, user in enumerate(users)))
            phases[phase] = summary(samples)
        repeated = []
        for _ in range(3):
            repeated.extend(await asyncio.gather(*(scheduled(user, 'competency_read', i) for i, user in enumerate(users))))
        phases['steady_competency_reads'] = summary(repeated)
    manifest = json.loads((Path(__file__).resolve().parents[3] / '_review/remediation/release-containers.json').read_text(encoding='utf-8'))
    stats = subprocess.run(['docker', 'stats', '--no-stream', '--format', '{{.Name}}: {{.CPUPerc}} / {{.MemUsage}}', *manifest['containers']], capture_output=True, text=True, timeout=30)
    report = {'concurrency': 100, 'transport': 'real HTTP, 100 connections; release server defaults to two API workers',
        'profile': profile, 'peak_in_flight_requests': peak,
        'arrival_pattern': '100 synchronized requests per phase' if profile == 'burst' else '100 active learners, staggered at 20 requests/sec; arrival delay excluded from latency',
        'database': 'disposable PostgreSQL 17', 'ai': 'real service with MockTransport; no live calls',
        'phases': phases, 'total_requests': sum(p['requests'] for p in phases.values()),
        'failures': sum(len(p['failures']) for p in phases.values()),
        'resource_observation': stats.stdout.strip().splitlines() if stats.returncode == 0 else ['docker stats unavailable'],
        'nfr_standard_api_mean_under_500ms': all(p['mean_ms'] <= 500 for p in phases.values())}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({k: report[k] for k in ['concurrency', 'total_requests', 'failures', 'nfr_standard_api_mean_under_500ms']}))
    for name, result in phases.items():
        print(f"{name}: p50={result['p50_ms']}ms p95={result['p95_ms']}ms p99={result['p99_ms']}ms failures={len(result['failures'])}")
    if report['failures']:
        raise SystemExit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', default='http://127.0.0.1:8100')
    parser.add_argument('--output', type=Path, default=Path('../../_review/remediation/load-results.json'))
    parser.add_argument('--profile', choices=['burst', 'normal'], default='burst')
    args = parser.parse_args()
    endpoint = urlsplit(args.base)
    if endpoint.hostname != '127.0.0.1' or endpoint.port != 8100 or endpoint.scheme != 'http':
        raise SystemExit('Load gate only supports the isolated localhost:8100 release server')
    asyncio.run(main(args.base, args.output, args.profile))
