"""
Flat File Database - JSON-baseret brugerdatabase.

Gemmer brugerdata i en JSON-fil i stedet for en traditionel database.
Understøtter CRUD operationer (Create, Read, Update, Delete) + List og Search.
"""
import json
import os
import hashlib


class FlatFileDB:
    """JSON-baseret flat file database til brugerhåndtering."""
    
    def __init__(self, filepath="users.json"):
        self.filepath = filepath
        self._load()
    
    def _load(self):
        """Indlæs data fra JSON-fil."""
        if os.path.exists(self.filepath):
            with open(self.filepath, "r", encoding="utf-8") as f:
                self.data = json.load(f)
        else:
            self.data = []
    
    def _save(self):
        """Gem data til JSON-fil."""
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
    
    def _hash_password(self, password):
        """Hash password med SHA-256 for sikkerhed."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _next_id(self):
        """Generér næste person_id."""
        if not self.data:
            return 1
        return max(user["person_id"] for user in self.data) + 1
    
    # =========================================================================
    # CRUD Operationer
    # =========================================================================
    
    def create(self, first_name, last_name, address, street_number, password, enabled=True):
        """Create: Opret ny bruger."""
        user = {
            "person_id": self._next_id(),
            "first_name": first_name,
            "last_name": last_name,
            "address": address,
            "street_number": street_number,
            "password": self._hash_password(password),
            "enabled": enabled
        }
        self.data.append(user)
        self._save()
        return user
    
    def read(self, person_id):
        """Read: Hent bruger efter person_id."""
        for user in self.data:
            if user["person_id"] == person_id:
                return user
        return None
    
    def update(self, person_id, **kwargs):
        """Update: Opdater brugerfelter."""
        # Tjek om nogen forsøger at ændre person_id
        if "person_id" in kwargs:
            raise ValueError("Kan ikke ændre person_id")
        
        user = self.read(person_id)
        if user is None:
            raise ValueError(f"Bruger med id {person_id} findes ikke")
        
        for key, value in kwargs.items():
            if key == "password":
                user[key] = self._hash_password(value)
            elif key in user:
                user[key] = value
            else:
                raise ValueError(f"Ugyldigt felt: {key}")
        
        self._save()
        return user

    
    def delete(self, person_id):
        """Delete: Slet bruger."""
        user = self.read(person_id)
        if user is None:
            raise ValueError(f"Bruger med id {person_id} findes ikke")
        self.data.remove(user)
        self._save()
        return True
    
    # =========================================================================
    # Ekstra funktioner
    # =========================================================================
    
    def list_all(self):
        """List: Returnér alle brugere."""
        return self.data
    
    def search(self, **kwargs):
        """Search: Søg brugere efter felter."""
        results = self.data
        for key, value in kwargs.items():
            results = [u for u in results if u.get(key) == value]
        return results
    
    def verify_password(self, person_id, password):
        """Verificér password for en bruger."""
        user = self.read(person_id)
        if user is None:
            return False
        return user["password"] == self._hash_password(password)
    
    def disable_user(self, person_id):
        """Deaktivér en bruger (sæt enabled=False)."""
        return self.update(person_id, enabled=False)
    
    def enable_user(self, person_id):
        """Aktivér en bruger (sæt enabled=True)."""
        return self.update(person_id, enabled=True)
    
    def count(self):
        """Returnér antal brugere."""
        return len(self.data)
