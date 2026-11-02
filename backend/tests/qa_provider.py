"""Local browser-QA HTTP provider. No real credentials, outbound calls or prompt logs."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import re
import threading
import time

LOCK = threading.Lock()
RELEASE = threading.Event()
RELEASE.set()
STATE = {"delay_seconds": 20, "failure": False, "hold": False, "calls": 0}


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
        try:
            size = int(self.headers.get("Content-Length", 0))
            if not 0 < size <= 262144:
                raise ValueError("invalid_size")
            body = json.loads(self.rfile.read(size))
            if self.path == "/control":
                delay = body.get("delay_seconds", 20)
                failure = body.get("failure", False)
                hold = body.get("hold", False)
                if isinstance(delay, bool) or not isinstance(delay, (int, float)) or not 0 <= delay <= 120 or not isinstance(failure, bool) or not isinstance(hold, bool):
                    raise ValueError("invalid_control")
                with LOCK:
                    STATE.update(delay_seconds=delay, failure=failure, hold=hold)
                    RELEASE.clear() if hold else RELEASE.set()
                    result = dict(STATE)
                return self.respond(200, result)
            if self.path != "/v1/chat/completions":
                return self.respond(404, {"error": "not_found"})
            if body.get("response_format", {}).get("json_schema", {}).get("name") != "essay_grade":
                return self.respond(503, {"error": "only_essay_grading_is_simulated"})
            prompt = next(m["content"] for m in body["messages"] if m["role"] == "user")
            band = re.search(r"- Complete: score (\d+(?:\.\d+)?) to (\d+(?:\.\d+)?)", prompt)
            answer = prompt.split("STUDENT ANSWER (identifiers redacted):\n", 1)[1].split("\n\nReturn JSON:", 1)[0]
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
