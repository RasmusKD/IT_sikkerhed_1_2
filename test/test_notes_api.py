"""
Notes Microservice - Unit Tests med Boundary Value Analysis (BVA).

Test design teknik: Boundary Value Analysis
Vi tester graensevaerdier for hvert input:
  - Token: gyldigt, ugyldigt, manglende
  - Note title/content: tomt, normalt, langt
  - Ejerskab: egen note, andres note
  - ID: eksisterende, ikke-eksisterende

RISIKO: Hvis disse tests fejler, kan uautoriserede brugere laese eller
slette andres noter.
"""
import pytest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from notes_api import app, notes_db, _save_db, auth, DB_FILE
from auth_api import app as auth_app, user_db, _create_default_admin, auth as auth_svc


@pytest.fixture(autouse=True)
def clean_db():
    """Fixture: Ryd noter og opret frisk admin + testbruger foer hver test."""
    notes_db.clear()
    user_db.clear()
    _create_default_admin()

    # Opret en testbruger via auth API
    auth_client = TestClient(auth_app)
    auth_client.post("/register", json={
        "username": "testuser",
        "password": "test123",
        "first_name": "Test",
        "last_name": "User",
        "roles": ["user"]
    })

    yield

    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    auth_db = "auth_db.json"
    if os.path.exists(auth_db):
        os.remove(auth_db)


client = TestClient(app)
auth_client = TestClient(auth_app)


def _get_token(username="admin", password="admin"):
    """Helper: Hent JWT token fra auth API."""
    resp = auth_client.post("/token", json={
        "username": username,
        "password": password
    })
    return resp.json()["token"]


# =============================================================================
# AUTH INTEGRATION Tests (BVA: token graensevaerdier)
# =============================================================================

class TestAuthIntegration:
    """Tester at microservicen afviser requests uden gyldig auth."""

    def test_valid_token_accepted(self):
        """BVA: Gyldigt token - skal give adgang."""
        token = _get_token()
        response = client.get("/notes", headers={"token": token})
        assert response.status_code == 200

    def test_invalid_token_rejected(self):
        """BVA: Ugyldigt token - skal afvises med 401."""
        response = client.get("/notes", headers={"token": "Bearer faketoken123"})
        assert response.status_code == 401

    def test_missing_token_rejected(self):
        """BVA: Manglende token - skal give 422 (validation error)."""
        response = client.get("/notes")
        assert response.status_code == 422


# =============================================================================
# CREATE NOTE Tests (BVA: title/content graensevaerdier)
# =============================================================================

class TestCreateNote:
    """POST /notes - BVA paa title og content felter."""

    def test_create_normal_note(self):
        """BVA: Normal note med title og content - skal oprettes."""
        token = _get_token()
        response = client.post("/notes",
            json={"title": "Min note", "content": "Noget vigtigt"},
            headers={"token": token}
        )
        assert response.status_code == 201
        assert "id" in response.json()

    def test_create_note_empty_title_fails(self):
        """BVA: Tom title (graensevaerdi) - skal afvises."""
        token = _get_token()
        response = client.post("/notes",
            json={"title": "", "content": "har content"},
            headers={"token": token}
        )
        assert response.status_code == 400

    def test_create_note_empty_content_fails(self):
        """BVA: Tom content (graensevaerdi) - skal afvises."""
        token = _get_token()
        response = client.post("/notes",
            json={"title": "har title", "content": ""},
            headers={"token": token}
        )
        assert response.status_code == 400

    def test_create_note_whitespace_title_fails(self):
        """BVA: Title med kun mellemrum - skal afvises."""
        token = _get_token()
        response = client.post("/notes",
            json={"title": "   ", "content": "har content"},
            headers={"token": token}
        )
        assert response.status_code == 400

    def test_create_long_note(self):
        """BVA: Meget lang note - skal accepteres."""
        token = _get_token()
        response = client.post("/notes",
            json={"title": "Lang note", "content": "x" * 10000},
            headers={"token": token}
        )
        assert response.status_code == 201


# =============================================================================
# GET NOTES Tests (BVA: ejerskab graensevaerdier)
# =============================================================================

class TestGetNotes:
    """GET /notes - BVA paa ejerskab."""

    def test_get_empty_notes(self):
        """BVA: Ingen noter - skal returnere tom liste."""
        token = _get_token()
        response = client.get("/notes", headers={"token": token})
        assert response.status_code == 200
        assert response.json()["count"] == 0

    def test_get_own_notes_only(self):
        """BVA: Bruger ser kun egne noter, ikke andres."""
        # Admin opretter en note
        admin_token = _get_token("admin", "admin")
        client.post("/notes",
            json={"title": "Admin note", "content": "Admin only"},
            headers={"token": admin_token}
        )

        # Testuser opretter en note
        user_token = _get_token("testuser", "test123")
        client.post("/notes",
            json={"title": "User note", "content": "User only"},
            headers={"token": user_token}
        )

        # Testuser ser kun sin egen
        response = client.get("/notes", headers={"token": user_token})
        assert response.json()["count"] == 1
        assert response.json()["notes"][0]["title"] == "User note"

        # Admin ser kun sin egen
        response = client.get("/notes", headers={"token": admin_token})
        assert response.json()["count"] == 1
        assert response.json()["notes"][0]["title"] == "Admin note"


# =============================================================================
# DELETE NOTE Tests (BVA: note ID og ejerskab graensevaerdier)
# =============================================================================

class TestDeleteNote:
    """DELETE /notes/{id} - BVA paa note ID og ejerskab."""

    def test_delete_own_note(self):
        """BVA: Slet egen note - skal lykkes."""
        token = _get_token()
        create_resp = client.post("/notes",
            json={"title": "Slet mig", "content": "Temp"},
            headers={"token": token}
        )
        note_id = create_resp.json()["id"]

        response = client.delete(f"/notes/{note_id}", headers={"token": token})
        assert response.status_code == 200

    def test_delete_nonexistent_note_fails(self):
        """BVA: Ikke-eksisterende ID (graensevaerdi) - 404."""
        token = _get_token()
        response = client.delete("/notes/findesikke", headers={"token": token})
        assert response.status_code == 404

    def test_delete_other_users_note_fails(self):
        """BVA: Forsog paa at slette andres note - 403."""
        # Admin opretter note
        admin_token = _get_token("admin", "admin")
        create_resp = client.post("/notes",
            json={"title": "Admin note", "content": "Privat"},
            headers={"token": admin_token}
        )
        note_id = create_resp.json()["id"]

        # Testuser forsoeger at slette den
        user_token = _get_token("testuser", "test123")
        response = client.delete(f"/notes/{note_id}", headers={"token": user_token})
        assert response.status_code == 403
