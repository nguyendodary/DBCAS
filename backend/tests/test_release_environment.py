"""Real subprocess regression: .env values cannot restore paid AI access."""
import json
import subprocess
import sys

from release_environment import server_environment


def test_child_process_keeps_ai_disabled_despite_dotenv_and_parent_settings(tmp_path, monkeypatch):
    dotenv = tmp_path / ".env"
    dotenv.write_text("LLM_API_KEY=test-only\nLLM_BASE_URL=https://provider.invalid/v1\nLLM_MODEL=test-model\n")
    for name in ("LLM_API_KEY", "LLM_BASE_URL", "LLM_MODEL"):
        monkeypatch.setenv(name, "parent-test-value")
    child = subprocess.run([sys.executable, "-c",
        "import sys,json; from app.config import Settings; s=Settings(_env_file=sys.argv[1]); "
        "print(json.dumps([bool(s.llm_api_key),bool(s.llm_base_url),bool(s.llm_model)]))", str(dotenv)],
        env=server_environment(), capture_output=True, text=True, check=True)
    assert json.loads(child.stdout) == [False, False, False]
