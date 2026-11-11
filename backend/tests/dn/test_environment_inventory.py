"""Configuration added in code must remain discoverable in the example."""
import importlib.util
from pathlib import Path


def test_every_public_configuration_name_is_documented():
    path = Path(__file__).resolve().parents[3] / "scripts/check_environment.py"
    spec = importlib.util.spec_from_file_location("environment_inventory", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    missing, backend_count, frontend_count = module.missing_names()
    assert backend_count > 0 and frontend_count > 0
    assert missing == [], f"Add these names to .env.example: {missing}"
