"""Product limits, shared by request schemas, bank sizing and the UI API."""
from math import ceil

MIN_QUESTIONS = 1
DEFAULT_QUESTIONS = 5
# The original balanced practice flow keeps its 13-question contract. Typed
# practice below is additive and intentionally does not change this constant.
LEGACY_MAX_QUESTIONS = 13
MAX_QUESTIONS = LEGACY_MAX_QUESTIONS
QUESTION_TYPES = ("mcq", "sql", "essay")
DIFFICULTY_LEVELS = {"EASY": (1, 2), "MEDIUM": (3,), "HARD": (4, 5)}
CELL_QUOTA = ceil(MAX_QUESTIONS / len(QUESTION_TYPES))

# One source of truth for user-chosen typed practice. A single-type attempt
# chooses one of these caps; a mixed attempt must stay within every per-type
# cap and the total cap.
SINGLE_TYPE_LIMITS = {"mcq": 50, "sql": 5, "essay": 10}
MIXED_LIMITS = {"mcq": 20, "sql": 2, "essay": 3}
MIXED_TOTAL_LIMIT = 25
MAX_SINGLE_TYPE_QUESTIONS = max(SINGLE_TYPE_LIMITS.values())


def difficulty_band(level):
    return next(band for band, levels in DIFFICULTY_LEVELS.items() if level in levels)


def typed_limits():
    return {"single": dict(SINGLE_TYPE_LIMITS),
            "mixed": dict(MIXED_LIMITS),
            "mixed_total": MIXED_TOTAL_LIMIT}


def public_config():
    return {"min": MIN_QUESTIONS, "default": DEFAULT_QUESTIONS, "max": MAX_QUESTIONS,
            "presets": [n for n in (5, 10, 13) if MIN_QUESTIONS <= n <= MAX_QUESTIONS],
            "typed": typed_limits()}
