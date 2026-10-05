"""Prerequisite skill graph tests — Task 5.1 (DBCAS-26).

``concept_dependency`` edges form a directed acyclic graph over the concept
model: edge (p, c) means "c requires prerequisite p". The service enforces
the documented DAG rules — no self-edges, no duplicate edges, no transitive
cycles — and every traversal is iterative and deterministic, so malformed
cyclic data can never hang the pipeline.
"""

import pytest
from sqlalchemy.exc import IntegrityError

from app.errors import AppError
from app.models import (
    Account,
    AccountRole,
    Concept,
    ConceptDependency,
    Role,
    UserProfile,
)
from app.security import hash_password
from app.services import concept_graph_service as graph


# ---------- fixture helpers ----------


def _make_learner(db, email="learner@test.dev", name="Learner One"):
    account = Account(
        email=email, password_hash=hash_password("Secret123!"), status="active"
    )
    account.profile = UserProfile(full_name=name)
    role = db.query(Role).filter_by(role_name="Learner").one()
    db.add(account)
    db.flush()
    db.add(AccountRole(account_id=account.account_id, role_id=role.role_id))
    db.commit()
    return account


def _make_admin(db, email="admin@test.dev"):
    account = Account(
        email=email, password_hash=hash_password("Admin123!"), status="active"
    )
    account.profile = UserProfile(full_name="Admin")
    role = db.query(Role).filter_by(role_name="Administrator").one()
    db.add(account)
    db.flush()
    db.add(AccountRole(account_id=account.account_id, role_id=role.role_id))
    db.commit()
    return account


def _make_concept(db, code, name=None):
    concept = Concept(
        concept_code=code,
        concept_name=name or code,
        subject_area="SQL Querying",
        difficulty_level=2,
    )
    db.add(concept)
    db.flush()
    return concept


def _edge(db, concept, prerequisite):
    db.add(
        ConceptDependency(
            concept_id=concept.concept_id,
            prerequisite_concept_id=prerequisite.concept_id,
        )
    )
    db.flush()


def _all_edges(db):
    return graph.edges_of(graph.ConceptGraphRepository(db).all_edges())


def _login(client, email, password):
    return client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    ).json()["access_token"]


# ---------- pure graph behaviour ----------


class TestGraphQueries:
    def test_no_prerequisites(self, db_session):
        c = _make_concept(db_session, "SQL-SELECT")
        db_session.commit()
        edges = _all_edges(db_session)
        assert graph.direct_prerequisites(c.concept_id, edges) == set()
        assert graph.transitive_prerequisites(c.concept_id, edges) == set()
        assert graph.direct_dependents(c.concept_id, edges) == set()
        assert graph.transitive_dependents(c.concept_id, edges) == set()

    def test_one_prerequisite(self, db_session):
        base = _make_concept(db_session, "SQL-SELECT")
        join = _make_concept(db_session, "SQL-JOIN")
        _edge(db_session, join, base)
        db_session.commit()
        edges = _all_edges(db_session)
        assert graph.direct_prerequisites(join.concept_id, edges) == {
            base.concept_id
        }
        assert graph.direct_dependents(base.concept_id, edges) == {
            join.concept_id
        }

    def test_multiple_prerequisites(self, db_session):
        a = _make_concept(db_session, "C-A")
        b = _make_concept(db_session, "C-B")
        c = _make_concept(db_session, "C-C")
        _edge(db_session, c, a)
        _edge(db_session, c, b)
        db_session.commit()
        assert graph.direct_prerequisites(c.concept_id, _all_edges(db_session)) == {
            a.concept_id,
            b.concept_id,
        }

    def test_one_prerequisite_many_dependents(self, db_session):
        base = _make_concept(db_session, "SQL-SELECT")
        join = _make_concept(db_session, "SQL-JOIN")
        group = _make_concept(db_session, "SQL-GROUPBY")
        _edge(db_session, join, base)
        _edge(db_session, group, base)
        db_session.commit()
        assert graph.direct_dependents(base.concept_id, _all_edges(db_session)) == {
            join.concept_id,
            group.concept_id,
        }

    def test_multi_level_chain_transitive(self, db_session):
        """SELECT <- JOIN <- SUBQUERY <- WINDOW: transitive queries cross
        every level of the chain."""
        select_ = _make_concept(db_session, "SQL-SELECT")
        join = _make_concept(db_session, "SQL-JOIN")
        sub = _make_concept(db_session, "SQL-SUBQUERY")
        window = _make_concept(db_session, "SQL-WINDOW")
        _edge(db_session, join, select_)
        _edge(db_session, sub, join)
        _edge(db_session, window, sub)
        db_session.commit()
        edges = _all_edges(db_session)

        assert graph.direct_prerequisites(window.concept_id, edges) == {
            sub.concept_id
        }
        assert graph.transitive_prerequisites(window.concept_id, edges) == {
            sub.concept_id,
            join.concept_id,
            select_.concept_id,
        }
        assert graph.transitive_dependents(select_.concept_id, edges) == {
            join.concept_id,
            sub.concept_id,
            window.concept_id,
        }

    def test_missing_node_queries_empty(self, db_session):
        edges = _all_edges(db_session)
        assert graph.direct_prerequisites(999999, edges) == set()
        assert graph.transitive_prerequisites(999999, edges) == set()
        assert graph.direct_dependents(999999, edges) == set()

    def test_topological_order_deterministic(self, db_session):
        """Prerequisites always precede dependents; ready nodes are taken in
        ascending concept_id order so the output is stable run to run."""
        a = _make_concept(db_session, "C-A")
        b = _make_concept(db_session, "C-B")
        c = _make_concept(db_session, "C-C")
        d = _make_concept(db_session, "C-D")
        _edge(db_session, c, a)  # a -> c
        _edge(db_session, c, b)  # b -> c
        _edge(db_session, d, c)  # c -> d
        db_session.commit()
        edges = _all_edges(db_session)
        ids = [a.concept_id, b.concept_id, c.concept_id, d.concept_id]

        order = graph.topological_order(ids, edges)
        assert order.index(a.concept_id) < order.index(c.concept_id)
        assert order.index(b.concept_id) < order.index(c.concept_id)
        assert order.index(c.concept_id) < order.index(d.concept_id)
        assert order == sorted(ids)  # this DAG is a single chain by id
        assert graph.topological_order(ids, edges) == order  # stable

    def test_traversal_survives_malformed_cycle(self, db_session):
        """Rows inserted outside the service (e.g. manual DB edits) can form
        a cycle — traversal must still terminate and stay deterministic."""
        a = _make_concept(db_session, "C-A")
        b = _make_concept(db_session, "C-B")
        c = _make_concept(db_session, "C-C")
        _edge(db_session, b, a)
        _edge(db_session, c, b)
        _edge(db_session, a, c)  # a -> b -> c -> a
        db_session.commit()
        edges = _all_edges(db_session)

        assert graph.transitive_prerequisites(a.concept_id, edges) == {
            b.concept_id,
            c.concept_id,
        }
        assert graph.transitive_dependents(a.concept_id, edges) == {
            b.concept_id,
            c.concept_id,
        }
        order = graph.topological_order(
            [a.concept_id, b.concept_id, c.concept_id], edges
        )
        assert order == sorted([a.concept_id, b.concept_id, c.concept_id])


# ---------- persistence constraints ----------


class TestGraphConstraints:
    def test_duplicate_edge_rejected_by_pk(self, db_session):
        a = _make_concept(db_session, "C-A")
        b = _make_concept(db_session, "C-B")
        _edge(db_session, b, a)
        db_session.commit()
        db_session.add(  # identical pair again — the composite PK must reject
            ConceptDependency(
                concept_id=b.concept_id,
                prerequisite_concept_id=a.concept_id,
            )
        )
        with pytest.raises(IntegrityError):
            db_session.flush()
        db_session.rollback()

    def test_self_edge_rejected_by_check(self, db_session):
        a = _make_concept(db_session, "C-A")
        db_session.commit()
        db_session.add(
            ConceptDependency(
                concept_id=a.concept_id,
                prerequisite_concept_id=a.concept_id,
            )
        )
        with pytest.raises(IntegrityError):
            db_session.flush()
        db_session.rollback()

    def test_edges_persist_and_read_back(self, db_session):
        a = _make_concept(db_session, "C-A")
        b = _make_concept(db_session, "C-B")
        _edge(db_session, b, a)
        db_session.commit()
        rows = db_session.query(ConceptDependency).all()
        assert [(r.concept_id, r.prerequisite_concept_id) for r in rows] == [
            (b.concept_id, a.concept_id)
        ]
        assert rows[0].created_at is not None


# ---------- admin write path (service level) ----------


class TestSetPrerequisites:
    def test_set_and_read_back(self, db_session):
        a = _make_concept(db_session, "C-A", name="A")
        b = _make_concept(db_session, "C-B", name="B")
        result = graph.set_concept_prerequisites(
            db_session, b.concept_id, [a.concept_id]
        )
        assert result.concept_id == b.concept_id
        assert [p.concept_id for p in result.prerequisites] == [a.concept_id]
        rows = db_session.query(ConceptDependency).all()
        assert len(rows) == 1

    def test_replace_semantics(self, db_session):
        a = _make_concept(db_session, "C-A")
        b = _make_concept(db_session, "C-B")
        c = _make_concept(db_session, "C-C")
        graph.set_concept_prerequisites(db_session, c.concept_id, [a.concept_id])
        graph.set_concept_prerequisites(db_session, c.concept_id, [b.concept_id])
        edges = _all_edges(db_session)
        assert graph.direct_prerequisites(c.concept_id, edges) == {
            b.concept_id
        }
        assert db_session.query(ConceptDependency).count() == 1

    def test_empty_list_clears(self, db_session):
        a = _make_concept(db_session, "C-A")
        b = _make_concept(db_session, "C-B")
        graph.set_concept_prerequisites(db_session, b.concept_id, [a.concept_id])
        result = graph.set_concept_prerequisites(db_session, b.concept_id, [])
        assert result.prerequisites == []
        assert db_session.query(ConceptDependency).count() == 0

    def test_idempotent_repeat_set(self, db_session):
        a = _make_concept(db_session, "C-A")
        b = _make_concept(db_session, "C-B")
        graph.set_concept_prerequisites(db_session, b.concept_id, [a.concept_id])
        again = graph.set_concept_prerequisites(
            db_session, b.concept_id, [a.concept_id]
        )
        assert [p.concept_id for p in again.prerequisites] == [a.concept_id]
        assert db_session.query(ConceptDependency).count() == 1

    def test_unknown_concept_404(self, db_session):
        a = _make_concept(db_session, "C-A")
        with pytest.raises(AppError) as exc:
            graph.set_concept_prerequisites(
                db_session, 999999, [a.concept_id]
            )
        assert exc.value.status_code == 404
        assert exc.value.code == "concept_not_found"

    def test_unknown_prerequisite_404(self, db_session):
        b = _make_concept(db_session, "C-B")
        with pytest.raises(AppError) as exc:
            graph.set_concept_prerequisites(
                db_session, b.concept_id, [999998, 999999]
            )
        assert exc.value.status_code == 404
        assert exc.value.code == "concept_not_found"
        assert [d["concept_id"] for d in exc.value.details] == [999998, 999999]

    def test_self_dependency_422(self, db_session):
        a = _make_concept(db_session, "C-A")
        with pytest.raises(AppError) as exc:
            graph.set_concept_prerequisites(
                db_session, a.concept_id, [a.concept_id]
            )
        assert exc.value.status_code == 422
        assert exc.value.code == "self_dependency"

    def test_duplicate_ids_in_payload_422(self, db_session):
        a = _make_concept(db_session, "C-A")
        b = _make_concept(db_session, "C-B")
        with pytest.raises(AppError) as exc:
            graph.set_concept_prerequisites(
                db_session, b.concept_id, [a.concept_id, a.concept_id]
            )
        assert exc.value.status_code == 422
        assert exc.value.code == "duplicate_prerequisite"

    def test_two_node_cycle_409(self, db_session):
        a = _make_concept(db_session, "C-A")
        b = _make_concept(db_session, "C-B")
        graph.set_concept_prerequisites(db_session, b.concept_id, [a.concept_id])
        with pytest.raises(AppError) as exc:
            graph.set_concept_prerequisites(
                db_session, a.concept_id, [b.concept_id]
            )
        assert exc.value.status_code == 409
        assert exc.value.code == "dependency_cycle"

    def test_three_node_cycle_409(self, db_session):
        a = _make_concept(db_session, "C-A")
        b = _make_concept(db_session, "C-B")
        c = _make_concept(db_session, "C-C")
        graph.set_concept_prerequisites(db_session, b.concept_id, [a.concept_id])
        graph.set_concept_prerequisites(db_session, c.concept_id, [b.concept_id])
        with pytest.raises(AppError) as exc:
            graph.set_concept_prerequisites(
                db_session, a.concept_id, [c.concept_id]
            )
        assert exc.value.status_code == 409
        assert exc.value.code == "dependency_cycle"

    def test_deep_chain_no_false_cycle(self, db_session):
        """Extending a chain at the head is legal — only closing the loop
        back onto an ancestor is a cycle."""
        ids = []
        for code in ("C-A", "C-B", "C-C", "C-D"):
            ids.append(_make_concept(db_session, code).concept_id)
        graph.set_concept_prerequisites(db_session, ids[1], [ids[0]])
        graph.set_concept_prerequisites(db_session, ids[2], [ids[1]])
        result = graph.set_concept_prerequisites(db_session, ids[3], [ids[2]])
        assert [p.concept_id for p in result.prerequisites] == [ids[2]]
        edges = _all_edges(db_session)
        assert graph.transitive_prerequisites(ids[3], edges) == {
            ids[0],
            ids[1],
            ids[2],
        }


# ---------- endpoints ----------


class TestGraphEndpoints:
    ADMIN_URL = "/api/v1/admin/concepts/{}/prerequisites"
    GRAPH_URL = "/api/v1/concepts/graph"

    def _admin_token(self, client, db_session):
        _make_admin(db_session)
        return _login(client, "admin@test.dev", "Admin123!")

    def test_admin_put_creates_edges(self, client, db_session):
        token = self._admin_token(client, db_session)
        a = _make_concept(db_session, "C-A", name="A")
        b = _make_concept(db_session, "C-B", name="B")
        db_session.commit()
        r = client.put(
            self.ADMIN_URL.format(b.concept_id),
            json={"prerequisite_concept_ids": [a.concept_id]},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["concept_id"] == b.concept_id
        assert [p["concept_code"] for p in body["prerequisites"]] == ["C-A"]

    def test_graph_endpoint_shape(self, client, db_session):
        token = self._admin_token(client, db_session)
        a = _make_concept(db_session, "C-A")
        b = _make_concept(db_session, "C-B")
        _edge(db_session, b, a)
        db_session.commit()
        r = client.get(
            self.GRAPH_URL, headers={"Authorization": f"Bearer {token}"}
        )
        assert r.status_code == 200
        body = r.json()
        assert body["edges"] == [
            {"prerequisite_concept_id": a.concept_id, "concept_id": b.concept_id}
        ]
        node_b = next(n for n in body["nodes"] if n["concept_id"] == b.concept_id)
        assert node_b["prerequisites"] == [a.concept_id]
        node_a = next(n for n in body["nodes"] if n["concept_id"] == a.concept_id)
        assert node_a["prerequisites"] == []
        # deterministic ordering: nodes by concept_id
        assert [n["concept_id"] for n in body["nodes"]] == sorted(
            n["concept_id"] for n in body["nodes"]
        )

    def test_empty_graph(self, client, db_session):
        token = self._admin_token(client, db_session)
        _make_concept(db_session, "C-A")
        db_session.commit()
        r = client.get(
            self.GRAPH_URL, headers={"Authorization": f"Bearer {token}"}
        )
        assert r.status_code == 200
        assert r.json()["edges"] == []
        assert len(r.json()["nodes"]) == 1

    def test_learner_cannot_write(self, client, db_session):
        _make_learner(db_session)
        c = _make_concept(db_session, "C-A")
        db_session.commit()
        token = _login(client, "learner@test.dev", "Secret123!")
        r = client.put(
            self.ADMIN_URL.format(c.concept_id),
            json={"prerequisite_concept_ids": []},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 403

    def test_unauthenticated_rejected(self, client, db_session):
        c = _make_concept(db_session, "C-A")
        db_session.commit()
        assert client.get(self.GRAPH_URL).status_code == 401
        assert (
            client.put(
                self.ADMIN_URL.format(c.concept_id),
                json={"prerequisite_concept_ids": []},
            ).status_code
            == 401
        )

    def test_put_unknown_concept_404(self, client, db_session):
        token = self._admin_token(client, db_session)
        r = client.put(
            self.ADMIN_URL.format(999999),
            json={"prerequisite_concept_ids": []},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 404
        assert r.json()["error"]["code"] == "concept_not_found"

    def test_put_self_edge_422(self, client, db_session):
        token = self._admin_token(client, db_session)
        a = _make_concept(db_session, "C-A")
        db_session.commit()
        r = client.put(
            self.ADMIN_URL.format(a.concept_id),
            json={"prerequisite_concept_ids": [a.concept_id]},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 422
        assert r.json()["error"]["code"] == "self_dependency"

    def test_put_cycle_409(self, client, db_session):
        token = self._admin_token(client, db_session)
        a = _make_concept(db_session, "C-A")
        b = _make_concept(db_session, "C-B")
        _edge(db_session, b, a)
        db_session.commit()
        r = client.put(
            self.ADMIN_URL.format(a.concept_id),
            json={"prerequisite_concept_ids": [b.concept_id]},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 409
        assert r.json()["error"]["code"] == "dependency_cycle"
