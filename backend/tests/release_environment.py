"""Explicit child environment: Windows drops empty values on implicit inherit."""
import os


def server_environment():
    environment = os.environ.copy()
    environment.update(LLM_API_KEY="", LLM_BASE_URL="", LLM_MODEL="")
    return environment
