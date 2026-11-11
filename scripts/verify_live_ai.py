"""Two opt-in live checks with a persistent five-request cap and no secret output.

Use --env-file explicitly. Without a key the check skips; ordinary tests and
demo traffic never call this script. All evidence is synthetic, no DB writes.
"""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import logging
from pathlib import Path
import sys
from types import SimpleNamespace
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
import httpx


class BudgetExhausted(RuntimeError):
    pass


def save(path, ledger):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


class MeteredTransport(httpx.BaseTransport):
    def __init__(self, path, ledger, inner=None):
        self.path, self.ledger = path, ledger
        self.inner = inner or httpx.HTTPTransport(retries=0)
        self.check = "unset"
        self.prompts = []

    def handle_request(self, request):
        if self.check not in {"evaluator", "generation"} or len(self.ledger["requests"]) >= 5:
            raise BudgetExhausted("Live request budget exhausted")
        body = json.loads(request.content)
        prompt = body["messages"][-1]["content"]
        self.prompts.append(prompt)
        entry = {"number": len(self.ledger["requests"]) + 1, "check": self.check,
                 "reserved_utc": datetime.now(timezone.utc).isoformat(),
                 "prompt_hash": hashlib.sha256(prompt.encode()).hexdigest(),
                 "reasoning": body.get("reasoning", body.get("reasoning_effort")),
                 "uses_temperature": "temperature" in body,
                 "token_parameter": "max_completion_tokens" if "max_completion_tokens" in body else "max_tokens",
                 "status": "reserved"}
        self.ledger["requests"].append(entry)
        save(self.path, self.ledger)  # Reserve durably BEFORE transport, including timeout/failure.
        try:
            response = self.inner.handle_request(request)
            response.read()
            entry["http_status"] = response.status_code
            entry["status"] = "received"
            try:
                payload = response.json()
                entry["usage"] = {key: value for key, value in payload.get("usage", {}).items()
                                  if key in {"prompt_tokens", "completion_tokens", "total_tokens"} and type(value) is int}
                entry["model_accepted"] = response.status_code == 200 and not payload.get("error")
            except (ValueError, AttributeError):
                entry["usage"] = {}
            save(self.path, self.ledger)
            return response
        except Exception as exc:
            entry["status"], entry["failure_type"] = "failed", type(exc).__name__
            save(self.path, self.ledger)
            raise

    def close(self):
        # The provider creates one Client per bounded retry; retain the same
        # counter and underlying pool until the two semantic checks finish.
        pass


def synthetic_attempt():
    return {"version": "two-ai-v4", "mode": "attempt", "attempt_count": 1,
            "score": {"earned": "1", "possible": "3", "percentage": 33.33},
            "history": [{"session_id": 1, "ordinal": 1, "date": datetime.now(timezone.utc).isoformat(),
                         "earned": "1", "possible": "3", "percentage": 33.33}],
            "dimensions": {}, "items": [
                {"attempt_id": 1, "question_id": 1, "type": "mcq", "prompt": "What does SELECT NULL + 1 return?",
                 "answer": "NULL", "reference_answer": "NULL", "points": "1", "score": "1", "rubric": []},
                {"attempt_id": 2, "question_id": 2, "type": "essay", "prompt": "Explain a lossless join decomposition.",
                 "answer": "Joining the decomposed relations must restore exactly the original rows, with no spurious rows.",
                 "reference_answer": "A lossless decomposition can be rejoined without missing or spurious rows.",
                 "points": "2", "score": None, "rubric": [
                     {"level": "Complete", "min": "1.5", "max": "2", "criteria": "Explains exact row restoration"}]}]}


def run(env_file, ledger_path):
    from app.config import Settings
    from app.services import evaluation_pipeline as pipeline
    from app.services.llm import ChatCompletionsProvider, LLMService
    from app.services.practice_generation import generate_entries, template_questions
    from app.services.practice_service import PracticeStart
    from app.services.prompt_builder import validate_prompt

    settings = Settings(_env_file=env_file, deployment_mode="development")
    if not settings.llm_api_key.strip():
        return {"status": "skipped_no_key", "requests": [], "checks": {}}
    if not settings.llm_base_url.strip() or not settings.llm_model.strip():
        return {"status": "skipped_incomplete_configuration", "requests": [], "checks": {}}
    identity = hashlib.sha256(settings.llm_api_key.encode()).hexdigest()[:16]
    if ledger_path.exists():
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
        if ledger.get("key_fingerprint") != identity:
            raise RuntimeError("Use a new ledger for a different key")
        if ledger.get("checks"):
            return ledger  # Never repeat completed/failed checks on a resume.
    else:
        ledger = {"status": "running", "limit": 5, "key_fingerprint": identity,
                  "key_masked": "sk-..." + settings.llm_api_key[-4:],
                  "model_fingerprint": hashlib.sha256(settings.llm_model.encode()).hexdigest()[:16],
                  "created_utc": datetime.now(timezone.utc).isoformat(), "requests": [], "checks": {}}
        save(ledger_path, ledger)
    settings = settings.model_copy(update={"llm_max_retries": 1, "llm_backoff_seconds": 0.0,
                                          "llm_timeout_seconds": 12.0, "prompt_builder_model_path": "",
                                          "evaluation_fake_delay_seconds": 0, "evaluation_fake_error": False})
    transport = MeteredTransport(ledger_path, ledger)
    provider = ChatCompletionsProvider(settings.llm_base_url, settings.llm_api_key,
        timeout_seconds=12, max_retries=1, backoff_seconds=0, transport=transport)
    llm = LLMService(settings, provider=provider)
    # Only stable reason codes are retained; no provider response/error text,
    # request headers, configuration values, or generated prose is logged.
    logging.getLogger("httpx").setLevel(logging.CRITICAL)
    ai_logger = logging.getLogger("dbcas.ai")
    ai_logger.handlers = [logging.NullHandler()]
    ai_logger.propagate = False
    built = []
    original_build = pipeline.build_prompt

    def capture_build(data, **kwargs):
        result = original_build(data, **kwargs)
        validate_prompt(result.prompt, data)
        built.append(result)
        return result

    try:
        transport.check = "evaluator"
        pipeline.build_prompt = capture_build
        data = synthetic_attempt()
        snapshot = deepcopy(data)
        result = pipeline.evaluate(data, llm, settings=settings)
        pipeline.build_prompt = original_build
        prompts = list(transport.prompts)
        check = {"builder_calls": len(built), "builder_purity_validated": len(built) == 1,
                 "data_unchanged": data == snapshot, "built_prompt_hash": result["prompt_hash"],
                 "wire_prompt_equal": bool(prompts) and all(prompt == built[0].prompt for prompt in prompts),
                 "builder_mode": "template", "evaluator_fallback": result["evaluator_fallback"],
                 "question_comments": len(result["evaluation"]["question_comments"])}
        assert check["builder_purity_validated"] and check["data_unchanged"] and check["wire_prompt_equal"]
        fallback = pipeline.evaluate(data, force_fallback=True)
        check["offline_fallback_validated"] = fallback["evaluator_fallback"] and len(fallback["evaluation"]["question_comments"]) == 2
        ledger["checks"]["evaluator"] = check
        save(ledger_path, ledger)

        transport.check = "generation"
        concept = SimpleNamespace(concept_id=1, concept_code="SQL-SELECT", concept_name="SELECT lists",
                                  description="Projection, aliases, expressions and NULL in PostgreSQL SELECT lists.")
        payload = PracticeStart(concept_ids=[1], difficulties=["EASY"], source="ai", question_count=1, request_id=uuid4())
        diagnostics = []
        generated = generate_entries([concept], payload, SimpleNamespace(account_id=1), None, llm, diagnostics=diagnostics)
        ledger["checks"]["generation"] = {"requested": 1, "validated_generated": len(generated),
            "diagnostic_codes": [entry["code"] for entry in diagnostics],
            "offline_template_available": bool(template_questions([concept], payload))}
        ledger["status"] = "complete"
        save(ledger_path, ledger)
    except Exception as exc:
        ledger["status"], ledger["failure_type"] = "incomplete", type(exc).__name__
        save(ledger_path, ledger)
    finally:
        pipeline.build_prompt = original_build
        transport.inner.close()
    return ledger


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.env_file.resolve(), args.ledger.resolve())
    print(json.dumps(result, indent=2))
