import pytest
from auth_flow import AuthFlowService, AuthenticationError


def test_register_and_password_login_success():
    svc = AuthFlowService(pbkdf2_iterations=10_000)
    user = svc.register_user("Alice@Example.com", "StrongPass123")
    assert user.email == "alice@example.com"

    session = svc.login_with_password("alice@example.com", "StrongPass123", now=1000.0)
    assert session["token_type"] == "Bearer"
    claims = svc.verify_access_token(session["access_token"], now=1100.0)
    assert claims["sub"] == user.user_id
    assert claims["email"] == "alice@example.com"


def test_invalid_password_and_account_lockout():
    svc = AuthFlowService(max_failed_attempts=3, lockout_seconds=120, pbkdf2_iterations=10_000)
    svc.register_user("bob@example.com", "CorrectHorse99")

    for _ in range(3):
        with pytest.raises(AuthenticationError) as exc_info:
            svc.login_with_password("bob@example.com", "WrongPass11", now=2000.0)
        assert exc_info.value.code == "INVALID_CREDENTIALS"

    # 4th attempt while locked must fail with ACCOUNT_LOCKED even with right password
    with pytest.raises(AuthenticationError) as locked_exc:
        svc.login_with_password("bob@example.com", "CorrectHorse99", now=2050.0)
    assert locked_exc.value.code == "ACCOUNT_LOCKED"
    assert locked_exc.value.status_code == 429

    # Succeeds after lockout window expires
    resumed = svc.login_with_password("bob@example.com", "CorrectHorse99", now=2200.0)
    assert "access_token" in resumed


def test_refresh_token_rotation_and_replay_revocation():
    svc = AuthFlowService(pbkdf2_iterations=10_000)
    svc.register_user("carol@example.com", "VaultKey2026")
    s1 = svc.login_with_password("carol@example.com", "VaultKey2026", now=5000.0)
    s2 = svc.rotate_refresh_token(s1["refresh_token"], now=5010.0)
    assert s2["refresh_token"] != s1["refresh_token"]

    # Replaying old refresh token revokes the entire token family
    with pytest.raises(AuthenticationError) as replay_exc:
        svc.rotate_refresh_token(s1["refresh_token"], now=5020.0)
    assert replay_exc.value.code == "REFRESH_REPLAY_DETECTED"

    with pytest.raises(AuthenticationError) as revoked_exc:
        svc.verify_access_token(s2["access_token"], now=5025.0)
    assert revoked_exc.value.code == "SESSION_REVOKED"
