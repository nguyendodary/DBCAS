import pytest
from pydantic import ValidationError
from app.schemas import ProvisionAccountRequest

@pytest.mark.parametrize("role", ["Learner", "Administrator,Learner", "Owner"])
def test_provisioning_accepts_only_the_documented_administrator_role(role):
    with pytest.raises(ValidationError):
        ProvisionAccountRequest(name="Local administrator", email="admin@test.dev", password="Secret123!", role=role)

def test_provisioning_defaults_to_administrator():
    assert ProvisionAccountRequest(name="Local administrator", email="admin@test.dev", password="Secret123!").role == "Administrator"
