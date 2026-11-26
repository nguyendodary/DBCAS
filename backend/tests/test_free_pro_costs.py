"""Free allowance, demo Pro duration, and every provider HTTP attempt."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import json
from uuid import uuid4

import httpx
import pytest
from sqlalchemy import func, select

from app.config import Settings
from app.errors import AppError
from app.models import Account, Assessment, AssessmentSession, OperatingCost, ProPurchase
from app.services.subscription_service import (
    VIETNAM_TIME, _monthly_free_used, buy_pro_demo, require_new_session, status,
)
from app.services.llm.costs import make_cost_observer
from app.services.llm.provider import ChatCompletionsProvider, ChatMessage, StructuredRequest
from app.routers.admin import get_financial_report, list_accounts
from app.routers.auth import DemoCheckoutRequest
from pydantic import ValidationError


def _account(db):
    user = Account(email="quota@example.test", password_hash="test")
    db.add(user)
    db.flush()
    return user


def test_admin_account_roster_shows_effective_plans(db_session):
    db = db_session
    free = _account(db)
    pro = Account(email="pro@example.test", password_hash="test",
                  plan="pro", pro_expires_at=datetime.now(timezone.utc) + timedelta(days=30))
    expired = Account(email="expired@example.test", password_hash="test",
                      plan="pro", pro_expires_at=datetime.now(timezone.utc) - timedelta(days=1))
    db.add_all([pro, expired])
    db.flush()

    roster = {item.email: item.model_dump(mode="json") for item in list_accounts(None, db)}
    assert roster[free.email]["plan"] == "free"
    assert roster[free.email]["pro_expires_at"] is None
    assert roster[pro.email]["plan"] == "pro"
    assert roster[pro.email]["pro_expires_at"] is not None
    assert roster[expired.email]["plan"] == "free"
    assert roster[expired.email]["pro_expires_at"] is None


def test_three_free_sessions_block_new_start_and_pro_expires(db_session):
    db = db_session
    user = _account(db)
    assessment = Assessment(title="Quota test", status="published", created_by=user.account_id)
    db.add(assessment)
    db.flush()
    for n in range(3):
        require_new_session(db, user)
        db.add(AssessmentSession(assessment_id=assessment.assessment_id,
                                 learner_id=user.account_id, status="completed",
                                 expires_at=datetime.now(timezone.utc) + timedelta(hours=1)))
        db.commit()
    assert status(db, user)["free_sessions_remaining"] == 0
    with pytest.raises(AppError) as error:
        require_new_session(db, user)
    assert error.value.code == "free_limit_reached"
    db.rollback()

    checkout_id = uuid4()
    upgraded = buy_pro_demo(db, user, 99000, checkout_id)
    assert upgraded["plan"] == "pro"
    assert upgraded["pro_expires_at"] > datetime.now(timezone.utc) + timedelta(days=29)
    assert db.scalar(select(ProPurchase.amount_vnd)) == 99000
    assert db.scalar(select(ProPurchase.simulated)) is True
    assert upgraded["demo_payment"]["amount_vnd"] == 99000
    repeated = buy_pro_demo(db, user, 99000, checkout_id)
    assert repeated["pro_expires_at"] == upgraded["pro_expires_at"]
    assert repeated["demo_payment"]["purchase_id"] == upgraded["demo_payment"]["purchase_id"]
    assert db.scalar(select(func.count()).select_from(ProPurchase)) == 1
    require_new_session(db, user)
    db.rollback()
    user.plan = "pro"
    user.pro_expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    db.commit()
    with pytest.raises(AppError) as error:
        require_new_session(db, user)
    assert error.value.code == "free_limit_reached"


def test_free_limit_resets_by_vietnam_calendar_month_and_ignores_pro_sessions(db_session):
    db = db_session
    user = _account(db)
    # UTC March 31, 18:00 is already April 1 in Vietnam.
    april = datetime(2026, 3, 31, 18, tzinfo=timezone.utc)
    march = datetime(2026, 3, 31, 16, tzinfo=timezone.utc)
    db.add(AssessmentSession(learner_id=user.account_id, status="completed",
                             started_at=march, expires_at=march + timedelta(hours=1)))
    db.add(AssessmentSession(learner_id=user.account_id, status="completed",
                             started_at=april, expires_at=april + timedelta(hours=1)))
    db.flush()
    assert april.astimezone(VIETNAM_TIME).month == 4
    assert _monthly_free_used(db, user.account_id, april) == 1

    db.add(ProPurchase(account_id=user.account_id, amount_usd=Decimal("0"), simulated=True,
                       purchased_at=april + timedelta(hours=1),
                       expires_at=april + timedelta(days=30)))
    db.add(AssessmentSession(learner_id=user.account_id, status="completed",
                             started_at=april + timedelta(hours=2),
                             expires_at=april + timedelta(hours=3)))
    db.flush()
    assert _monthly_free_used(db, user.account_id, april + timedelta(hours=4)) == 1


def test_demo_checkout_requires_test_token():
    with pytest.raises(ValidationError):
        DemoCheckoutRequest(request_id=uuid4(), test_token="real-card-number")
    assert DemoCheckoutRequest(
        request_id=uuid4(), test_token="dbcas-demo-visa-approved"
    ).test_token == "dbcas-demo-visa-approved"


def test_provider_retries_are_costed_per_http_attempt(db_session):
    attempts = []

    def respond(request):
        attempts.append(request)
        if len(attempts) == 1:
            return httpx.Response(429, json={"error": "limited"})
        return httpx.Response(200, json={
            "choices": [{"message": {"content": '{"ok": true}'}}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 50},
        })

    settings = Settings(llm_input_usd_per_million=2, llm_output_usd_per_million=8)
    observer = make_cost_observer(db_session.get_bind(), settings)
    provider = ChatCompletionsProvider("https://ai.example/v1", "test-key",
        transport=httpx.MockTransport(respond), sleeper=lambda _: None,
        on_attempt=observer)
    request = StructuredRequest(task_type="essay_grading", model="grader-test",
                                messages=(ChatMessage("user", "test"),))
    assert provider.generate(request) == '{"ok": true}'
    costs = list(db_session.scalars(select(OperatingCost).order_by(OperatingCost.cost_id)))
    assert len(costs) == 2
    assert [r.outcome for r in costs] == ["http_error", "success"]
    assert [r.http_status for r in costs] == [429, 200]
    assert costs[0].amount_usd is None
    assert costs[1].amount_usd == Decimal("0.00060000")
    assert (costs[1].prompt_tokens, costs[1].completion_tokens) == (100, 50)


def test_deepseek_flash_json_request_and_cache_aware_estimate(db_session):
    bodies = []

    def respond(request):
        bodies.append(json.loads(request.content))
        return httpx.Response(200, json={
            "choices": [{"message": {"content": '{"ok": true}'}}],
            "usage": {"prompt_tokens": 1_000_000, "prompt_cache_hit_tokens": 100_000,
                      "prompt_cache_miss_tokens": 900_000, "completion_tokens": 500_000},
        })

    settings = Settings(llm_base_url="https://api.deepseek.com",
                        llm_input_usd_per_million=0.15,
                        llm_output_usd_per_million=0.6,
                        llm_cache_hit_usd_per_million=0.003)
    observer = make_cost_observer(db_session.get_bind(), settings,
                                  clock=lambda: datetime(2026, 11, 15, 8, tzinfo=timezone.utc))
    provider = ChatCompletionsProvider(settings.llm_base_url, "test-key",
        transport=httpx.MockTransport(respond), on_attempt=observer)
    request = StructuredRequest(task_type="essay_grading", model="deepseek-flash",
                                messages=(ChatMessage("user", "Return JSON"),),
                                json_schema={"name": "result", "strict": True,
                                             "schema": {"type": "object", "properties": {"ok": {"type": "boolean"}}}})
    assert provider.generate(request) == '{"ok": true}'
    assert bodies[0]["response_format"] == {"type": "json_object"}
    assert bodies[0]["thinking"] == {"type": "disabled"}
    cost = db_session.scalar(select(OperatingCost).where(OperatingCost.model == "deepseek-flash"))
    assert cost.amount_usd == Decimal("0.43530000")

    peak_observer = make_cost_observer(db_session.get_bind(), settings,
        clock=lambda: datetime(2026, 11, 16, 7, tzinfo=timezone.utc))
    peak_observer(request, "success", 200, {
        "usage": {"prompt_tokens": 1_000_000, "prompt_cache_hit_tokens": 100_000,
                  "prompt_cache_miss_tokens": 900_000, "completion_tokens": 500_000},
    })
    amounts = list(db_session.scalars(select(OperatingCost.amount_usd).where(
        OperatingCost.model == "deepseek-flash").order_by(OperatingCost.cost_id)))
    assert amounts == [Decimal("0.43530000"), Decimal("0.87060000")]


def test_deepseek_missing_cache_breakdown_keeps_cost_unpriced(db_session):
    settings = Settings(llm_base_url="https://api.deepseek.com",
                        llm_input_usd_per_million=0.15, llm_output_usd_per_million=0.6,
                        llm_cache_hit_usd_per_million=0.003)
    observer = make_cost_observer(db_session.get_bind(), settings)
    request = StructuredRequest(task_type="essay_grading", model="deepseek-flash",
                                messages=(ChatMessage("user", "test"),))
    observer(request, "success", 200,
             {"usage": {"prompt_tokens": 100, "completion_tokens": 50}})
    cost = db_session.scalar(select(OperatingCost).where(OperatingCost.model == "deepseek-flash"))
    assert cost.amount_usd is None


def test_admin_financial_report_uses_vietnam_month_and_flags_unpriced_calls(db_session):
    db = db_session
    user = _account(db)
    db.add(ProPurchase(account_id=user.account_id, amount_usd=Decimal("0"),
                       amount_vnd=99000,
                       simulated=True,
                       purchased_at=datetime(2026, 10, 31, 18, tzinfo=timezone.utc),
                       expires_at=datetime(2026, 11, 30, 18, tzinfo=timezone.utc)))
    db.add(ProPurchase(account_id=user.account_id, amount_usd=Decimal("0"),
                       amount_vnd=123000,
                       simulated=True,
                       purchased_at=datetime(2026, 11, 30, 18, tzinfo=timezone.utc),
                       expires_at=datetime(2026, 12, 30, 18, tzinfo=timezone.utc)))
    for amount in (Decimal("0.42"), None):
        db.add(OperatingCost(kind="ai", task_type="essay_grading", model="deepseek-flash",
                             amount_usd=amount, outcome="success",
                             created_at=datetime(2026, 11, 2, tzinfo=timezone.utc)))
    db.add(OperatingCost(kind="hosting", amount_usd=Decimal("1.25"),
                         outcome="success",
                         created_at=datetime(2026, 11, 2, tzinfo=timezone.utc)))
    db.flush()

    report = get_financial_report("2026-11", user, db, Settings())
    assert report["purchase_count"] == 1
    assert report["currency"] == "VND"
    assert report["revenue"] == 99000
    assert report["ai_cost"] == 10920
    assert report["hosting_cost"] == 32500
    assert report["balance"] == 55580
    assert report["unpriced_ai_calls"] == 1
