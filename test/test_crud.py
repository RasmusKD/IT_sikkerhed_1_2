"""
CRUD(L) Test
IT-sikkerhed eksempel: Bruger håndtering

CRUD = Create, Read, Update, Delete (+ List)
Tester grundlæggende operationer på en bruger-database.
"""
import pytest


# Simpel in-memory bruger database til test
class UserDatabase:
    def __init__(self):
        self.users = {}
    
    def create(self, user_id, data):
        """Create: Opret ny bruger."""
        if user_id in self.users:
            raise ValueError("Bruger eksisterer allerede")
        self.users[user_id] = data
        return True
    
    def read(self, user_id):
        """Read: Læs bruger data."""
        if user_id not in self.users:
            return None
        return self.users[user_id]
    
    def update(self, user_id, data):
        """Update: Opdater bruger data."""
        if user_id not in self.users:
            raise ValueError("Bruger findes ikke")
        self.users[user_id] = data
        return True
    
    def delete(self, user_id):
        """Delete: Slet bruger."""
        if user_id not in self.users:
            raise ValueError("Bruger findes ikke")
        del self.users[user_id]
        return True
    
    def list_all(self):
        """List: Returnér alle brugere."""
        return list(self.users.keys())


@pytest.fixture
def db():
    """Fixture: Frisk database til hver test."""
    return UserDatabase()


class TestCRUDL:
    """CRUD(L) tests for bruger database."""
    
    def test_create_user(self, db):
        """C - Create: Kan oprette ny bruger."""
        result = db.create("user1", {"name": "Rasmus", "role": "admin"})
        assert result == True
        assert "user1" in db.users
    
    def test_create_duplicate_fails(self, db):
        """C - Create: Duplikat bruger fejler."""
        db.create("user1", {"name": "Rasmus"})
        with pytest.raises(ValueError):
            db.create("user1", {"name": "Anden"})
    
    def test_read_user(self, db):
        """R - Read: Kan læse bruger data."""
        db.create("user1", {"name": "Rasmus"})
        data = db.read("user1")
        assert data["name"] == "Rasmus"
    
    def test_read_nonexistent_returns_none(self, db):
        """R - Read: Ikke-eksisterende bruger returnerer None."""
        assert db.read("ghost") is None
    
    def test_update_user(self, db):
        """U - Update: Kan opdatere bruger."""
        db.create("user1", {"name": "Rasmus"})
        db.update("user1", {"name": "Rasmus K", "role": "superadmin"})
        assert db.read("user1")["role"] == "superadmin"
    
    def test_delete_user(self, db):
        """D - Delete: Kan slette bruger."""
        db.create("user1", {"name": "Rasmus"})
        db.delete("user1")
        assert db.read("user1") is None
    
    def test_list_users(self, db):
        """L - List: Kan liste alle brugere."""
        db.create("user1", {"name": "Rasmus"})
        db.create("user2", {"name": "Peter"})
        users = db.list_all()
        assert len(users) == 2
        assert "user1" in users
        assert "user2" in users
