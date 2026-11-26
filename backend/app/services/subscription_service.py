"""Three Free sessions per Vietnam calendar month and a 30-day demo Pro plan."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import exists, func, select
from sqlalchemy.orm import Session

from ..errors import AppError
from ..models import Account, AssessmentSession, ProPurchase
from ..repositories import SecurityRepository

FREE_SESSION_LIMIT = 3
PRO_DURATION = timedelta(days=30)
VIETNAM_TIME = timezone(timedelta(hours=7))


def effective_plan(account: Account, now: datetime) -> str:
    return "pro" if account.plan == "pro" and account.pro_expires_at and account.pro_expires_at > now else "free"


def _monthly_free_used(db: Session, account_id: int, now: datetime) -> int:
    """Count sessions started while Free during the current Vietnam month.

    Purchase windows identify sessions started as Pro without adding a third
    account field or changing historical assessment-session rows.
    """
    local = now.astimezone(VIETNAM_TIME)
    beginning = local.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    next_month = (beginning.replace(year=beginning.year + 1, month=1)
                  if beginning.month == 12 else beginning.replace(month=beginning.month + 1))
    pro_at_start = exists(select(ProPurchase.purchase_id).where(
        ProPurchase.account_id == account_id,
        ProPurchase.purchased_at <= AssessmentSession.started_at,
        AssessmentSession.started_at < ProPurchase.expires_at,
    ))
    return db.scalar(select(func.count()).select_from(AssessmentSession).where(
        AssessmentSession.learner_id == account_id,
        AssessmentSession.started_at >= beginning.astimezone(timezone.utc),
        AssessmentSession.started_at < next_month.astimezone(timezone.utc),
        ~pro_at_start,
    )) or 0


def status(db: Session, account: Account) -> dict:
    now = datetime.now(timezone.utc)
    used = _monthly_free_used(db, account.account_id, now)
    plan = effective_plan(account, now)
    return {
        "plan": plan,
        "pro_expires_at": account.pro_expires_at if plan == "pro" else None,
        "free_sessions_used": used,
        "free_sessions_remaining": max(0, FREE_SESSION_LIMIT - used),
    }


def require_new_session(db: Session, account: Account) -> None:
    """Hold one per-account transaction lock through the session's commit."""
    SecurityRepository(db).lock(f"plan-session:{account.account_id}")
    current = db.get(Account, account.account_id, with_for_update=True)
    if effective_plan(current, datetime.now(timezone.utc)) == "pro":
        return
    used = _monthly_free_used(db, account.account_id, datetime.now(timezone.utc))
    if used >= FREE_SESSION_LIMIT:
        raise AppError(403, "free_limit_reached", "Your 3 free sessions this month are used; activate Pro or wait until next month")


def buy_pro_demo(db: Session, account: Account, demo_price_vnd: int, request_id: UUID) -> dict:
    """Record one successful test checkout and grant Pro; never charge a card."""
    SecurityRepository(db).lock(f"plan-session:{account.account_id}")
    current = db.get(Account, account.account_id, with_for_update=True)
    previous = db.scalar(select(ProPurchase).where(
        ProPurchase.checkout_request_id == request_id
    ))
    if previous is not None:
        if previous.account_id != current.account_id:
            raise AppError(409, "checkout_request_reused", "Checkout request already used")
        return {
            **status(db, current),
            "demo_payment": {
                "purchase_id": previous.purchase_id,
                "amount_vnd": previous.amount_vnd,
                "currency": "VND",
                "simulated": True,
            },
        }
    now = datetime.now(timezone.utc)
    expires = max(now, current.pro_expires_at or now) + PRO_DURATION
    current.plan = "pro"
    current.pro_expires_at = expires
    purchase = ProPurchase(account_id=current.account_id, amount_usd=Decimal("0"),
                           amount_vnd=demo_price_vnd, checkout_request_id=request_id,
                           simulated=True, purchased_at=now, expires_at=expires)
    db.add(purchase)
    db.commit()
    return {
        **status(db, current),
        "demo_payment": {
            "purchase_id": purchase.purchase_id,
            "amount_vnd": purchase.amount_vnd,
            "currency": "VND",
            "simulated": True,
        },
    }
