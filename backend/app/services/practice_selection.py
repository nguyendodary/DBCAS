"""Pure deterministic selection; the same engine serves bank and AI recovery."""
from collections import Counter, defaultdict, deque
from dataclasses import dataclass
from hashlib import sha256
from math import ceil

from ..errors import AppError
from .practice_config import MAX_QUESTIONS, MIN_QUESTIONS, QUESTION_TYPES, difficulty_band


@dataclass(frozen=True)
class Candidate:
    identity: object
    kind: str
    level: int
    concepts: frozenset
    family: object
    signature: str
    value: object
    origin: str = "bank"
    valid: bool = True


@dataclass(frozen=True)
class Pick:
    candidate: Candidate
    tier: int
    distance: int


@dataclass(frozen=True)
class PreparedPlan:
    picks: tuple

    def take(self, count):
        if type(count) is not int or not MIN_QUESTIONS <= count <= MAX_QUESTIONS:
            raise ValueError("Invalid question count")
        return list(self.picks[:count])


def complete_batch(generated, count, concepts, bands):
    if (len(generated) != count or not all(c.valid and c.origin == "ai" and c.concepts and c.concepts <= set(concepts) for c in generated)
            or any(len({getattr(c, field) for c in generated}) != count for field in ("identity", "family", "signature"))):
        return False
    kinds = Counter(c.kind for c in generated)
    if set(kinds)-set(QUESTION_TYPES) or max(kinds[k] for k in QUESTION_TYPES)-min(kinds[k] for k in QUESTION_TYPES) > 1:
        return False
    if any(difficulty_band(c.level) not in bands for c in generated):
        return False
    band_counts = Counter(difficulty_band(c.level) for c in generated)
    concept_counts = Counter(cid for c in generated for cid in c.concepts)
    return (all(band_counts[b] <= ceil(count/len(bands)) for b in bands)
            and all(concept_counts[cid] <= ceil(count/len(concepts)) for cid in concepts))


def recovered_plan(bank_plan, generated, requested_count, concepts, bands):
    """A complete validated provider batch is served intact; failures use bank.

    Partial-batch mixing is prepared with Catalog in the service adapter so
    duplicate families/prompts and balances receive the same checks.
    """
    if complete_batch(generated, requested_count, concepts, bands):
        return PreparedPlan(tuple(Pick(c, 0, 0) for c in generated))
    return bank_plan


def tier_for(candidate, concepts, bands, related=frozenset()):
    actual = difficulty_band(candidate.level)
    order = {"EASY": 0, "MEDIUM": 1, "HARD": 2}
    distance = min(abs(order[actual]-order[band]) for band in bands)
    if candidate.concepts <= concepts:
        return (0 if distance == 0 else 1), distance
    if candidate.concepts <= concepts | related and candidate.concepts & related:
        return 2, distance
    return 3, distance


class Catalog:
    def __init__(self, candidates):
        self.candidates = tuple(c for c in candidates if c.valid and c.concepts and c.kind in QUESTION_TYPES)
        self.by_concept = defaultdict(list)
        for candidate in self.candidates:
            for concept in candidate.concepts:
                self.by_concept[concept].append(candidate)

    def prepare(self, concepts, bands, *, related=frozenset(), seed="0", preferred=(), blocked=()):
        return PreparedPlan(tuple(self._plan(concepts, bands, related=related, seed=seed, preferred=preferred,
                                             blocked=blocked)))

    def plan(self, concepts, bands, *, related=frozenset(), seed="0", limit=MAX_QUESTIONS, preferred=(), blocked=()):
        return self.prepare(concepts, bands, related=related, seed=seed, preferred=preferred,
                            blocked=blocked).take(limit)

    def _plan(self, concepts, bands, *, related=frozenset(), seed="0", limit=MAX_QUESTIONS, preferred=(), blocked=(),
              _widen=False):
        concepts, bands, related = frozenset(concepts), frozenset(bands), frozenset(related)
        if not MIN_QUESTIONS <= limit <= MAX_QUESTIONS or not concepts or not bands:
            raise ValueError("Invalid practice selection")
        # Most scopes have sufficient exact capacity. Avoid scanning unrelated
        # records on the hot path; widening remains ordered if capacity is low.
        scoped = {c.identity: c for concept in concepts for c in self.by_concept.get(concept, ())}
        exact = [c for c in scoped.values() if c.origin != "template" and tier_for(c, concepts, bands)[0] == 0]
        pool = list(scoped.values()) if len(exact) >= limit and not _widen else list(self.candidates)
        pool = [c for c in preferred if c.valid] + pool
        blocked_ids = {c.identity for c in blocked}
        blocked_families = {c.family for c in blocked}
        blocked_prompts = {c.signature for c in blocked}
        stages = defaultdict(lambda: defaultdict(list))
        seed_order = lambda value: sha256(f"{seed}:{value}".encode()).digest()
        concept_order = sorted(concepts, key=seed_order)
        concept_position = {concept: index for index, concept in enumerate(concept_order)}
        for c in pool:
            if (not c.valid or not c.concepts or c.kind not in QUESTION_TYPES
                    or c.identity in blocked_ids or c.family in blocked_families or c.signature in blocked_prompts):
                continue
            tier, distance = tier_for(c, concepts, bands, related)
            # Wrong-scope AI output is never legitimized by bank widening.
            if c.origin == "ai" and tier:
                continue
            owner = min(c.concepts & concepts, key=lambda cid: concept_position[cid]) if c.concepts & concepts else min(c.concepts)
            stages[c.origin == "template", tier, distance][c.kind, owner, difficulty_band(c.level)].append(c)
        chosen, used_ids, used_families, used_prompts = [], set(), set(), set()
        kind_counts, concept_counts, band_counts = Counter(), Counter(), Counter()
        for (_, tier, distance), grouped in sorted(stages.items()):
            buckets = {key: deque(sorted(values, key=lambda c: (c.origin != "ai", c.origin == "template", seed_order(c.identity))))
                       for key, values in grouped.items()}
            while len(chosen) < limit:
                available = []
                for key, bucket in buckets.items():
                    while bucket and (bucket[0].identity in used_ids or bucket[0].family in used_families or bucket[0].signature in used_prompts):
                        bucket.popleft()
                    if bucket:
                        kind, concept, band = key
                        score = (kind_counts[kind], concept_counts[concept], band_counts[band],
                                 bucket[0].origin != "ai", QUESTION_TYPES.index(kind), concept_position.get(concept, len(concepts)), band)
                        available.append((score, key))
                if not available:
                    break
                _, key = min(available)
                c = buckets[key].popleft()
                chosen.append(Pick(c, tier, distance))
                used_ids.add(c.identity); used_families.add(c.family); used_prompts.add(c.signature)
                kind_counts[c.kind] += 1
                for concept in c.concepts & concepts:
                    concept_counts[concept] += 1
                band_counts[difficulty_band(c.level)] += 1
            if len(chosen) == limit:
                break
        if len(chosen) < limit and not _widen:
            return self._plan(concepts, bands, related=related, seed=seed, limit=limit, preferred=preferred,
                              blocked=blocked, _widen=True)
        return chosen


def mixed_plan(catalog, concepts, bands, preferred, targets, *, related=frozenset(), seed="0", kind_catalogs=None):
    """Validated AI picks first, then exact per-kind bank/template shortfalls."""
    picks, counts = [], Counter()
    for candidate in preferred:
        if candidate.valid and counts[candidate.kind] < targets.get(candidate.kind, 0):
            counts[candidate.kind] += 1
            picks.append(Pick(candidate, 0, 0))
    blocked = tuple(pick.candidate for pick in picks)
    available = kind_catalogs or {}
    for kind in QUESTION_TYPES:
        need = targets.get(kind, 0) - counts[kind]
        if need <= 0:
            continue
        kind_catalog = available.get(kind) or Catalog(c for c in catalog.candidates if c.kind == kind)
        chosen = kind_catalog.plan(concepts, bands, related=related, seed=seed,
                                   limit=max(MIN_QUESTIONS, need), blocked=blocked)[:need]
        picks.extend(chosen)
        blocked += tuple(pick.candidate for pick in chosen)
    return PreparedPlan(tuple(picks))


def select_bank_mix(candidates, concepts, band, targets, *, seed="0"):
    """Select an exact type mix from one difficulty band.

    This is intentionally separate from ``Catalog``: the legacy practice flow
    may widen concepts/bands to reach its exact count, while typed practice
    must fail closed rather than silently change the learner's band.
    """
    concepts = frozenset(concepts)
    required = {kind: int(count) for kind, count in targets.items() if count}
    if (not required or any(kind not in QUESTION_TYPES or count < 1
                           for kind, count in required.items())):
        raise ValueError("Invalid typed practice targets")

    by_kind = defaultdict(list)
    candidate_rows = Counter()
    for candidate in candidates:
        if (not candidate.valid or candidate.origin != "bank"
                or candidate.kind not in required
                or not candidate.concepts
                or not (candidate.concepts & concepts)
                or difficulty_band(candidate.level) != band):
            continue
        by_kind[candidate.kind].append(candidate)
        candidate_rows[candidate.kind] += 1

    def available(kind):
        families, signatures = set(), set()
        for candidate in by_kind.get(kind, ()):
            family = candidate.family if candidate.family is not None else candidate.identity
            if family in families or candidate.signature in signatures:
                continue
            families.add(family)
            signatures.add(candidate.signature)
        return len(families)

    available_by_kind = {kind: available(kind) for kind in required}
    shortage = {kind: required[kind] - available_by_kind[kind]
                for kind in required if available_by_kind[kind] < required[kind]}
    if shortage:
        raise AppError(
            422,
            "insufficient_question_pool",
            f"Not enough validated bank questions at {band} for the requested mix",
            details=[{
                "band": band,
                "requested_by_type": required,
                "available_by_type": available_by_kind,
                "candidate_rows_by_type": dict(candidate_rows),
                "shortage_by_type": shortage,
                "concept_ids": sorted(concepts),
            }],
        )

    picks, used_ids, used_families, used_signatures = [], set(), set(), set()
    for kind in QUESTION_TYPES:
        need = required.get(kind, 0)
        if not need:
            continue
        ordered = sorted(
            by_kind.get(kind, ()),
            key=lambda candidate: sha256(f"{seed}:{candidate.identity}".encode()).digest(),
        )
        for candidate in ordered:
            if need == 0:
                break
            family = candidate.family if candidate.family is not None else candidate.identity
            if (candidate.identity in used_ids or family in used_families
                    or candidate.signature in used_signatures):
                continue
            picks.append(Pick(candidate, 0, 0))
            used_ids.add(candidate.identity)
            used_families.add(family)
            used_signatures.add(candidate.signature)
            need -= 1
        if need:
            selected_by_kind = Counter(pick.candidate.kind for pick in picks)
            raise AppError(
                422,
                "insufficient_question_pool",
                f"Not enough distinct validated bank questions at {band} for the requested mix",
                details=[{
                    "band": band,
                    "requested_by_type": required,
                    "selected_by_type": dict(selected_by_kind),
                    "concept_ids": sorted(concepts),
                }],
            )

    picks.sort(key=lambda pick: sha256(
        f"{seed}:{pick.candidate.identity}".encode()).digest())
    return picks


def disclosure(picks, *, source):
    widened = any(p.tier for p in picks)
    fallback = source == "ai" and any(p.candidate.origin != "ai" for p in picks)
    template = any(p.candidate.origin == "template" for p in picks)
    bank_sql = (source == "ai" and any(p.candidate.origin == "ai" for p in picks)
                and any(p.candidate.origin == "bank" and p.candidate.kind == "sql" for p in picks)
                and all(p.candidate.origin == "ai" for p in picks if p.candidate.kind != "sql"))
    if widened:
        return ("Đã dùng câu dự phòng và mở rộng độ khó hoặc khái niệm để đủ số câu bạn chọn." if fallback else
                "Đã mở rộng độ khó hoặc khái niệm để đủ số câu bạn chọn.")
    if template:
        return "Đã bổ sung câu hỏi từ mẫu đã kiểm chứng để đủ số câu bạn chọn."
    if bank_sql:
        return "Đã kết hợp câu SQL đã kiểm chứng từ ngân hàng với câu MCQ/tự luận do AI tạo."
    if fallback:
        return "Đã bổ sung câu hỏi đã kiểm chứng từ ngân hàng để đủ số câu bạn chọn."
    return None
