"""Provider transport failures and malformed fields are controlled errors."""
import httpx
import pytest
from app.config import Settings
from app.services import oauth


def _spec(provider):
    return oauth.get_provider(Settings(_env_file=None, google_client_id="test", google_client_secret="test",
        google_redirect_uri="http://localhost/callback", github_client_id="test", github_client_secret="test",
        github_redirect_uri="http://localhost/callback"), provider)


@pytest.mark.parametrize("token", [None, True, 123, [], {}, "", "a\r\nb", "x" * 4097])
def test_malformed_token_response_cannot_become_a_bearer_header(token):
    with httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(200, json={"access_token": token}))) as http:
        with pytest.raises(oauth.OAuthFlowError, match="exchange"):
            oauth._exchange_code(_spec("google"), "test-code", "", http)


@pytest.mark.parametrize("change", [{"sub": True}, {"sub": []}, {"sub": ""}, {"sub": "x" * 256},
    {"email": []}, {"email": "invalid"}, {"name": {"bad": True}}])
def test_malformed_google_profile_is_controlled(change):
    profile = {"sub": "subject", "email": "learner@test.dev", "email_verified": True, "name": "Learner", **change}
    with httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(200, json=profile))) as http:
        with pytest.raises(oauth.OAuthFlowError, match="profile"):
            oauth._google_identity(_spec("google"), "test-token", http)


@pytest.mark.parametrize("change", [{"id": True}, {"id": -1}, {"id": "1"}, {"name": []}, {"login": {}}])
def test_malformed_github_profile_is_controlled(change):
    def handler(request):
        return httpx.Response(200, json=[{"email": "learner@test.dev", "verified": True}] if request.url.path.endswith("emails") else {"id": 1, "name": None, "login": "learner", **change})
    with httpx.Client(transport=httpx.MockTransport(handler)) as http:
        with pytest.raises(oauth.OAuthFlowError, match="profile"):
            oauth._github_identity(_spec("github"), "test-token", http)
