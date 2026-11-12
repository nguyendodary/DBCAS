"""Local browser-QA HTTP provider. No real credentials, outbound calls or prompt logs."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import re
import threading
import time

LOCK = threading.Lock()
RELEASE = threading.Event()
RELEASE.set()
STATE = {"delay_seconds": 20, "failure": False, "hold": False, "calls": 0, "active": 0, "peak_active": 0}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def respond(self, status, body):
        content = json.dumps(body, ensure_ascii=False).encode()
        try:
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_GET(self):
        if self.path != "/health":
            return self.respond(404, {"error": "not_found"})
        with LOCK:
            self.respond(200, dict(STATE))

    def do_POST(self):
        completion = self.path == "/v1/chat/completions"
        if completion:
            with LOCK:
                STATE["active"] += 1
                STATE["peak_active"] = max(STATE["peak_active"], STATE["active"])
        try:
            self._post()
        finally:
            if completion:
                with LOCK:
                    STATE["active"] -= 1

    def _post(self):
        try:
            size = int(self.headers.get("Content-Length", 0))
            if not 0 < size <= 262144:
                raise ValueError("invalid_size")
            body = json.loads(self.rfile.read(size))
            if self.path == "/control":
                delay = body.get("delay_seconds", 20)
                failure = body.get("failure", False)
                hold = body.get("hold", False)
                reset_peak = body.get("reset_peak", False)
                if isinstance(delay, bool) or not isinstance(delay, (int, float)) or not 0 <= delay <= 120 or not isinstance(failure, bool) or not isinstance(hold, bool) or not isinstance(reset_peak, bool):
                    raise ValueError("invalid_control")
                with LOCK:
                    STATE.update(delay_seconds=delay, failure=failure, hold=hold)
                    if reset_peak:
                        STATE["peak_active"] = STATE["active"]
                    RELEASE.clear() if hold else RELEASE.set()
                    result = dict(STATE)
                return self.respond(200, result)
            if self.path != "/v1/chat/completions":
                return self.respond(404, {"error": "not_found"})
            schema_name = body.get("response_format", {}).get("json_schema", {}).get("name")
            if schema_name not in {"evaluation", "practice_questions", "essay_grade"}:
                return self.respond(503, {"error": "task_not_simulated"})
            prompt = next(m["content"] for m in body["messages"] if m["role"] == "user")
            with LOCK:
                STATE["calls"] += 1
                delay, failure, hold = STATE["delay_seconds"], STATE["failure"], STATE["hold"]
            # Hold real HTTP work until the browser observes the waiting page.
            # Bound the fixture itself so an interrupted test never hangs a job.
            if hold and not RELEASE.wait(timeout=90):
                return self.respond(504, {"error": "test_release_timeout"})
            time.sleep(delay)
            if failure:
                return self.respond(503, {"error": "simulated_provider_outage"})
            if schema_name == "evaluation":
                from app.services.evaluation_pipeline import rule_evaluation
                data = json.loads(prompt.split("## DỮ LIỆU\n", 1)[1].split("## RUBRIC\n", 1)[0])
                payload = rule_evaluation(data)
                return self.respond(200, {"choices": [{"message": {"content": json.dumps(payload, ensure_ascii=False)}, "finish_reason": "stop"}]})
            if schema_name == "practice_questions":
                from types import SimpleNamespace
                from uuid import uuid4
                from app.services.practice_service import PracticeStart, template_questions
                data = json.loads(prompt[prompt.index('{'):])
                concepts = [SimpleNamespace(concept_id=c["id"], concept_code=c.get("code", c["name"]), concept_name=c["name"], description=c["description"]) for c in data["concepts"]]
                bands = sorted({"EASY" if level <= 2 else "MEDIUM" if level == 3 else "HARD" for level in data["difficulty_levels"]})
                targets = data.get("type_counts") or {"mcq": data["count"]}
                request = PracticeStart(concept_ids=[c.concept_id for c in concepts], difficulties=bands,
                                        source="ai", question_count=sum(targets.values()), request_id=uuid4())
                payload = {"questions": template_questions(concepts, request, kinds=tuple(targets),
                                                           type_targets_override=targets)}
                return self.respond(200, {"choices": [{"message": {"content": json.dumps(payload, ensure_ascii=False)}, "finish_reason": "stop"}]})
            band = re.search(r"- Complete: score (\d+(?:\.\d+)?) to (\d+(?:\.\d+)?)", prompt)
            answer = prompt.split("STUDENT ANSWER (identifiers redacted):\n", 1)[1].split("\n\nReturn JSON:", 1)[0]
            minimum, maximum = map(float, band.groups())
            payload = {"rubric_level": "Complete", "score": round((minimum + maximum) / 2, 2),
                       "confidence": 0.95, "matched_criteria": ["Phân tích phụ thuộc hàm và phân rã"],
                       "missing_concepts": [], "evidence": [answer[:64]],
                       "explanation": "Phản hồi xác định từ provider kiểm thử local.",
                       "feedback": "Bổ sung ví dụ kiểm chứng phép nối không mất mát."}
            self.respond(200, {"choices": [{"message": {"content": json.dumps(payload, ensure_ascii=False)}}]})
        except (ValueError, KeyError, TypeError, StopIteration, IndexError, AttributeError):
            self.respond(400, {"error": "invalid_request"})


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
