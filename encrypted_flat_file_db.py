"""
Flat File Database med Kryptering + Hashing

Krypterings-valg:
  - AES-128 via Fernet (symmetrisk) → til persondata (fornavn, efternavn, adresse, etc.)
  - SHA-256 (hashing) → til passwords (envejs, kan ikke dekrypteres)

Hvorfor disse valg:
  - Fernet/AES: Industristandard, GDPR-kompatibel, understøtter dekryptering
  - SHA-256: Envejs-hash, sikrer at passwords aldrig kan læses i klartekst
  - Vi valgte Fernet (AES-128-CBC) over AES-256 da det er simplere og stadig sikkert
  - Vi valgte SHA-256 over bcrypt for simplicitet (bcrypt er bedre til produktion)
"""
import json
import os
import hashlib
from cryptography.fernet import Fernet


# Felter der indeholder persondata og SKAL krypteres (GDPR)
ENCRYPTED_FIELDS = ["first_name", "last_name", "address", "email", "telefon"]


class EncryptedFlatFileDB:
    """Flat file database med kryptering af persondata og hashing af passwords."""
    
    def __init__(self, filepath="encrypted_users.json", key=None):
        self.filepath = filepath
        
        # Generér eller brug eksisterende nøgle
        if key:
            self.key = key
        else:
            keyfile = filepath.replace(".json", ".key")
            if os.path.exists(keyfile):
                with open(keyfile, "rb") as f:
                    self.key = f.read()
            else:
                self.key = Fernet.generate_key()
                with open(keyfile, "wb") as f:
                    f.write(self.key)
        
        self.cipher = Fernet(self.key)
        self._load()
    
    def _load(self):
        """Indlæs krypteret data fra JSON-fil."""
        if os.path.exists(self.filepath):
            with open(self.filepath, "r", encoding="utf-8") as f:
                self.data = json.load(f)
        else:
            self.data = []
    
    def _save(self):
        """Gem krypteret data til JSON-fil."""
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
    
    # =========================================================================
    # Kryptering + Hashing
    # =========================================================================
    
    def _encrypt(self, plaintext):
        """Kryptér data med Fernet (AES-128).
        
        HVORNÅR: Når persondata gemmes i databasen.
        HVORFOR: GDPR kræver beskyttelse af persondata at rest.
        """
        return self.cipher.encrypt(plaintext.encode()).decode()
    
    def _decrypt(self, ciphertext):
        """Dekryptér data med Fernet.
        
        HVORNÅR: Kun når data skal vises til autoriseret bruger.
        HVORFOR: Data skal kun eksistere i klartekst når det aktivt bruges.
        """
        return self.cipher.decrypt(ciphertext.encode()).decode()
    
    def _hash_password(self, password):
        """Hash password med SHA-256.
        
        HVORNÅR: Når password oprettes eller ændres.
        HVORFOR: Passwords skal ALDRIG kunne læses - kun verificeres.
        """
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _clear_from_memory(self, data_dict):
        """Fjern dekrypteret data fra hukommelsen.
        
        HVORNÅR: Når dekrypteret data ikke længere er nødvendig.
        HVORFOR: Minimerer risikoen for at klartekst-data lækker via memory dumps.
        """
        for key in list(data_dict.keys()):
            if isinstance(data_dict[key], str):
                data_dict[key] = None
        data_dict.clear()
    
    def _next_id(self):
        """Generér næste kunde_id."""
        if not self.data:
            return 1
        return max(user["kunde_id"] for user in self.data) + 1
    
    # =========================================================================
    # CRUD med kryptering
    # =========================================================================
    
    def create(self, first_name, last_name, address, email, telefon, password):
        """Opret bruger - persondata krypteres, password hashes."""
        user = {
            "kunde_id": self._next_id(),
            "first_name": self._encrypt(first_name),
            "last_name": self._encrypt(last_name),
            "address": self._encrypt(address),
            "email": self._encrypt(email),
            "telefon": self._encrypt(telefon),
            "password": self._hash_password(password),
        }
        self.data.append(user)
        self._save()
        return user
    
    def read(self, kunde_id, decrypt=False):
        """Læs bruger - dekryptér kun hvis nødvendigt."""
        for user in self.data:
            if user["kunde_id"] == kunde_id:
                if decrypt:
                    return self._decrypt_user(user)
                return user.copy()
        return None
    
    def _decrypt_user(self, user):
        """Dekryptér alle persondata-felter for en bruger."""
        decrypted = user.copy()
        for field in ENCRYPTED_FIELDS:
            if field in decrypted and decrypted[field]:
                decrypted[field] = self._decrypt(decrypted[field])
        return decrypted
    
    def update(self, kunde_id, **kwargs):
        """Opdater bruger - re-kryptér ændrede felter."""
        user = None
        for u in self.data:
            if u["kunde_id"] == kunde_id:
                user = u
                break
        
        if user is None:
            raise ValueError(f"Bruger med id {kunde_id} findes ikke")
        
        for key, value in kwargs.items():
            if key == "kunde_id":
                raise ValueError("Kan ikke ændre kunde_id")
            elif key == "password":
                user[key] = self._hash_password(value)
            elif key in ENCRYPTED_FIELDS:
                user[key] = self._encrypt(value)
            elif key in user:
                user[key] = value
            else:
                raise ValueError(f"Ugyldigt felt: {key}")
        
        self._save()
        return user
    
    def delete(self, kunde_id):
        """Slet bruger - fjern al data (GDPR ret til sletning)."""
        for i, user in enumerate(self.data):
            if user["kunde_id"] == kunde_id:
                self.data.pop(i)
                self._save()
                return True
        raise ValueError(f"Bruger med id {kunde_id} findes ikke")
    
    def list_all(self, decrypt=False):
        """List alle brugere."""
        if decrypt:
            return [self._decrypt_user(u) for u in self.data]
        return [u.copy() for u in self.data]
    
    def verify_password(self, kunde_id, password):
        """Verificér password uden at dekryptere persondata."""
        user = self.read(kunde_id)
        if user is None:
            return False
        return user["password"] == self._hash_password(password)
    
    def count(self):
        """Returnér antal brugere."""
        return len(self.data)
