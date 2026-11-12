"""Product limits, shared by request schemas, bank sizing and the UI API."""
from math import ceil

MIN_QUESTIONS = 1
DEFAULT_QUESTIONS = 5
MAX_QUESTIONS = 20
QUESTION_TYPES = ("mcq", "sql", "essay")
DIFFICULTY_LEVELS = {"EASY": (1, 2), "MEDIUM": (3,), "HARD": (4, 5)}
CELL_QUOTA = ceil(MAX_QUESTIONS / len(QUESTION_TYPES))


def difficulty_band(level):
    return next(band for band, levels in DIFFICULTY_LEVELS.items() if level in levels)


def public_config():
    return {"min": MIN_QUESTIONS, "default": DEFAULT_QUESTIONS, "max": MAX_QUESTIONS,
            "presets": [n for n in (5, 10, 15, 20) if MIN_QUESTIONS <= n <= MAX_QUESTIONS]}
