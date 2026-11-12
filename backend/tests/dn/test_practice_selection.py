from collections import Counter

from app.services.practice_generation import ai_type_targets, type_targets
from app.services.practice_selection import Candidate, Catalog, Pick, tier_for, disclosure, mixed_plan


def item(i, kind="mcq", concept=1, level=2, **kwargs):
    return Candidate(i, kind, level, frozenset({concept}), kwargs.get("family", i), kwargs.get("signature", str(i)), i,
                     kwargs.get("origin", "bank"), kwargs.get("valid", True))


def test_selection_widens_in_required_order_and_preserves_nearest_difficulty():
    pool = [item(1), item(2, level=3), item(3, level=5), item(4, concept=2), item(5, concept=3)]
    plan = Catalog(pool).plan([1], ["EASY"], related={2}, limit=5)
    assert [p.candidate.identity for p in plan] == [1, 2, 3, 4, 5]
    assert [(p.tier, p.distance) for p in plan] == [(0, 0), (1, 1), (1, 2), (2, 0), (3, 0)]
    assert disclosure(plan, source="bank")


def test_selection_balances_types_concepts_and_difficulties_and_is_reproducible():
    pool = [item(f"{c}-{level}-{kind}-{n}", kind, c, level) for c in (1, 2) for level in (2, 3, 5)
            for kind in ("mcq", "sql", "essay") for n in range(7)]
    catalog = Catalog(pool)
    plan = catalog.plan([1, 2], ["EASY", "MEDIUM", "HARD"], limit=13, seed="fixed")
    assert plan == catalog.plan([2, 1], ["HARD", "EASY", "MEDIUM"], limit=13, seed="fixed")
    assert len(plan) == 13 and not disclosure(plan, source="bank")
    for counts in (Counter(p.candidate.kind for p in plan), Counter(next(iter(p.candidate.concepts)) for p in plan),
                   Counter(p.candidate.level for p in plan)):
        assert max(counts.values())-min(counts.values()) <= 1


def test_bank_sql_mix_gets_one_notice_and_ai_only_does_not():
    ai_only = [Pick(item("ai-mcq", origin="ai"), 0, 0)]
    assert disclosure(ai_only, source="ai") is None
    mixed = ai_only + [Pick(item("ai-essay", "essay", origin="ai"), 0, 0),
                       Pick(item("bank-sql", "sql"), 0, 0)]
    notice = disclosure(mixed, source="ai")
    assert notice and notice.count("SQL") == 1 and "ngân hàng" in notice
    partial = [Pick(item("ai-mcq", origin="ai"), 0, 0),
               Pick(item("bank-essay", "essay"), 0, 0),
               Pick(item("bank-sql", "sql"), 0, 0)]
    fallback = disclosure(partial, source="ai")
    assert fallback and "SQL" not in fallback and "ngân hàng" in fallback


def test_type_targets_omit_unused_kinds_so_they_match_exact_counters():
    assert type_targets(1) == {"mcq": 1}
    assert type_targets(2) == {"mcq": 1, "sql": 1}
    assert ai_type_targets(2) == {"mcq": 1}
    assert sum(type_targets(13).values()) == 13


def test_ai_mix_keeps_every_validated_ai_pick_and_fills_only_exact_bank_sql():
    bank = [item("bank-mcq", "mcq"), item("bank-sql", "sql"), item("bank-sql-2", "sql", level=3),
            item("bank-essay", "essay", signature="shared prompt")]
    preferred = [item("ai-mcq", "mcq", origin="ai"),
                 item("ai-essay", "essay", signature="shared prompt", origin="ai")]
    picked = mixed_plan(Catalog(bank), {1}, {"EASY"}, preferred,
                        {"mcq": 1, "sql": 1, "essay": 1}, seed="mix").picks
    assert [p.candidate.identity for p in picked] == ["ai-mcq", "ai-essay", "bank-sql"]
    assert [p.candidate.kind for p in picked] == ["mcq", "essay", "sql"]
    assert [p.candidate.origin for p in picked] == ["ai", "ai", "bank"]
    assert len({p.candidate.family for p in picked}) == len({p.candidate.signature for p in picked}) == 3


def test_ai_mix_fills_missing_non_sql_from_bank_but_sql_is_never_ai():
    bank = [item("bank-sql", "sql"), item("bank-essay", "essay")]
    preferred = [item("ai-mcq", "mcq", origin="ai")]
    picked = mixed_plan(Catalog(bank), {1}, {"EASY"}, preferred,
                        {"mcq": 1, "sql": 1, "essay": 1}, seed="partial").picks
    assert Counter(p.candidate.kind for p in picked) == Counter({"mcq": 1, "sql": 1, "essay": 1})
    assert next(p.candidate.origin for p in picked if p.candidate.kind == "sql") == "bank"
    assert next(p.candidate.origin for p in picked if p.candidate.kind == "mcq") == "ai"


def test_selection_rejects_duplicate_ids_families_prompts_and_invalid_or_wrong_scope_ai():
    candidates = [item(1), item(1), item(2, family=1), item(3, signature="1"), item(4, valid=False),
                  item(5, concept=9, origin="ai"), item(6, level=5, origin="ai"), item(7, "sql"), item(8, "essay")]
    plan = Catalog(candidates).plan([1], ["EASY"], limit=3)
    assert {p.candidate.identity for p in plan} == {3, 7, 8}
    assert len({p.candidate.family for p in plan}) == len({p.candidate.signature for p in plan}) == 3
    assert all(tier_for(p.candidate, {1}, {"EASY"})[0] == 0 for p in plan)
