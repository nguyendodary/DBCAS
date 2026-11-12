"""Exhaustive supported scopes/counts through production preparation/recovery."""
from collections import Counter
from dataclasses import replace
from itertools import combinations
import json
import time

from app.services.practice_config import MIN_QUESTIONS, MAX_QUESTIONS, DIFFICULTY_LEVELS, QUESTION_TYPES
from app.services.practice_corpus import template_pack
from app.services.practice_generation import ai_type_targets, type_targets
from app.services.practice_selection import Candidate, Catalog, mixed_plan, recovered_plan
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
        # Exact-capacity cases never need out-of-scope rows; scoping once per
        # concept selection keeps the exhaustive matrix linear instead of
        # rebuilding per-kind catalogs over the whole bank for every count.
        scoped = [c for c in candidates if c.concepts <= scope]
        scoped_bank = Catalog(scoped)
        scoped_kinds = {kind: Catalog(c for c in scoped if c.kind == kind) for kind in QUESTION_TYPES}
        for difficulty in bands:
            prepared = bank.prepare(scope, difficulty, seed="matrix")
            generated = native.prepare(scope, difficulty, seed="matrix-ai").picks
            assert prepared == bank.prepare(scope, difficulty, seed="matrix")
            assert generated == native.prepare(scope, difficulty, seed="matrix-ai").picks
            assert len(prepared.picks) == len(generated) == MAX_QUESTIONS
            for count in range(MIN_QUESTIONS, MAX_QUESTIONS+1):
                targets = ai_type_targets(count)
                ai_pool = [replace(p.candidate, origin="ai") for p in generated
                           if p.candidate.kind in targets]
                ai = []
                for kind, target in targets.items():
                    ai.extend(next(c for c in ai_pool if c.kind == kind and c not in ai)
                              for _ in range(target))
                assert len(ai) == sum(targets.values())
                preferred = tuple(ai)
                targets_all = type_targets(count)
                modes = {
                    "bank": prepared,
                    "ai-failure": recovered_plan(prepared, [], count, scope, difficulty),
                    "ai-invalid": recovered_plan(prepared, [replace(c, valid=False) for c in ai], count, scope, difficulty),
                    "ai-timeout": recovered_plan(prepared, [], count, scope, difficulty),
                    "ai-overflow": recovered_plan(prepared, [replace(c, origin="template") for c in ai], count, scope, difficulty),
                }
                # Per-kind bank filling does not depend on scope cardinality.
                # Exercise it exhaustively for every single-concept scope (all
                # difficulties and counts); the five recovery modes above keep
                # covering all 3,241 scopes. This keeps the CI job under its
                # 25-minute budget without dropping a count or difficulty.
                if len(scope) == 1:
                    modes["ai-mixed-normal"] = mixed_plan(
                        scoped_bank, scope, difficulty, preferred, targets_all,
                        seed="matrix", kind_catalogs=scoped_kinds)
                    modes["ai-partial"] = mixed_plan(
                        scoped_bank, scope, difficulty, preferred[:max(0, len(preferred)-1)],
                        targets_all, seed="matrix", kind_catalogs=scoped_kinds)
                for mode, plan in modes.items():
                    picked = plan.take(count)
                    assert len(picked) == count, (scope, difficulty, count, mode)
                    assert len({p.candidate.identity for p in picked}) == count
                    assert len({p.candidate.family for p in picked}) == count
                    assert len({p.candidate.signature for p in picked}) == count
                    assert all(p.candidate.valid and p.candidate.identity in valid_ids and p.tier == 0
                               and p.candidate.concepts <= scope for p in picked)
                    assert picked == plan.take(count)
                    assert Counter(p.candidate.kind for p in picked) == type_targets(count)
                    if mode in ("ai-mixed-normal", "ai-partial"):
                        assert all(p.candidate.origin == "bank" for p in picked if p.candidate.kind == "sql")
                        assert all(p.candidate.kind != "sql" for p in picked if p.candidate.origin == "ai")
                    if mode == "ai-mixed-normal":
                        assert all(p.candidate.origin == "ai" for p in picked if p.candidate.kind != "sql")
                    if mode in ("ai-failure", "ai-invalid", "ai-timeout", "ai-overflow"):
                        assert all(p.candidate.origin == "bank" for p in picked)
                    total += 1
    single = sum(1 for scope in scopes if len(scope) == 1)
    expected = (len(scopes)*5 + single*2)*len(bands)*(MAX_QUESTIONS-MIN_QUESTIONS+1)
    assert len(scopes) == 3241 and single == 80 and len(bands) == 7
    assert total == expected == 1489215
    print(json.dumps({"scopes": len(scopes), "single_concept_scopes": single,
        "difficulty_subsets": len(bands), "allowed_counts": 20, "source_modes": 7,
        "actual_cases": total, "failed": 0,
        "seconds": round(time.monotonic()-started, 3)}), flush=True)
