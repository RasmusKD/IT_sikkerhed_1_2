"""
REST API - FastAPI wrapper til Flat File Database.

Endpoints:
  POST   /users       → Create (opret bruger)
  GET    /users       → List (alle brugere)
  GET    /users/{id}  → Read (hent bruger)
  PUT    /users/{id}  → Update (opdater bruger)
  DELETE /users/{id}  → Delete (slet bruger)

Kør med:
  uvicorn api:app --reload

Swagger docs:
  http://127.0.0.1:8000/docs
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from flat_file_db import FlatFileDB


app = FastAPI(
    title="Flat File Database API",
    description="REST API til brugerhåndtering med JSON flat file database",
    version="1.0.0"
)

db = FlatFileDB("api_users.json")


# =============================================================================
# Pydantic Models (input validering)
# =============================================================================

class UserCreate(BaseModel):
    """Data til oprettelse af ny bruger."""
    first_name: str
    last_name: str
    address: str
    street_number: int
    password: str


class UserUpdate(BaseModel):
    """Data til opdatering af bruger (alle felter valgfrie)."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    address: Optional[str] = None
    street_number: Optional[int] = None
    password: Optional[str] = None


# =============================================================================
# CRUD Endpoints
# =============================================================================

@app.post("/users", status_code=201)
def create_user(user: UserCreate):
    """Create: Opret ny bruger."""
    created = db.create(
        user.first_name,
        user.last_name,
        user.address,
        user.street_number,
        user.password
    )
    return created


@app.get("/users")
def list_users():
    """List: Hent alle brugere."""
    return db.list_all()


@app.get("/users/{person_id}")
def read_user(person_id: int):
    """Read: Hent bruger efter ID."""
    user = db.read(person_id)
    if user is None:
        raise HTTPException(status_code=404, detail=f"Bruger {person_id} ikke fundet")
    return user


@app.put("/users/{person_id}")
def update_user(person_id: int, user: UserUpdate):
    """Update: Opdater brugerfelter."""
    # Byg kwargs fra felter der ikke er None
    updates = {k: v for k, v in user.model_dump().items() if v is not None}
    
    if not updates:
        raise HTTPException(status_code=400, detail="Ingen felter at opdatere")
    
    try:
        updated = db.update(person_id, **updates)
        return updated
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.delete("/users/{person_id}")
def delete_user(person_id: int):
    """Delete: Slet bruger."""
    try:
        db.delete(person_id)
        return {"message": f"Bruger {person_id} slettet"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
