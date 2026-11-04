"""Exhaustive supported scopes/counts through production preparation/recovery."""
from dataclasses import replace
from itertools import combinations
import json
import time

from app.services.practice_config import MIN_QUESTIONS, MAX_QUESTIONS, DIFFICULTY_LEVELS
from app.services.practice_corpus import template_pack
from app.services.practice_selection import Candidate, Catalog, recovered_plan
from app.services.question_validator import bank_problems, fingerprint
from app.validate_bank import load_corpus


def test_exact_count_exhaustive_concept_difficulty_count_source_matrix():
    started = time.monotonic()
    packs, translations = load_corpus()
    assert bank_problems(packs, translations) == {}
    codes = sorted({c["concept_code"] for pack in packs for c in pack["concepts"]})
    ids = {code: index+1 for index, code in enumerate(codes)}
    questions = [q for pack in packs for q in pack["questions"] if q.get("status") != "retired"]
    candidates = [Candidate(q["key"], q["question_type"], q["difficulty_level"],
        frozenset(ids[c] for c in q["concept_codes"]), q["key"], fingerprint(q["prompt"]), q) for q in questions]
    valid_ids = {c.identity for c in candidates}
    bank = Catalog(candidates)
    native_keys = {q["key"] for q in template_pack()["questions"]}
    native = Catalog(c for c in candidates if c.identity in native_keys)
    scopes = [*combinations(ids.values(), 1), *combinations(ids.values(), 2), tuple(ids.values())]
    bands = [subset for n in (1, 2, 3) for subset in combinations(DIFFICULTY_LEVELS, n)]
    total = 0
    for scope in scopes:
        scope = frozenset(scope)
        for difficulty in bands:
            prepared = bank.prepare(scope, difficulty, seed="matrix")
            generated = native.prepare(scope, difficulty, seed="matrix-ai").picks
            assert prepared == bank.prepare(scope, difficulty, seed="matrix")
            assert generated == native.prepare(scope, difficulty, seed="matrix-ai").picks
            assert len(prepared.picks) == len(generated) == MAX_QUESTIONS
            for count in range(MIN_QUESTIONS, MAX_QUESTIONS+1):
                ai = [replace(p.candidate, origin="ai") for p in generated[:count]]
                modes = {
                    "bank": prepared,
                    "ai-normal": recovered_plan(prepared, ai, count, scope, difficulty),
                    "ai-failure": recovered_plan(prepared, [], count, scope, difficulty),
                    "ai-invalid": recovered_plan(prepared, [replace(c, valid=False) for c in ai], count, scope, difficulty),
                    "ai-timeout": recovered_plan(prepared, [], count, scope, difficulty),
                }
                for mode, plan in modes.items():
                    picked = plan.take(count)
                    assert len(picked) == count, (scope, difficulty, count, mode)
                    assert len({p.candidate.identity for p in picked}) == count
                    assert len({p.candidate.family for p in picked}) == count
                    assert len({p.candidate.signature for p in picked}) == count
                    assert all(p.candidate.valid and p.candidate.identity in valid_ids and p.tier == 0
                               and p.candidate.concepts <= scope for p in picked)
                    assert picked == plan.take(count)
                    if mode == "ai-normal":
                        assert all(p.candidate.origin == "ai" for p in picked)
                    total += 1
    expected = len(scopes)*len(bands)*(MAX_QUESTIONS-MIN_QUESTIONS+1)*5
    assert len(scopes) == 3241 and len(bands) == 7
    assert total == expected == 2268700
    print(json.dumps({"scopes": len(scopes), "difficulty_subsets": len(bands), "allowed_counts": 20,
        "source_modes": 5, "actual_cases": total, "failed": 0, "seconds": round(time.monotonic()-started, 3)}), flush=True)
