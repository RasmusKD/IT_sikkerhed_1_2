"""
Kryptering + Hashing - Unit Tests
Tester at persondata krypteres korrekt og passwords hashes.

RISIKO: Hvis disse tests fejler, kan persondata ligge i klartekst
i databasen, hvilket er en GDPR-overtrædelse og sikkerhedsbrist.
"""
import pytest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from encrypted_flat_file_db import EncryptedFlatFileDB, ENCRYPTED_FIELDS


TEST_DB = "test_encrypted.json"
TEST_KEY_FILE = "test_encrypted.key"


@pytest.fixture
def db():
    """Fixture: Frisk krypteret database til hver test."""
    for f in [TEST_DB, TEST_KEY_FILE]:
        if os.path.exists(f):
            os.remove(f)
    
    database = EncryptedFlatFileDB(TEST_DB)
    yield database
    
    for f in [TEST_DB, TEST_KEY_FILE]:
        if os.path.exists(f):
            os.remove(f)


# =============================================================================
# KRYPTERING Tests
# =============================================================================

class TestEncryption:
    """Tester at persondata krypteres korrekt."""
    
    def test_data_is_encrypted_in_storage(self, db):
        """
        RISIKO: Persondata i klartekst → GDPR overtrædelse.
        """
        # Given: En tom database
        # When: En bruger oprettes
        db.create("Rasmus", "K", "Hovedgaden 1", "rasmus@test.dk", "12345678", "pass")
        
        # Then: Data i filen er krypteret (ikke læsbar)
        raw_user = db.data[0]
        assert raw_user["first_name"] != "Rasmus"
        assert raw_user["last_name"] != "K"
        assert raw_user["address"] != "Hovedgaden 1"
        assert raw_user["email"] != "rasmus@test.dk"
        assert raw_user["telefon"] != "12345678"
    
    def test_data_can_be_decrypted(self, db):
        """
        RISIKO: Kan ikke dekryptere → data er ubrugeligt.
        """
        # Given: En krypteret bruger i databasen
        db.create("Rasmus", "K", "Hovedgaden 1", "rasmus@test.dk", "12345678", "pass")
        
        # When: Data læses med dekryptering
        user = db.read(1, decrypt=True)
        
        # Then: Klartekst data returneres
        assert user["first_name"] == "Rasmus"
        assert user["last_name"] == "K"
        assert user["email"] == "rasmus@test.dk"
    
    def test_read_without_decrypt_returns_ciphertext(self, db):
        """
        RISIKO: Data dekrypteres uden grund → unødvendig eksponering.
        """
        # Given: En krypteret bruger
        db.create("Rasmus", "K", "Vej 1", "r@test.dk", "11111111", "pass")
        
        # When: Data læses UDEN dekryptering
        user = db.read(1, decrypt=False)
        
        # Then: Data er stadig krypteret
        assert user["first_name"] != "Rasmus"
    
    def test_all_pii_fields_are_encrypted(self, db):
        """
        RISIKO: Nogle felter gemt i klartekst → delvis GDPR overtrædelse.
        """
        # Given: En bruger med alle felter
        db.create("Alice", "Jensen", "Storgade 5", "alice@mail.dk", "87654321", "secret")
        
        # When: Rå data tjekkes
        raw = db.data[0]
        
        # Then: Alle PII felter er krypteret
        for field in ENCRYPTED_FIELDS:
            if field in raw:
                assert raw[field] != {"first_name": "Alice", "last_name": "Jensen",
                    "address": "Storgade 5", "email": "alice@mail.dk",
                    "telefon": "87654321"}[field], f"{field} er ikke krypteret!"
    
    def test_kunde_id_is_not_encrypted(self, db):
        """
        RISIKO: Krypteret ID → kan ikke finde brugere.
        """
        # Given: En bruger
        db.create("Test", "User", "Vej", "t@t.dk", "11111111", "pass")
        
        # When: Rå data tjekkes
        raw = db.data[0]
        
        # Then: kunde_id er et normalt tal
        assert isinstance(raw["kunde_id"], int)
        assert raw["kunde_id"] == 1


# =============================================================================
# HASHING Tests
# =============================================================================

class TestHashing:
    """Tester at passwords hashes korrekt."""
    
    def test_password_is_hashed_not_encrypted(self, db):
        """
        RISIKO: Password krypteret i stedet for hashed → kan dekrypteres.
        """
        # Given: En bruger med password
        db.create("Test", "User", "Vej", "t@t.dk", "11111111", "hemmeligt")
        
        # When: Password tjekkes i databasen
        raw = db.data[0]
        
        # Then: Password er en SHA-256 hash (64 tegn hex)
        assert raw["password"] != "hemmeligt"
        assert len(raw["password"]) == 64
    
    def test_verify_correct_password(self, db):
        """
        RISIKO: Korrekt password afvises → brugere låst ude.
        """
        # Given: En bruger med password "secret"
        db.create("Test", "User", "Vej", "t@t.dk", "11111111", "secret")
        
        # When: Der verificeres med korrekt password
        result = db.verify_password(1, "secret")
        
        # Then: Verificering lykkes
        assert result == True
    
    def test_verify_wrong_password(self, db):
        """
        RISIKO: Forkert password accepteres → uautoriseret adgang.
        """
        # Given: En bruger med password "secret"
        db.create("Test", "User", "Vej", "t@t.dk", "11111111", "secret")
        
        # When: Der verificeres med forkert password
        result = db.verify_password(1, "forkert")
        
        # Then: Verificering fejler
        assert result == False
    
    def test_same_password_same_hash(self, db):
        """
        RISIKO: Inkonsistent hashing → kan ikke logge ind.
        """
        # Given: To brugere med SAMME password
        db.create("A", "A", "V1", "a@a.dk", "11111111", "same_pass")
        db.create("B", "B", "V2", "b@b.dk", "22222222", "same_pass")
        
        # When: Password hashes sammenlignes
        hash1 = db.data[0]["password"]
        hash2 = db.data[1]["password"]
        
        # Then: Samme password giver samme hash
        assert hash1 == hash2


# =============================================================================
# MEMORY CLEARING Tests
# =============================================================================

class TestMemoryClearing:
    """Tester at dekrypteret data fjernes fra hukommelsen."""
    
    def test_clear_from_memory(self, db):
        """
        RISIKO: Klartekst data i hukommelsen → kan lækkes via memory dump.
        """
        # Given: Dekrypteret brugerdata
        decrypted = {"first_name": "Rasmus", "email": "rasmus@test.dk"}
        
        # When: Hukommelsen ryddes
        db._clear_from_memory(decrypted)
        
        # Then: Data er fjernet
        assert len(decrypted) == 0


# =============================================================================
# CRUD MED KRYPTERING Tests
# =============================================================================

class TestEncryptedCRUD:
    """Tester CRUD operationer med kryptering."""
    
    def test_create_and_read_roundtrip(self, db):
        """
        RISIKO: Data korrupt efter kryptering/dekryptering → datatab.
        """
        # Given: Originale brugerdata
        original = ("Rasmus", "K", "Hovedgaden 1", "rasmus@test.dk", "12345678")
        
        # When: Brugeren oprettes og læses
        db.create(*original, "pass")
        user = db.read(1, decrypt=True)
        
        # Then: Dekrypteret data matcher originalen
        assert user["first_name"] == "Rasmus"
        assert user["last_name"] == "K"
        assert user["address"] == "Hovedgaden 1"
        assert user["email"] == "rasmus@test.dk"
        assert user["telefon"] == "12345678"
    
    def test_update_re_encrypts_data(self, db):
        """
        RISIKO: Opdateret data ikke re-krypteret → klartekst efter update.
        """
        # Given: En krypteret bruger
        db.create("Rasmus", "K", "Vej 1", "r@t.dk", "11111111", "pass")
        
        # When: Navnet opdateres
        db.update(1, first_name="Peter")
        
        # Then: Nyt navn er krypteret i storage men dekrypteres korrekt
        raw = db.data[0]
        assert raw["first_name"] != "Peter"  # Krypteret i filen
        
        user = db.read(1, decrypt=True)
        assert user["first_name"] == "Peter"  # Dekrypterer korrekt
    
    def test_delete_removes_all_data(self, db):
        """
        RISIKO: Slettet brugers data stadig i filen → GDPR overtrædelse.
        """
        # Given: En bruger i databasen
        db.create("Rasmus", "K", "Vej", "r@t.dk", "11111111", "pass")
        assert db.count() == 1
        
        # When: Brugeren slettes
        db.delete(1)
        
        # Then: Ingen data tilbage
        assert db.count() == 0
    
    def test_data_persists_encrypted(self, db):
        """
        RISIKO: Data tabt eller dekrypteret ved genindlæsning.
        """
        # Given: En krypteret bruger
        db.create("Rasmus", "K", "Vej", "r@t.dk", "11111111", "pass")
        
        # When: Databasen genindlæses med samme nøgle
        db2 = EncryptedFlatFileDB(TEST_DB, key=db.key)
        
        # Then: Data kan stadig dekrypteres
        user = db2.read(1, decrypt=True)
        assert user["first_name"] == "Rasmus"
    
    def test_list_all_decrypted(self, db):
        """
        RISIKO: Liste viser krypteret data → ubrugelig til admin.
        """
        # Given: To brugere
        db.create("Alice", "A", "V1", "a@a.dk", "11111111", "p1")
        db.create("Bob", "B", "V2", "b@b.dk", "22222222", "p2")
        
        # When: Alle brugere listes med dekryptering
        users = db.list_all(decrypt=True)
        
        # Then: Alle navne er i klartekst
        assert users[0]["first_name"] == "Alice"
        assert users[1]["first_name"] == "Bob"
