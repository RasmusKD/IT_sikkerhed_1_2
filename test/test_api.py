"""
REST API - Unit Tests
Tester alle CRUD(L) endpoints med FastAPIs TestClient.

RISIKO: Hvis disse tests fejler, fungerer API'et ikke korrekt
og brugere kan ikke oprettes, læses, opdateres eller slettes.
"""
import pytest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from api import app, db


API_DB = "api_users.json"


@pytest.fixture(autouse=True)
def clean_db():
    """Fixture: Ryd database før og efter hver test."""
    db.data = []
    db._save()
    yield
    if os.path.exists(API_DB):
        os.remove(API_DB)


client = TestClient(app)


# =============================================================================
# CREATE Tests
# =============================================================================

class TestCreateEndpoint:
    """POST /users"""

    def test_create_user(self):
        """
        RISIKO: Kan ikke oprette brugere via API → systemet er ubrugeligt.
        """
        # Given: En tom database
        # When: En POST request sendes med brugerdata
        response = client.post("/users", json={
            "first_name": "Rasmus",
            "last_name": "K",
            "address": "Hovedgaden",
            "street_number": 42,
            "password": "secret123"
        })

        # Then: Status 201 og brugeren returneres
        assert response.status_code == 201
        data = response.json()
        assert data["first_name"] == "Rasmus"
        assert data["person_id"] == 1

    def test_create_user_password_is_hashed(self):
        """
        RISIKO: Password sendt via API gemmes i klartekst.
        """
        # Given: En tom database
        # When: En bruger oprettes via API
        response = client.post("/users", json={
            "first_name": "Test",
            "last_name": "User",
            "address": "Vej",
            "street_number": 1,
            "password": "hemmeligt"
        })

        # Then: Password er hashed i response
        data = response.json()
        assert data["password"] != "hemmeligt"
        assert len(data["password"]) == 64


# =============================================================================
# READ Tests
# =============================================================================

class TestReadEndpoint:
    """GET /users/{id}"""

    def test_read_existing_user(self):
        """
        RISIKO: Kan ikke hente brugerdata via API.
        """
        # Given: En bruger i databasen
        client.post("/users", json={
            "first_name": "Rasmus",
            "last_name": "K",
            "address": "Vej",
            "street_number": 1,
            "password": "pass"
        })

        # When: En GET request sendes
        response = client.get("/users/1")

        # Then: Brugeren returneres
        assert response.status_code == 200
        assert response.json()["first_name"] == "Rasmus"

    def test_read_nonexistent_user_returns_404(self):
        """
        RISIKO: Fejl ved opslag af manglende bruger → crash.
        """
        # Given: En tom database
        # When: En ikke-eksisterende bruger forespørges
        response = client.get("/users/999")

        # Then: 404 returneres
        assert response.status_code == 404


# =============================================================================
# UPDATE Tests
# =============================================================================

class TestUpdateEndpoint:
    """PUT /users/{id}"""

    def test_update_user_name(self):
        """
        RISIKO: Kan ikke opdatere brugerdata via API.
        """
        # Given: En bruger i databasen
        client.post("/users", json={
            "first_name": "Rasmus",
            "last_name": "K",
            "address": "Vej",
            "street_number": 1,
            "password": "pass"
        })

        # When: Fornavnet opdateres via PUT
        response = client.put("/users/1", json={
            "first_name": "Peter"
        })

        # Then: Navnet er ændret
        assert response.status_code == 200
        assert response.json()["first_name"] == "Peter"

    def test_update_nonexistent_user_returns_404(self):
        """
        RISIKO: Stille fejl ved opdatering af manglende bruger.
        """
        # Given: En tom database
        # When: En ikke-eksisterende bruger forsøges opdateret
        response = client.put("/users/999", json={
            "first_name": "Ghost"
        })

        # Then: 404 returneres
        assert response.status_code == 404


# =============================================================================
# DELETE Tests
# =============================================================================

class TestDeleteEndpoint:
    """DELETE /users/{id}"""

    def test_delete_user(self):
        """
        RISIKO: Kan ikke slette brugere → GDPR overtrædelse.
        """
        # Given: En bruger i databasen
        client.post("/users", json={
            "first_name": "Rasmus",
            "last_name": "K",
            "address": "Vej",
            "street_number": 1,
            "password": "pass"
        })

        # When: Brugeren slettes
        response = client.delete("/users/1")

        # Then: Sletning bekræftes og brugeren er væk
        assert response.status_code == 200
        assert client.get("/users/1").status_code == 404

    def test_delete_nonexistent_user_returns_404(self):
        """
        RISIKO: Stille sletning af manglende bruger.
        """
        # Given: En tom database
        # When: En ikke-eksisterende bruger forsøges slettet
        response = client.delete("/users/999")

        # Then: 404 returneres
        assert response.status_code == 404


# =============================================================================
# LIST Tests
# =============================================================================

class TestListEndpoint:
    """GET /users"""

    def test_list_empty(self):
        """
        RISIKO: Tomt resultat håndteres ikke korrekt.
        """
        # Given: En tom database
        # When: Alle brugere forespørges
        response = client.get("/users")

        # Then: En tom liste returneres
        assert response.status_code == 200
        assert response.json() == []

    def test_list_multiple_users(self):
        """
        RISIKO: Ikke alle brugere returneres.
        """
        # Given: To brugere i databasen
        client.post("/users", json={
            "first_name": "Alice",
            "last_name": "A",
            "address": "V1",
            "street_number": 1,
            "password": "p1"
        })
        client.post("/users", json={
            "first_name": "Bob",
            "last_name": "B",
            "address": "V2",
            "street_number": 2,
            "password": "p2"
        })

        # When: Alle brugere forespørges
        response = client.get("/users")

        # Then: Begge brugere returneres
        assert response.status_code == 200
        assert len(response.json()) == 2
