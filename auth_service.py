"""
Auth Service - Håndterer password hashing, kryptering og JWT tokens.

Secrets:
  - HASH_KEY: Bruges til HMAC password hashing (fra .env eller environment)
  - ENCRYPTION_KEY: Fernet nøgle til kryptering af PII (fra .env eller environment)

Sikkerhed:
  - Test secrets ligger i .env (committed til git)
  - Produktion secrets skal ligge i environment variables (IKKE i git)
"""
import hashlib
import hmac
import os
import base64
import datetime
import jwt
from cryptography.fernet import Fernet
from dotenv import load_dotenv
from fastapi import HTTPException


class AuthService:
    """Håndterer authentication: hashing, kryptering og JWT tokens."""

    def __init__(self):
        # Indlæs secrets fra .env hvis ikke allerede sat
        if os.getenv("HASH_KEY") is None:
            load_dotenv()

        env_name = os.getenv("ENVIRONMENT_NAME", "unknown")
        if env_name == "test":
            print(f"⚠️  ADVARSEL: Kører med TEST secrets fra .env fil ({env_name})")

        self._secret = os.getenv("HASH_KEY")
        if self._secret is None:
            raise ValueError("HASH_KEY ikke fundet i environment eller .env fil")
        self._secret = self._secret.encode()

        encryption_key = os.getenv("ENCRYPTION_KEY")
        if encryption_key is None:
            raise ValueError("ENCRYPTION_KEY ikke fundet i environment eller .env fil")
        self._fernet = Fernet(encryption_key)

        self._algorithm = "HS256"

    # =========================================================================
    # Password Hashing (HMAC + salt)
    # =========================================================================

    def hash_password(self, password: str) -> str:
        """Hash password med HMAC-SHA256 + tilfældigt salt."""
        salt = os.urandom(16)
        hashed = hmac.new(self._secret, salt + password.encode(), hashlib.sha256).digest()
        return base64.b64encode(salt + hashed).decode()

    def verify_password(self, password: str, stored_hash: str) -> bool:
        """Verificér password mod gemt hash."""
        data = base64.b64decode(stored_hash.encode())
        salt = data[:16]
        stored_hmac = data[16:]
        new_hmac = hmac.new(self._secret, salt + password.encode(), hashlib.sha256).digest()
        return hmac.compare_digest(stored_hmac, new_hmac)

    # =========================================================================
    # PII Kryptering (Fernet/AES)
    # =========================================================================

    def encrypt_data(self, plaintext: str) -> str:
        """Kryptér persondata med Fernet."""
        return self._fernet.encrypt(plaintext.encode()).decode()

    def decrypt_data(self, token: str) -> str:
        """Dekryptér persondata."""
        return self._fernet.decrypt(token.encode()).decode()

    # =========================================================================
    # JWT Tokens
    # =========================================================================

    def create_token(self, username: str, roles: list) -> str:
        """Generér JWT Bearer token med 1 times udløb."""
        payload = {
            "sub": username,
            "roles": roles,
            "exp": datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=1),
            "iat": datetime.datetime.now(datetime.UTC),
        }
        token = jwt.encode(payload, self._secret, algorithm=self._algorithm)
        return f"Bearer {token}"

    def verify_token(self, token: str) -> dict:
        """Verificér og dekod JWT token."""
        if not token.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Ugyldig token format")

        token_data = token.split(" ", 1)[1]
        try:
            payload = jwt.decode(token_data, self._secret, algorithms=[self._algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token udløbet")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Ugyldig token")
