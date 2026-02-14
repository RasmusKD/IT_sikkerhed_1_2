"""
Flat File Database - Unit Tests
Tester CRUD operationer og ekstra funktioner med given/when/then kommentarer.

RISIKO: Hvis disse tests fejler, betyder det at databasen ikke kan
håndtere brugerdata korrekt - dette kan føre til datatab, korrupt data
eller sikkerhedsproblemer med passwords.
"""
import pytest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from flat_file_db import FlatFileDB


TEST_DB = "test_users.json"


@pytest.fixture
def db():
    """Fixture: Frisk database til hver test."""
    # Slet test-fil hvis den eksisterer
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    
    database = FlatFileDB(TEST_DB)
    yield database
    
    # Oprydning efter test
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


# =============================================================================
# CREATE Tests
# =============================================================================

class TestCreate:
    """Tests for Create operationen."""
    
    def test_create_user_successfully(self, db):
        """
        RISIKO: Kan ikke oprette brugere → systemet er ubrugeligt.
        """
        # Given: En tom database
        assert db.count() == 0
        
        # When: En ny bruger oprettes
        user = db.create("Rasmus", "K", "Hovedgaden", 42, "secret123")
        
        # Then: Brugeren er oprettet med korrekte data
        assert user["first_name"] == "Rasmus"
        assert user["last_name"] == "K"
        assert user["person_id"] == 1
        assert db.count() == 1
    
    def test_create_multiple_users_unique_ids(self, db):
        """
        RISIKO: Duplikerede IDs → kan overskrive brugerdata.
        """
        # Given: En tom database
        # When: Tre brugere oprettes
        user1 = db.create("Alice", "A", "Vej 1", 1, "pass1")
        user2 = db.create("Bob", "B", "Vej 2", 2, "pass2")
        user3 = db.create("Charlie", "C", "Vej 3", 3, "pass3")
        
        # Then: Alle har unikke IDs
        ids = [user1["person_id"], user2["person_id"], user3["person_id"]]
        assert len(set(ids)) == 3
        assert db.count() == 3
    
    def test_create_user_password_is_hashed(self, db):
        """
        RISIKO: Passwords gemt i klartekst → alvorlig sikkerhedsbrist.
        """
        # Given: En tom database
        # When: En bruger oprettes med password
        user = db.create("Test", "User", "Vej", 1, "hemmeligt123")
        
        # Then: Password er hashed, ikke i klartekst
        assert user["password"] != "hemmeligt123"
        assert len(user["password"]) == 64  # SHA-256 hash længde
    
    def test_create_user_enabled_by_default(self, db):
        """
        RISIKO: Bruger oprettet som disabled → kan ikke logge ind.
        """
        # Given: En tom database
        # When: En bruger oprettes uden at angive enabled
        user = db.create("Test", "User", "Vej", 1, "pass")
        
        # Then: Brugeren er enabled som standard
        assert user["enabled"] == True


# =============================================================================
# READ Tests
# =============================================================================

class TestRead:
    """Tests for Read operationen."""
    
    def test_read_existing_user(self, db):
        """
        RISIKO: Kan ikke læse brugerdata → ingen login mulig.
        """
        # Given: En database med én bruger
        created = db.create("Rasmus", "K", "Hovedgaden", 42, "pass")
        
        # When: Brugeren læses
        user = db.read(created["person_id"])
        
        # Then: Den rigtige bruger returneres
        assert user["first_name"] == "Rasmus"
        assert user["person_id"] == created["person_id"]
    
    def test_read_nonexistent_user_returns_none(self, db):
        """
        RISIKO: Crash ved manglende bruger → ustabilt system.
        """
        # Given: En tom database
        # When: En ikke-eksisterende bruger forsøges læst
        user = db.read(999)
        
        # Then: None returneres (ikke en fejl)
        assert user is None


# =============================================================================
# UPDATE Tests
# =============================================================================

class TestUpdate:
    """Tests for Update operationen."""
    
    def test_update_user_name(self, db):
        """
        RISIKO: Kan ikke opdatere → forkerte data permanent.
        """
        # Given: En bruger i databasen
        user = db.create("Rasmus", "K", "Vej", 1, "pass")
        
        # When: Fornavnet opdateres
        updated = db.update(user["person_id"], first_name="Peter")
        
        # Then: Navnet er ændret
        assert updated["first_name"] == "Peter"
        assert updated["last_name"] == "K"  # Uændret
    
    def test_update_nonexistent_user_fails(self, db):
        """
        RISIKO: Stille fejl → data korruption.
        """
        # Given: En tom database
        # When/Then: Opdatering af ikke-eksisterende bruger giver fejl
        with pytest.raises(ValueError):
            db.update(999, first_name="Ghost")
    
    def test_update_does_not_change_person_id(self, db):
        """
        RISIKO: Ændret ID → bruger mister adgang til sin konto.
        """
        # Given: En bruger i databasen
        user = db.create("Test", "User", "Vej", 1, "pass")
        original_id = user["person_id"]
        
        # When: Andre felter opdateres
        updated = db.update(original_id, first_name="Ny")
        
        # Then: person_id er uændret
        assert updated["person_id"] == original_id
    
    def test_update_password_is_rehashed(self, db):
        """
        RISIKO: Nyt password gemt i klartekst → sikkerhedsbrist.
        """
        # Given: En bruger med et password
        user = db.create("Test", "User", "Vej", 1, "gammelt_pass")
        old_hash = user["password"]
        
        # When: Passwordet opdateres
        updated = db.update(user["person_id"], password="nyt_pass")
        
        # Then: Password er hashed og forskellig fra det gamle
        assert updated["password"] != "nyt_pass"
        assert updated["password"] != old_hash


# =============================================================================
# DELETE Tests
# =============================================================================

class TestDelete:
    """Tests for Delete operationen."""
    
    def test_delete_user(self, db):
        """
        RISIKO: Kan ikke slette → GDPR overtrædelse.
        """
        # Given: En database med én bruger
        user = db.create("Rasmus", "K", "Vej", 1, "pass")
        
        # When: Brugeren slettes
        result = db.delete(user["person_id"])
        
        # Then: Brugeren er væk
        assert result == True
        assert db.read(user["person_id"]) is None
        assert db.count() == 0
    
    def test_delete_nonexistent_user_fails(self, db):
        """
        RISIKO: Stille sletning → uventet datatab.
        """
        # Given: En tom database
        # When/Then: Sletning af ikke-eksisterende bruger giver fejl
        with pytest.raises(ValueError):
            db.delete(999)


# =============================================================================
# EKSTRA FUNKTIONER Tests
# =============================================================================

class TestExtraFunctions:
    """Tests for ekstra funktioner (search, password, enable/disable)."""
    
    def test_search_by_last_name(self, db):
        """
        RISIKO: Søgning virker ikke → kan ikke finde brugere.
        """
        # Given: Tre brugere, to med samme efternavn
        db.create("Alice", "Jensen", "Vej 1", 1, "pass1")
        db.create("Bob", "Jensen", "Vej 2", 2, "pass2")
        db.create("Charlie", "Hansen", "Vej 3", 3, "pass3")
        
        # When: Der søges efter efternavn "Jensen"
        results = db.search(last_name="Jensen")
        
        # Then: To brugere returneres
        assert len(results) == 2
    
    def test_verify_correct_password(self, db):
        """
        RISIKO: Password verificering fejler → ingen kan logge ind.
        """
        # Given: En bruger med password "secret"
        user = db.create("Test", "User", "Vej", 1, "secret")
        
        # When: Der verificeres med korrekt password
        result = db.verify_password(user["person_id"], "secret")
        
        # Then: Verificering lykkes
        assert result == True
    
    def test_verify_wrong_password(self, db):
        """
        RISIKO: Forkert password giver adgang → sikkerhedsbrist.
        """
        # Given: En bruger med password "secret"
        user = db.create("Test", "User", "Vej", 1, "secret")
        
        # When: Der verificeres med forkert password
        result = db.verify_password(user["person_id"], "wrong")
        
        # Then: Verificering fejler
        assert result == False
    
    def test_disable_user(self, db):
        """
        RISIKO: Kan ikke deaktivere → kompromitterede konti forbliver aktive.
        """
        # Given: En aktiv bruger
        user = db.create("Test", "User", "Vej", 1, "pass")
        assert user["enabled"] == True
        
        # When: Brugeren deaktiveres
        db.disable_user(user["person_id"])
        
        # Then: Brugeren er deaktiveret
        assert db.read(user["person_id"])["enabled"] == False
    
    def test_enable_user(self, db):
        """
        RISIKO: Kan ikke genaktivere → brugere låst ude permanent.
        """
        # Given: En deaktiveret bruger
        user = db.create("Test", "User", "Vej", 1, "pass", enabled=False)
        
        # When: Brugeren aktiveres
        db.enable_user(user["person_id"])
        
        # Then: Brugeren er aktiv
        assert db.read(user["person_id"])["enabled"] == True
    
    def test_data_persists_after_reload(self, db):
        """
        RISIKO: Data tabt ved genindlæsning → alt data forsvinder.
        """
        # Given: En bruger i databasen
        db.create("Rasmus", "K", "Vej", 1, "pass")
        
        # When: Databasen åbnes igen (simulerer genstart)
        db2 = FlatFileDB(TEST_DB)
        
        # Then: Data er stadig der
        assert db2.count() == 1
        assert db2.read(1)["first_name"] == "Rasmus"
    
    def test_list_all_users(self, db):
        """
        RISIKO: Kan ikke liste brugere → ingen admin overblik.
        """
        # Given: Tre brugere i databasen
        db.create("Alice", "A", "Vej 1", 1, "pass1")
        db.create("Bob", "B", "Vej 2", 2, "pass2")
        db.create("Charlie", "C", "Vej 3", 3, "pass3")
        
        # When: Alle brugere hentes
        users = db.list_all()
        
        # Then: Tre brugere returneres
        assert len(users) == 3
