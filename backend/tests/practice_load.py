"""Current-practice HTTP concurrency gate, only with the local fake provider.

Run through scripts/browser-qa.mjs so its owned Compose override guarantees
that no real provider is reachable. Uses new disposable learner identities,
preserves existing histories and restores the prior global release setting.
Only aggregate latency/count results are written; no tokens or answers.
"""
import argparse
import asyncio
from collections import defaultdict
from contextlib import AsyncExitStack
from decimal import Decimal, ROUND_HALF_UP
import json
import os
from pathlib import Path
import time
from urllib.parse import urlsplit
from uuid import uuid4

import httpx

from release_load import summary


class Probe:
    def __init__(self):
        self.samples = defaultdict(list)
        self.active = defaultdict(int)
        self.peak = defaultdict(int)
        self.backpressure = defaultdict(int)

    async def hit(self, client, phase, method, url, **kwargs):
        began = time.perf_counter()
        self.active[phase] += 1
        self.peak[phase] = max(self.peak[phase], self.active[phase])
        error = None
        try:
            response = await client.request(method, url, **kwargs)
            if not 200 <= response.status_code < 300:
                error = f"HTTP {response.status_code}"
            return response
        except Exception as exc:
            error = type(exc).__name__
            raise
        finally:
            self.active[phase] -= 1
            self.samples[phase].append({"ms": (time.perf_counter() - began) * 1000,
                                        "ok": error is None, "error": error})


class Learner:
    def __init__(self, client, probe):
        self.client, self.probe = client, probe
        self.token = None
        self.refresh_token = None
        self.refresh_lock = asyncio.Lock()
        self.state = None
        self.seen = set()

    async def request(self, phase, method, path, body=None, *, authenticated=True, expected=200):
        token = self.token
        headers = {"Authorization": f"Bearer {token}"} if authenticated else {}
        response = await self.probe.hit(self.client, phase, method, path, json=body, headers=headers)
        if response.status_code == 401 and authenticated:
            async with self.refresh_lock:
                if self.token == token:
                    refreshed = await self.probe.hit(self.client, "token_refresh", "POST", "auth/refresh", json={"refresh_token": self.refresh_token})
                    assert refreshed.status_code == 200, "Refresh did not preserve the learner session"
                    self.token = refreshed.json()["access_token"]
                    self.refresh_token = refreshed.json()["refresh_token"]
            response = await self.probe.hit(self.client, phase, method, path, json=body,
                headers={"Authorization": f"Bearer {self.token}"})
            headers = {"Authorization": f"Bearer {self.token}"}
        for retry in range(3):
            code = response.json().get("error", {}).get("code") if response.status_code == 503 else None
            if code != "sandbox_busy" or phase not in {"concurrent_sql", "sql_timeout", "sql_cell_limit", "sql_row_limit"}:
                break
            self.probe.backpressure[phase] += 1
            if retry == 2:
                break
            await asyncio.sleep(.25 * (retry + 1))
            response = await self.probe.hit(self.client, phase, method, path, json=body, headers=headers)
        assert response.status_code == expected, f"{phase}: HTTP {response.status_code} ({code if response.status_code == 503 else 'unexpected'})"
        return response.json() if response.content else None

    async def login(self, email, password):
        result = await self.request("login", "POST", "auth/login", {"email": email, "password": password}, authenticated=False)
        self.token = result["access_token"]
        self.refresh_token = result["refresh_token"]


def local_url(value):
    parts = urlsplit(value)
    if parts.scheme != "http" or parts.hostname != "127.0.0.1" or parts.username or parts.password or parts.query:
        raise argparse.ArgumentTypeError("Use a plain 127.0.0.1 HTTP endpoint")
    return value.rstrip("/")


async def settled(*tasks):
    results = await asyncio.gather(*tasks, return_exceptions=True)
    failures = [str(result) if isinstance(result, AssertionError) else type(result).__name__
                for result in results if isinstance(result, BaseException)]
    assert not failures, "; ".join(sorted(set(failures)))
    return results


async def run(args):
    if os.environ.get("LLM_API_KEY", "").strip() or os.environ.get("DBCAS_QA_LOAD_GUARD") != "fake-provider-only":
        raise RuntimeError("Load gate requires the owned fake-provider launcher and an empty real key")
    probe, report = Probe(), {"learners": args.learners, "failures": [], "real_provider_calls": 0}
    started = time.perf_counter()
    password, run_id = "Demo12345!", uuid4().hex[:12]
    async with AsyncExitStack() as stack:
        async def identity():
            client = await stack.enter_async_context(httpx.AsyncClient(base_url=args.base + "/api/v1/",
                timeout=60, trust_env=False, limits=httpx.Limits(max_connections=8)))
            return Learner(client, probe)
        admin = await identity()
        provider = await stack.enter_async_context(httpx.AsyncClient(base_url=args.provider, timeout=5, trust_env=False))
        control = await provider.post("/control", json={"delay_seconds": .25, "failure": False, "hold": False, "reset_peak": True})
        control.raise_for_status()
        provider_before = control.json()
        assert isinstance(provider_before.get("calls"), int) and "peak_active" in provider_before, "Not the local QA provider"
        await admin.login("admin@dbcas.local", password)
        system = await admin.request("system_status", "GET", "admin/system")
        assert system["evaluator_configured"], "The fake evaluator must be enabled"
        learners = [await identity() for _ in range(args.learners)]
        try:
            async def register(index, learner):
                email = f"qa-load-{run_id}-{index}@dbcas.local"
                await learner.request("registration", "POST", "auth/register", {
                    "name": "Controlled load learner", "email": email, "password": password,
                    "password_confirm": password}, authenticated=False, expected=201)
                await learner.login(email, password)
            await settled(*(register(i, learner) for i, learner in enumerate(learners)))
            options = await learners[0].request("practice_options", "GET", "practice/options")
            count = options["question_count"]["max"]
            report.update(question_count=count, concepts=len(options["concepts"]))
            bank = await admin.request("bank_catalog", "GET", "admin/questions")
            report["bank_rows"] = len(bank)
            del bank
            async def begin(learner):
                body = {"concept_ids": [c["concept_id"] for c in options["concepts"]],
                        "difficulties": ["EASY", "MEDIUM", "HARD"], "source": "bank",
                        "question_count": count, "request_id": str(uuid4())}
                first, duplicate = await settled(*(learner.request("duplicate_start", "POST", "practice/start", body) for _ in range(2)))
                assert first["session_id"] == duplicate["session_id"] and first["max_questions"] == count
                learner.state = first
            await settled(*(begin(learner) for learner in learners))
            assert len({u.state["session_id"] for u in learners}) == args.learners
            sql_slots = asyncio.Semaphore(4)
            async def answer(index, learner):
                state, kinds = learner.state, set()
                for _ in range(3):
                    question, sid = state["current_question"], state["session_id"]
                    assert question["question_id"] not in learner.seen
                    learner.seen.add(question["question_id"])
                    kinds.add(question["question_type"])
                    body = {"question_id": question["question_id"]}
                    if question["question_type"] == "mcq":
                        body["selected_option_id"] = question["options"][0]["option_id"]
                    elif question["question_type"] == "sql":
                        body["sql_answer"] = "SELECT 1"
                        async with sql_slots:
                            result = await learner.request("concurrent_sql", "POST", f"sessions/{sid}/sql-run",
                                {"question_id": question["question_id"], "sql": "SELECT 1"})
                            if index == 0:
                                for phase, sql, expected_error in [
                                    ("sql_timeout", "WITH RECURSIVE n AS (SELECT 1 AS x UNION ALL SELECT x+1 FROM n WHERE x<100000000) SELECT max(x) FROM n", "timeout"),
                                    ("sql_cell_limit", "SELECT repeat('x',20000)", "result_too_large"),
                                    ("sql_row_limit", "SELECT generate_series(1,2000)", "result_too_large"),
                                ]:
                                    bounded = await learner.request(phase, "POST", f"sessions/{sid}/sql-run",
                                        {"question_id": question["question_id"], "sql": sql})
                                    assert bounded["success"] is False and bounded["error_type"] == expected_error, f"{phase} did not enforce its configured limit"
                                    report.setdefault("sql_limit_results", {})[phase] = {
                                        "error_type": bounded["error_type"], "execution_time_ms": bounded["execution_time_ms"]}
                        assert result["success"] and result["rows"] == [[1]]
                    else:
                        body["essay_answer"] = "Chuẩn hóa cần xét khóa, phụ thuộc hàm và phép phân rã không mất mát. Cần kiểm chứng dữ liệu bằng ví dụ và kết quả truy vấn."
                    drafts = await settled(*(learner.request("duplicate_draft", "PUT", f"sessions/{sid}/draft", {**body, "revision": 1}) for _ in range(2)))
                    assert all(row["revision"] == 1 for row in drafts)
                    responses = await settled(*(learner.request("duplicate_submission", "POST", f"sessions/{sid}/submit", body) for _ in range(2)))
                    assert responses[0]["answer"]["attempt_id"] == responses[1]["answer"]["attempt_id"]
                    assert all(row["answer"]["score"] is None for row in responses), "Unreleased score leaked"
                    assert responses[0]["state"]["answered_count"] == responses[1]["state"]["answered_count"]
                    state = responses[0]["state"]
                assert kinds == {"mcq", "sql", "essay"}, "Balanced plan did not deliver all three types"
                learner.state = state
            await settled(*(answer(index, learner) for index, learner in enumerate(learners)))
            async def finish(learner):
                sid = learner.state["session_id"]
                rows = await settled(*(learner.request("duplicate_finish", "POST", f"sessions/{sid}/finish") for _ in range(2)))
                assert all(row["status"] == "completed" for row in rows)
                deadline = time.monotonic() + 90
                while time.monotonic() < deadline:
                    evaluation = await learner.request("concurrent_evaluation", "GET", f"evaluations/attempts/{sid}")
                    if evaluation["status"] == "awaiting_approval":
                        break
                    await asyncio.sleep(.25)
                else:
                    raise AssertionError("Concurrent grading did not reach admin review within the bounded deadline")
                detail = await admin.request("review", "GET", f"admin/grading-reviews/{sid}")
                await admin.request("publish", "POST", f"admin/grading-reviews/{sid}/publish",
                                    {"revision": detail["revision"]})
                evaluation = await learner.request("evaluation_after_review", "GET", f"evaluations/attempts/{sid}")
                assert evaluation["status"] == "ready", "Approved result was not released"
                assert evaluation["result"]["evaluator_fallback"] is False, "Fake HTTP evaluator was bypassed"
                evidence = await learner.request("evidence", "GET", f"sessions/{sid}/evidence")
                assert len(evidence["items"]) == count and len({q["question_id"] for q in evidence["items"]}) == count
                assert sum(q["submitted_at"] is not None for q in evidence["items"]) == count
                earned = sum(Decimal(q["score"]) for q in evidence["items"])
                possible = sum(Decimal(q["points"]) for q in evidence["items"])
                expected = (earned * 100 / possible).quantize(Decimal(".01"), rounding=ROUND_HALF_UP)
                history = await learner.request("history", "GET", "sessions")
                assert len(history) == 1 and Decimal(history[0]["overall_result_pct"]) == expected
                stats = await learner.request("statistics", "GET", "sessions/statistics")
                assert stats["published_formal_sessions"] == 1
                return sid
            sessions = await settled(*(finish(learner) for learner in learners))
            for index, learner in enumerate(learners):
                response = await learner.client.get(f"sessions/{sessions[(index + 1) % len(sessions)]}/evidence",
                    headers={"Authorization": f"Bearer {learner.token}"})
                assert response.status_code == 404, "Cross-learner evidence was exposed"
            provider_after = (await provider.get("/health")).json()
            report.update(provider_requests=provider_after["calls"] - provider_before["calls"],
                          provider_peak_concurrency=provider_after["peak_active"], exact_count_cases=args.learners,
                          duplicate_safe_sessions=len(sessions), cross_learner_denials=args.learners)
            # The per-attempt Evaluator can also supply the essay score;
            # a separate essay job is opportunistic, not a second required call.
            assert report["provider_requests"] >= args.learners, "Each attempt must reach the fake HTTP Evaluator"
            assert report["provider_peak_concurrency"] >= 2, "Concurrent provider execution was not observed"
        except Exception as exc:
            report["failures"].append(str(exc) if isinstance(exc, AssertionError) else type(exc).__name__)
        finally:
            try:
                await provider.post("/control", json={"delay_seconds": 1, "failure": False, "hold": False})
            except Exception as exc:
                report["failures"].append("fake_control_restore: " + type(exc).__name__)
    report["elapsed_seconds"] = round(time.perf_counter() - started, 3)
    report["phases"] = {phase: {**summary(samples), "peak_in_flight": probe.peak[phase]} for phase, samples in probe.samples.items()}
    report["http_requests"] = sum(len(samples) for samples in probe.samples.values())
    report["controlled_backpressure_responses"] = dict(probe.backpressure)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    if report["failures"]:
        raise SystemExit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=local_url, required=True)
    parser.add_argument("--provider", type=local_url, required=True)
    parser.add_argument("--learners", type=int, choices=range(4, 21), default=8)
    parser.add_argument("--output", type=Path, required=True)
    asyncio.run(run(parser.parse_args()))
