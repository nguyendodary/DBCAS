"""Shared OAuth/throttle concurrency, deployment guards and bounded renewal."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import httpx
import pytest
from jose import jwt
from sqlalchemy import select, func

from app.config import get_settings
from app.db import get_session_factory
from app.errors import AppError
from app.models import Account, AccountIdentity, OAuthHandoff, LoginThrottleRecord
from app.security import create_access_token, decode_access_token, hash_password
from app.services import oauth
from app.services.deployment_safety import validate_deployment_accounts
from app.services.login_throttle import DatabaseLoginThrottle


def _account(db):
    account=Account(email="shared-auth@test.dev",password_hash=hash_password("SafePassword456!"),status="active")
    db.add(account);db.commit()
    return account


def test_handoff_and_access_tokens_cannot_be_confused(db_session):
    account=_account(db_session)
    settings=get_settings()
    handoff,_=oauth.issue_handoff(account.account_id,"google",settings,db_session)
    with pytest.raises(AppError):decode_access_token(handoff,settings)
    access,_=create_access_token(account.account_id,["Learner"],settings)
    with pytest.raises(oauth.OAuthFlowError):oauth.consume_handoff(access,settings,db_session)
    assert oauth.consume_handoff(handoff,settings,db_session)==account.account_id
    assert db_session.scalar(select(OAuthHandoff)).consumed_at is not None


def test_handoff_single_use_across_concurrent_connections(db_session):
    account=_account(db_session)
    settings=get_settings()
    token,_=oauth.issue_handoff(account.account_id,"github",settings,db_session)
    def consume(_):
        with get_session_factory()() as db:
            try:return oauth.consume_handoff(token,settings,db)
            except oauth.OAuthFlowError:return None
    with ThreadPoolExecutor(max_workers=8) as executor:results=list(executor.map(consume,range(8)))
    assert results.count(account.account_id)==1 and results.count(None)==7


def test_expired_database_handoff_cannot_be_consumed(db_session):
    account=_account(db_session)
    token,_=oauth.issue_handoff(account.account_id,"google",get_settings(),db_session)
    row=db_session.scalar(select(OAuthHandoff))
    row.expires_at=datetime.now(timezone.utc)-timedelta(seconds=1)
    db_session.commit()
    with pytest.raises(oauth.OAuthFlowError):oauth.consume_handoff(token,get_settings(),db_session)


def test_unissued_handoff_cannot_be_consumed(db_session):
    account=_account(db_session)
    settings=get_settings()
    token=jwt.encode({"typ":"oauth_handoff","purpose":"oauth_handoff","jti":"never-issued","sub":str(account.account_id),"exp":datetime.now(timezone.utc)+timedelta(seconds=60)},settings.jwt_secret,algorithm="HS256")
    with pytest.raises(oauth.OAuthFlowError):oauth.consume_handoff(token,settings,db_session)


def test_concurrent_provider_link_creates_one_account_and_identity():
    identity=oauth.ProviderIdentity(provider="google",provider_user_id="same-subject",email="race@test.dev",email_verified=True,name="Race Learner")
    def resolve(_):
        with get_session_factory()() as db:
            return oauth.resolve_or_create(db,identity).account_id
    with ThreadPoolExecutor(max_workers=5) as executor:ids=list(executor.map(resolve,range(5)))
    assert len(set(ids))==1
    with get_session_factory()() as db:
        assert db.scalar(select(func.count()).select_from(Account))==1
        assert db.scalar(select(func.count()).select_from(AccountIdentity))==1
        assert [r.role_name for r in db.get(Account,ids[0]).roles]==["Learner"]


def test_concurrent_different_providers_share_verified_email():
    def resolve(provider):
        identity=oauth.ProviderIdentity(provider=provider,provider_user_id=provider+"-subject",email="same-email@test.dev",email_verified=True,name="Learner")
        with get_session_factory()() as db:return oauth.resolve_or_create(db,identity).account_id
    with ThreadPoolExecutor(max_workers=2) as executor:ids=list(executor.map(resolve,["google","github"]))
    assert ids[0]==ids[1]
    with get_session_factory()() as db:
        assert db.scalar(select(func.count()).select_from(AccountIdentity))==2


@pytest.mark.parametrize("failure",["network","invalid_json","http_error","unverified"])
def test_github_email_lookup_has_safe_errors(failure):
    def handler(request):
        if request.url.path=="/user":return httpx.Response(200,json={"id":1,"login":"learner"})
        if failure=="network":raise httpx.ConnectError("offline")
        if failure=="invalid_json":return httpx.Response(200,text="not JSON")
        if failure=="http_error":return httpx.Response(503,json={})
        return httpx.Response(200,json=[{"email":"unverified@test.dev","verified":False}])
    spec=oauth.get_provider(get_settings(),"github")
    with httpx.Client(transport=httpx.MockTransport(handler)) as http:
        if failure=="unverified":assert oauth._github_identity(spec,"test-only-token",http).email_verified is False
        else:
            with pytest.raises(oauth.OAuthFlowError) as exc:oauth._github_identity(spec,"test-only-token",http)
            assert exc.value.code=="profile"


def test_shared_throttle_atomic_failure_count():
    settings=get_settings().model_copy(update={"login_rate_limit_attempts":5})
    def fail(_):
        with get_session_factory()() as db:
            throttle=DatabaseLoginThrottle(db);key=throttle.key("NORMAL@test.dev","127.0.0.1")
            with throttle.transaction(key):
                try:throttle.check(key,settings)
                except AppError:return "limited"
                throttle.record_failure(key,settings)
                return "failed"
    with ThreadPoolExecutor(max_workers=10) as executor:out=list(executor.map(fail,range(10)))
    assert out.count("failed")==5 and out.count("limited")==5
    with get_session_factory()() as db:
        row=db.scalar(select(LoginThrottleRecord))
        assert len(row.failures)==5 and "NORMAL" not in row.key_hash
        throttle=DatabaseLoginThrottle(db);key=throttle.key("normal@test.dev","127.0.0.1")
        with throttle.transaction(key):throttle.record_success(key)
        assert db.scalar(select(LoginThrottleRecord)) is None


def test_shared_throttle_expiry_and_capacity(db_session):
    settings=get_settings().model_copy(update={"login_rate_limit_max_keys":1})
    throttle=DatabaseLoginThrottle(db_session)
    key=throttle.key("one@test.dev","ip")
    with throttle.transaction(key):throttle.record_failure(key,settings)
    with pytest.raises(AppError) as exc:
        second=throttle.key("two@test.dev","ip")
        with throttle.transaction(second):throttle.record_failure(second,settings)
    assert exc.value.code=="login_capacity"
    row=db_session.scalar(select(LoginThrottleRecord));row.expires_at=datetime.now(timezone.utc)-timedelta(seconds=1);db_session.commit()
    with throttle.transaction(second):throttle.record_failure(second,settings)
    assert db_session.scalar(select(func.count()).select_from(LoginThrottleRecord))==1


def test_production_startup_rejects_known_seed_credentials(db_session,monkeypatch):
    import app.main as main
    account=_account(db_session)
    account.password_hash=hash_password("Admin123!");db_session.commit()
    production=get_settings().model_copy(update={"deployment_mode":"production"})
    monkeypatch.setattr(main,"settings",production)
    from fastapi.testclient import TestClient
    with pytest.raises(RuntimeError,match="Unsafe development account credentials"):
        with TestClient(main.app):pass
    validate_deployment_accounts(db_session,get_settings())  # development allowed
    account.status="disabled";db_session.commit()
    validate_deployment_accounts(db_session,production)


def test_access_renewal_preserves_absolute_sign_in_time(client,db_session):
    account=_account(db_session)
    token,_=create_access_token(account.account_id,["Learner"],get_settings())
    result=client.post("/api/v1/auth/renew",headers={"Authorization":"Bearer "+token})
    assert result.status_code==200
    before=decode_access_token(token,get_settings());after=decode_access_token(result.json()["access_token"],get_settings())
    assert before["auth_time"]==after["auth_time"]
    assert after["typ"]=="access" and result.json()["expires_in"]<=3600


def test_access_renewal_rejects_absolute_expiry(client,db_session):
    account=_account(db_session);settings=get_settings();now=datetime.now(timezone.utc)
    token=jwt.encode({"typ":"access","sub":str(account.account_id),"auth_time":int(now.timestamp())-settings.access_session_max_minutes*60-1,"iat":int(now.timestamp()),"exp":now+timedelta(minutes=1)},settings.jwt_secret,algorithm="HS256")
    r=client.post("/api/v1/auth/renew",headers={"Authorization":"Bearer "+token})
    assert r.status_code==401 and r.json()["error"]["code"]=="reauthentication_required"
