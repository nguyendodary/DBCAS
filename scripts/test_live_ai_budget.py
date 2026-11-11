"""Offline tests: the live-check budget must fail closed before HTTP."""
import json
from pathlib import Path
import tempfile
import unittest

import httpx
from verify_live_ai import BudgetExhausted, MeteredTransport, run


class LiveBudgetTests(unittest.TestCase):
    def test_sixth_request_cannot_reach_transport(self):
        calls = []
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ledger.json"
            ledger = {"requests": []}
            inner = httpx.MockTransport(lambda request: (calls.append(1) or httpx.Response(200, json={"usage": {"total_tokens": 3}})))
            transport = MeteredTransport(path, ledger, inner)
            transport.check = "evaluator"
            request = httpx.Request("POST", "https://provider.test", json={"messages": [{"content": "synthetic"}]})
            for _ in range(5):
                transport.handle_request(request)
            with self.assertRaises(BudgetExhausted):
                transport.handle_request(request)
            self.assertEqual(len(calls), 5)
            self.assertEqual(len(json.loads(path.read_text())["requests"]), 5)

    def test_no_key_skips_without_creating_a_ledger(self):
        import os
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"LLM_API_KEY": ""}):
            path = Path(directory) / "ledger.json"
            result = run(Path(directory) / "absent.env", path)
            self.assertEqual(result["status"], "skipped_no_key")
            self.assertFalse(path.exists())


if __name__ == "__main__":
    unittest.main()
