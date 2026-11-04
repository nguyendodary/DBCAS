from collections import Counter

from app.services.practice_selection import Candidate, Catalog, tier_for, disclosure


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
    plan = catalog.plan([1, 2], ["EASY", "MEDIUM", "HARD"], limit=20, seed="fixed")
    assert plan == catalog.plan([2, 1], ["HARD", "EASY", "MEDIUM"], limit=20, seed="fixed")
    assert len(plan) == 20 and not disclosure(plan, source="bank")
    for counts in (Counter(p.candidate.kind for p in plan), Counter(next(iter(p.candidate.concepts)) for p in plan),
                   Counter(p.candidate.level for p in plan)):
        assert max(counts.values())-min(counts.values()) <= 1


def test_selection_rejects_duplicate_ids_families_prompts_and_invalid_or_wrong_scope_ai():
    candidates = [item(1), item(1), item(2, family=1), item(3, signature="1"), item(4, valid=False),
                  item(5, concept=9, origin="ai"), item(6, level=5, origin="ai"), item(7, "sql"), item(8, "essay")]
    plan = Catalog(candidates).plan([1], ["EASY"], limit=3)
    assert {p.candidate.identity for p in plan} == {3, 7, 8}
    assert len({p.candidate.family for p in plan}) == len({p.candidate.signature for p in plan}) == 3
    assert all(tier_for(p.candidate, {1}, {"EASY"})[0] == 0 for p in plan)
