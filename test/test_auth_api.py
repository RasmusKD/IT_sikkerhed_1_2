"""
Auth API - Unit Tests
Tester authentication endpoints: registrering, login, token, deaktiver, aktiver.

RISIKO: Hvis disse tests fejler, kan uautoriserede brugere få adgang
til systemet eller autoriserede brugere blive låst ude.
"""
import pytest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from auth_api import app, user_db, _save_db, _create_default_admin, auth, DB_FILE


@pytest.fixture(autouse=True)
def clean_db():
    """Fixture: Ryd database og opret frisk admin før hver test."""
    user_db.clear()
    _create_default_admin()
    yield
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)


client = TestClient(app)


def _get_admin_token():
    """Helper: Hent admin JWT token."""
    response = client.post("/token", json={
        "username": "admin",
        "password": "admin"
    })
    return response.json()["token"]


# =============================================================================
# DEFAULT ADMIN Tests
# =============================================================================

class TestDefaultAdmin:
    """Test at default admin bruger oprettes automatisk."""

    def test_admin_created_on_empty_db(self):
        """
        RISIKO: Ingen admin → ingen kan administrere systemet.
        """
        # Given: En frisk database
        # Then: Admin bruger eksisterer
        assert "admin" in user_db
        assert user_db["admin"]["active"] == True
        assert "admin" in user_db["admin"]["roles"]

    def test_admin_password_is_hashed(self):
        """
        RISIKO: Admin password i klartekst → fuld systemadgang ved datalæk.
        """
        # Given: Default admin bruger
        # Then: Password er hashed (ikke "admin" i klartekst)
        assert user_db["admin"]["password"] != "admin"
        assert auth.verify_password("admin", user_db["admin"]["password"])

    def test_admin_name_is_encrypted(self):
        """
        RISIKO: Admin PII i klartekst → GDPR overtrædelse.
        """
        # Given: Default admin bruger
        # Then: Navn er krypteret
        assert user_db["admin"]["first_name"] != "Admin"
        assert auth.decrypt_data(user_db["admin"]["first_name"]) == "Admin"


# =============================================================================
# REGISTER Tests
# =============================================================================

class TestRegister:
    """POST /register"""

    def test_register_new_user(self):
        """
        RISIKO: Kan ikke oprette brugere → systemet er ubrugeligt.
        """
        # Given: Kun admin i databasen
        # When: En ny bruger registreres
        response = client.post("/register", json={
            "username": "rasmus",
            "password": "secret123",
            "first_name": "Rasmus",
            "last_name": "K",
            "roles": ["user"]
        })

        # Then: Bruger oprettes
        assert response.status_code == 201
        assert "rasmus" in user_db

    def test_register_duplicate_user_fails(self):
        """
        RISIKO: Duplikerede brugere → datakonflikt.
        """
        # Given: Admin eksisterer
        # When: Samme brugernavn forsøges registreret
        response = client.post("/register", json={
            "username": "admin",
            "password": "nyt_pass",
            "first_name": "Fake",
            "last_name": "Admin",
            "roles": ["user"]
        })

        # Then: 400 fejl
        assert response.status_code == 400


# =============================================================================
# TOKEN Tests
# =============================================================================

class TestToken:
    """POST /token"""

    def test_login_returns_token(self):
        """
        RISIKO: Kan ikke logge ind → systemet er låst.
        """
        # Given: Admin bruger eksisterer
        # When: Login med korrekte credentials
        response = client.post("/token", json={
            "username": "admin",
            "password": "admin"
        })

        # Then: JWT token returneres
        assert response.status_code == 200
        token = response.json()["token"]
        assert token.startswith("Bearer ")

    def test_login_wrong_password_fails(self):
        """
        RISIKO: Forkert password giver adgang → sikkerhedsbrist.
        """
        # Given: Admin bruger
        # When: Login med forkert password
        response = client.post("/token", json={
            "username": "admin",
            "password": "forkert"
        })

        # Then: 401 Unauthorized
        assert response.status_code == 401

    def test_login_nonexistent_user_fails(self):
        """
        RISIKO: Information leakage om brugereksistens.
        """
        # Given: Bruger eksisterer ikke
        # When: Login forsøges
        response = client.post("/token", json={
            "username": "ghost",
            "password": "pass"
        })

        # Then: 401 (ikke 404, for at undgå info leakage)
        assert response.status_code == 401

    def test_deactivated_user_cannot_login(self):
        """
        RISIKO: Deaktiveret bruger kan stadig logge ind.
        """
        # Given: En deaktiveret bruger
        client.post("/register", json={
            "username": "test_user",
            "password": "pass",
            "first_name": "Test",
            "last_name": "User",
            "roles": ["user"]
        })
        admin_token = _get_admin_token()
        client.post("/deactivate",
            json={"username": "test_user"},
            headers={"token": admin_token}
        )

        # When: Deaktiveret bruger forsøger login
        response = client.post("/token", json={
            "username": "test_user",
            "password": "pass"
        })

        # Then: 403 Forbidden
        assert response.status_code == 403


# =============================================================================
# CHANGE PASSWORD Tests
# =============================================================================

class TestChangePassword:
    """POST /change-password"""

    def test_change_password_success(self):
        """
        RISIKO: Bruger kan ikke skifte password → sidder fast med kompromitteret password.
        """
        # Given: Admin bruger med token
        token = _get_admin_token()

        # When: Password ændres
        response = client.post("/change-password",
            json={"old_password": "admin", "new_password": "nyt_password"},
            headers={"token": token}
        )

        # Then: Password er ændret
        assert response.status_code == 200
        assert auth.verify_password("nyt_password", user_db["admin"]["password"])

    def test_change_password_wrong_old_fails(self):
        """
        RISIKO: Password kan ændres uden at kende det nuværende → kontoovertagelse.
        """
        # Given: Admin bruger med token
        token = _get_admin_token()

        # When: Forkert nuværende password angives
        response = client.post("/change-password",
            json={"old_password": "forkert", "new_password": "nyt"},
            headers={"token": token}
        )

        # Then: 401 Unauthorized
        assert response.status_code == 401

    def test_login_with_new_password(self):
        """
        RISIKO: Nyt password virker ikke efter ændring → bruger låst ude.
        """
        # Given: Password er ændret
        token = _get_admin_token()
        client.post("/change-password",
            json={"old_password": "admin", "new_password": "nyt123"},
            headers={"token": token}
        )

        # When: Login med nyt password
        response = client.post("/token", json={
            "username": "admin",
            "password": "nyt123"
        })

        # Then: Token returneres
        assert response.status_code == 200
        assert response.json()["token"].startswith("Bearer ")


# =============================================================================
# DEACTIVATE Tests
# =============================================================================

class TestDeactivate:
    """POST /deactivate"""

    def test_user_can_deactivate_self(self):
        """
        RISIKO: Bruger kan ikke deaktivere sin egen konto.
        """
        # Given: En registreret bruger med token
        client.post("/register", json={
            "username": "rasmus",
            "password": "pass",
            "first_name": "Rasmus",
            "last_name": "K",
            "roles": ["user"]
        })
        token_resp = client.post("/token", json={
            "username": "rasmus",
            "password": "pass"
        })
        token = token_resp.json()["token"]

        # When: Brugeren deaktiverer sig selv
        response = client.post("/deactivate",
            json={"username": "rasmus"},
            headers={"token": token}
        )

        # Then: Konto er deaktiveret
        assert response.status_code == 200
        assert user_db["rasmus"]["active"] == False

    def test_user_cannot_deactivate_others(self):
        """
        RISIKO: Almindelig bruger kan deaktivere andre → privilege escalation.
        """
        # Given: To brugere
        client.post("/register", json={
            "username": "user1",
            "password": "pass",
            "first_name": "User",
            "last_name": "One",
            "roles": ["user"]
        })
        client.post("/register", json={
            "username": "user2",
            "password": "pass",
            "first_name": "User",
            "last_name": "Two",
            "roles": ["user"]
        })
        token_resp = client.post("/token", json={
            "username": "user1",
            "password": "pass"
        })
        token = token_resp.json()["token"]

        # When: User1 forsøger at deaktivere user2
        response = client.post("/deactivate",
            json={"username": "user2"},
            headers={"token": token}
        )

        # Then: 403 Forbidden
        assert response.status_code == 403

    def test_admin_can_deactivate_anyone(self):
        """
        RISIKO: Admin kan ikke administrere brugere.
        """
        # Given: Admin og en bruger
        client.post("/register", json={
            "username": "target",
            "password": "pass",
            "first_name": "Target",
            "last_name": "User",
            "roles": ["user"]
        })
        admin_token = _get_admin_token()

        # When: Admin deaktiverer brugeren
        response = client.post("/deactivate",
            json={"username": "target"},
            headers={"token": admin_token}
        )

        # Then: Bruger er deaktiveret
        assert response.status_code == 200
        assert user_db["target"]["active"] == False


# =============================================================================
# ACTIVATE Tests
# =============================================================================

class TestActivate:
    """POST /activate"""

    def test_admin_can_reactivate_user(self):
        """
        RISIKO: Deaktiverede brugere kan ikke genaktiveres → permanent låst ude.
        """
        # Given: En deaktiveret bruger
        client.post("/register", json={
            "username": "locked",
            "password": "pass",
            "first_name": "Locked",
            "last_name": "User",
            "roles": ["user"]
        })
        admin_token = _get_admin_token()
        client.post("/deactivate",
            json={"username": "locked"},
            headers={"token": admin_token}
        )
        assert user_db["locked"]["active"] == False

        # When: Admin reaktiverer brugeren
        response = client.post("/activate",
            json={"username": "locked"},
            headers={"token": admin_token}
        )

        # Then: Bruger er aktiv igen
        assert response.status_code == 200
        assert user_db["locked"]["active"] == True

    def test_user_cannot_activate_others(self):
        """
        RISIKO: Almindelig bruger kan reaktivere andre → privilege escalation.
        """
        # Given: En bruger og en deaktiveret bruger
        client.post("/register", json={
            "username": "normal",
            "password": "pass",
            "first_name": "Normal",
            "last_name": "User",
            "roles": ["user"]
        })
        client.post("/register", json={
            "username": "deactivated",
            "password": "pass",
            "first_name": "Deac",
            "last_name": "User",
            "roles": ["user"]
        })
        admin_token = _get_admin_token()
        client.post("/deactivate",
            json={"username": "deactivated"},
            headers={"token": admin_token}
        )

        # Hent normal bruger token
        token_resp = client.post("/token", json={
            "username": "normal",
            "password": "pass"
        })
        user_token = token_resp.json()["token"]

        # When: Normal bruger forsøger at reaktivere
        response = client.post("/activate",
            json={"username": "deactivated"},
            headers={"token": user_token}
        )

        # Then: 403 Forbidden
        assert response.status_code == 403
