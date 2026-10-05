"""Prerequisite Skill Graph service — Task 5.1 (DBCAS-26).

``concept_dependency`` rows form a directed graph over the concept model:
an edge ``(p, c)`` means *concept c requires prerequisite p* — the learner
must reach p's benchmark before studying c. Administrators maintain the
graph as part of the concept model (UC05); the study-guidance pipeline
(Task 5.2) reads it to order weak concepts prerequisite-first.

The documented graph is a DAG. Self-edges are blocked by the table CHECK,
duplicate edges by the composite primary key, and transitive cycles are
rejected here on every write — a CHECK constraint cannot see transitive
edges. All traversal is iterative with visited sets, so even malformed
cyclic data can never recurse forever, and every query returns results in
deterministic order.
"""

from heapq import heapify, heappop, heappush
from typing import Callable, Iterable, Optional

from sqlalchemy.orm import Session

from ..errors import AppError
from ..models import Concept, ConceptDependency
from ..repositories import ConceptGraphRepository
from ..schemas import (
    ConceptGraphEdge,
    ConceptGraphNode,
    ConceptGraphResult,
    ConceptPrerequisitesResult,
    ConceptRef,
)

# An edge is (prerequisite_concept_id, dependent_concept_id).
Edge = tuple[int, int]


def edges_of(rows: Iterable[ConceptDependency]) -> list[Edge]:
    return [(r.prerequisite_concept_id, r.concept_id) for r in rows]


def prerequisite_map(edges: Iterable[Edge]) -> dict[int, set[int]]:
    """concept_id -> its direct prerequisite ids."""
    prereqs: dict[int, set[int]] = {}
    for prereq, dependent in edges:
        prereqs.setdefault(dependent, set()).add(prereq)
    return prereqs


def dependent_map(edges: Iterable[Edge]) -> dict[int, set[int]]:
    """concept_id -> ids of concepts that directly depend on it."""
    dependents: dict[int, set[int]] = {}
    for prereq, dependent in edges:
        dependents.setdefault(prereq, set()).add(dependent)
    return dependents


def _reachable(start: int, adjacency: dict[int, set[int]]) -> set[int]:
    """Iterative reachability — terminates even on cyclic malformed data."""
    seen: set[int] = set()
    stack = list(adjacency.get(start, ()))
    while stack:
        node = stack.pop()
        if node in seen:
            continue
        seen.add(node)
        stack.extend(adjacency.get(node, set()) - seen)
    return seen


def direct_prerequisites(concept_id: int, edges: Iterable[Edge]) -> set[int]:
    return prerequisite_map(edges).get(concept_id, set())


def direct_dependents(concept_id: int, edges: Iterable[Edge]) -> set[int]:
    return dependent_map(edges).get(concept_id, set())


def transitive_prerequisites(
    concept_id: int, edges: Iterable[Edge]
) -> set[int]:
    """Everything the concept transitively requires (excluding itself)."""
    return _reachable(concept_id, prerequisite_map(edges)) - {concept_id}


def transitive_dependents(
    concept_id: int, edges: Iterable[Edge]
) -> set[int]:
    """Everything that transitively requires the concept."""
    return _reachable(concept_id, dependent_map(edges)) - {concept_id}


def would_create_cycle(
    concept_id: int, prerequisite_id: int, edges: Iterable[Edge]
) -> bool:
    """True iff making ``prerequisite_id`` a prerequisite of ``concept_id``
    closes a cycle — i.e. the prerequisite already depends on the concept."""
    if concept_id == prerequisite_id:
        return True
    return concept_id in _reachable(prerequisite_id, prerequisite_map(edges))


def topological_order(
    concept_ids: Iterable[int],
    edges: Iterable[Edge],
    *,
    key: Optional[Callable[[int], tuple]] = None,
) -> list[int]:
    """Deterministic Kahn ordering over the subgraph induced by
    ``concept_ids``: prerequisites before dependents. ``key`` picks among
    ready nodes (default: ascending concept_id). Leftover nodes — only
    possible when the input graph is cyclic — append last, key-sorted, so
    the function still returns a complete deterministic sequence."""
    nodes = set(concept_ids)
    edge_list = list(edges)
    prereq_map = prerequisite_map(edge_list)
    prereqs = {n: prereq_map.get(n, set()) & nodes for n in nodes}
    dependents = dependent_map(edge_list)
    rank = key or (lambda cid: (cid,))
    ready = sorted((rank(n), n) for n, ps in prereqs.items() if not ps)
    heapify(ready)
    order: list[int] = []
    remaining = {n: len(ps) for n, ps in prereqs.items()}
    while ready:
        _, node = heappop(ready)
        order.append(node)
        for dependent in dependents.get(node, set()) & nodes:
            remaining[dependent] -= 1
            if remaining[dependent] == 0:
                heappush(ready, (rank(dependent), dependent))
    if len(order) < len(nodes):
        leftover = nodes - set(order)
        order.extend(n for _, n in sorted((rank(n), n) for n in leftover))
    return order


def _concept_ref(concept: Concept) -> ConceptRef:
    return ConceptRef(
        concept_id=concept.concept_id,
        concept_code=concept.concept_code,
        concept_name=concept.concept_name,
    )


# ---------- admin write path (UC05 — concept model maintenance) ----------


def set_concept_prerequisites(
    db: Session, concept_id: int, prerequisite_ids: list[int]
) -> ConceptPrerequisitesResult:
    """Replace a concept's direct prerequisite set, DAG-checked.

    Rejections follow the API conventions: unknown concept/prerequisite →
    404 (the resource does not exist), malformed payloads (self-edge or
    repeated ids) → 422, and a set that would close a transitive cycle →
    409 state conflict.
    """
    repo = ConceptGraphRepository(db)
    concept = repo.get_concept(concept_id)
    if concept is None:
        raise AppError(404, "concept_not_found", "Concept not found")

    if len(set(prerequisite_ids)) != len(prerequisite_ids):
        raise AppError(
            422,
            "duplicate_prerequisite",
            "prerequisite_concept_ids must not contain duplicates",
        )
    if concept_id in prerequisite_ids:
        raise AppError(
            422,
            "self_dependency",
            "A concept cannot be its own prerequisite",
        )

    known = {c.concept_id for c in repo.get_concepts(set(prerequisite_ids))}
    missing = [pid for pid in prerequisite_ids if pid not in known]
    if missing:
        raise AppError(
            404,
            "concept_not_found",
            "Prerequisite concept not found",
            [{"concept_id": pid} for pid in missing],
        )

    edges = edges_of(repo.all_edges())
    # Only edges that are actually new can introduce a cycle.
    existing = direct_prerequisites(concept_id, edges)
    for pid in prerequisite_ids:
        if pid not in existing and would_create_cycle(concept_id, pid, edges):
            raise AppError(
                409,
                "dependency_cycle",
                "This prerequisite would create a dependency cycle",
                [{"concept_id": concept_id, "prerequisite_concept_id": pid}],
            )

    repo.replace_prerequisites(concept_id, prerequisite_ids)
    db.commit()

    concepts = {
        c.concept_id: c for c in repo.get_concepts(set(prerequisite_ids))
    }
    return ConceptPrerequisitesResult(
        concept_id=concept.concept_id,
        concept_code=concept.concept_code,
        concept_name=concept.concept_name,
        prerequisites=[_concept_ref(concepts[pid]) for pid in prerequisite_ids],
    )


# ---------- read path ----------


def concept_graph(db: Session) -> ConceptGraphResult:
    """The full prerequisite graph: every concept as a node (with its direct
    prerequisite ids) plus the raw edge list for client-side rendering."""
    repo = ConceptGraphRepository(db)
    edges = edges_of(repo.all_edges())
    prereqs = prerequisite_map(edges)
    nodes = [
        ConceptGraphNode(
            concept_id=c.concept_id,
            concept_code=c.concept_code,
            concept_name=c.concept_name,
            subject_area=c.subject_area,
            prerequisites=sorted(prereqs.get(c.concept_id, ())),
        )
        for c in repo.list_concepts()
    ]
    return ConceptGraphResult(
        nodes=nodes,
        edges=[
            ConceptGraphEdge(prerequisite_concept_id=p, concept_id=c)
            for p, c in edges
        ],
    )
