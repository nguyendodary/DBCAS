"""Canonical four-band rubric validation at the database's cent precision."""
from decimal import Decimal, InvalidOperation

KNOWN_LEVELS = ("Incomplete", "Partial", "Mostly Complete", "Complete")


def rubric_problems(rubrics, points) -> list[str]:
    try:
        points = Decimal(str(points))
        if not points.is_finite() or points <= 0:
            raise ValueError()
        rows = []
        for row in rubrics:
            get = row.get if isinstance(row, dict) else lambda k: getattr(row, k, None)
            low, high = Decimal(str(get("min_score"))), Decimal(str(get("max_score")))
            name, criteria = get("level_name"), get("criteria")
            if not low.is_finite() or not high.is_finite() or low != low.quantize(Decimal("0.01")) or high != high.quantize(Decimal("0.01")):
                raise ValueError()
            if not isinstance(criteria, str) or not criteria.strip() or not 0 <= low <= high <= points:
                raise ValueError()
            rows.append((low, high, name))
        rows.sort()
        if len(rows) != 4 or tuple(r[2] for r in rows) != KNOWN_LEVELS:
            return ["exactly four canonical rubric levels in increasing score order are required"]
        if rows[0][0] != 0 or rows[-1][1] != points or any(rows[i+1][0] != rows[i][1]+Decimal("0.01") for i in range(3)):
            return ["rubric bands must cover zero through question points without overlap or missing cent values"]
        return []
    except (InvalidOperation, ValueError, TypeError, AttributeError):
        return ["rubric scores must be finite cent-precision values within question points, with nonempty criteria"]
