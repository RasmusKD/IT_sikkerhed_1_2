"""
Auth REST API - Authorization med JWT Security Tokens.

Endpoints:
  POST /register        → Registrer ny bruger
  POST /token           → Login og få JWT token
  POST /change-password → Skift password (kræver token)
  POST /deactivate      → Deaktiver konto (sig selv eller admin)
  POST /activate        → Reaktiver konto (kun admin)

Kør med:
  uvicorn auth_api:app --reload

Swagger docs:
  http://127.0.0.1:8000/docs
"""
import json
import os
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import List, Optional
from enum import Enum

from auth_service import AuthService


# =============================================================================
# Models
# =============================================================================

class Role(str, Enum):
    user = "user"
    admin = "admin"


class RegisterRequest(BaseModel):
    username: str
    password: str
    first_name: str
    last_name: str
    roles: List[Role] = [Role.user]


class LoginRequest(BaseModel):
    username: str
    password: str


class UserActionRequest(BaseModel):
    username: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


# =============================================================================
# App
# =============================================================================

app = FastAPI(
    title="Auth API",
    description="Authorization REST API med JWT security tokens",
    version="1.0.0"
)

DB_FILE = "auth_users.json"
auth = AuthService()
user_db: dict = {}


# =============================================================================
# Database helpers
# =============================================================================

def _load_db():
    """Indlæs brugerdatabase fra JSON fil."""
    global user_db
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            user_db = json.load(f)
    else:
        # Opret default admin bruger
        _create_default_admin()


def _save_db():
    """Gem brugerdatabase til JSON fil."""
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(user_db, f, indent=2, ensure_ascii=False)


def _create_default_admin():
    """Opret standard admin bruger med admin/admin."""
    global user_db
    user_db["admin"] = {
        "username": "admin",
        "password": auth.hash_password("admin"),
        "first_name": auth.encrypt_data("Admin"),
        "last_name": auth.encrypt_data("User"),
        "active": True,
        "roles": ["admin"]
    }
    _save_db()
    print("✅ Default admin bruger oprettet (username: admin, password: admin)")


# Indlæs database ved opstart
_load_db()


# =============================================================================
# Endpoints
# =============================================================================

@app.post("/register", status_code=201)
def register_user(request: RegisterRequest):
    """Registrer ny bruger."""
    if request.username in user_db:
        raise HTTPException(status_code=400, detail="Brugernavn eksisterer allerede")

    user_db[request.username] = {
        "username": request.username,
        "password": auth.hash_password(request.password),
        "first_name": auth.encrypt_data(request.first_name),
        "last_name": auth.encrypt_data(request.last_name),
        "active": True,
        "roles": [r.value for r in request.roles]
    }
    _save_db()
    return {"status": f"Bruger '{request.username}' oprettet"}


@app.post("/token")
def get_token(request: LoginRequest):
    """Login og få JWT Bearer token."""
    user = user_db.get(request.username)
    if not user:
        raise HTTPException(status_code=401, detail="Forkert brugernavn eller password")

    if not user["active"]:
        raise HTTPException(status_code=403, detail="Konto er deaktiveret")

    if not auth.verify_password(request.password, user["password"]):
        raise HTTPException(status_code=401, detail="Forkert brugernavn eller password")

    token = auth.create_token(user["username"], user["roles"])
    return {"token": token}


@app.post("/change-password")
def change_password(request: ChangePasswordRequest, token: str = Header(...)):
    """Skift password. Kræver gyldig token."""
    payload = auth.verify_token(token)
    username = payload["sub"]
    user = user_db.get(username)

    if not user:
        raise HTTPException(status_code=404, detail="Bruger ikke fundet")

    if not auth.verify_password(request.old_password, user["password"]):
        raise HTTPException(status_code=401, detail="Forkert nuværende password")

    user_db[username]["password"] = auth.hash_password(request.new_password)
    _save_db()
    return {"status": "Password ændret"}


@app.post("/deactivate")
def deactivate_user(request: UserActionRequest, token: str = Header(...)):
    """Deaktiver bruger. Bruger kan deaktivere sig selv, admin kan deaktivere alle."""
    payload = auth.verify_token(token)
    caller = payload["sub"]
    caller_roles = payload["roles"]
    target = request.username

    # Tjek rettigheder: admin kan deaktivere alle, bruger kun sig selv
    if "admin" not in caller_roles and caller != target:
        raise HTTPException(status_code=403, detail="Kun admin kan deaktivere andre brugere")

    if target not in user_db:
        raise HTTPException(status_code=404, detail=f"Bruger '{target}' ikke fundet")

    user_db[target]["active"] = False
    _save_db()
    return {"status": f"Bruger '{target}' er deaktiveret"}


@app.post("/activate")
def activate_user(request: UserActionRequest, token: str = Header(...)):
    """Reaktiver bruger. Kun admin."""
    payload = auth.verify_token(token)
    caller_roles = payload["roles"]

    if "admin" not in caller_roles:
        raise HTTPException(status_code=403, detail="Kun admin kan reaktivere brugere")

    if request.username not in user_db:
        raise HTTPException(status_code=404, detail=f"Bruger '{request.username}' ikke fundet")

    user_db[request.username]["active"] = True
    _save_db()
    return {"status": f"Bruger '{request.username}' er reaktiveret"}
