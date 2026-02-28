"""
Notes Microservice - Simpel note-tjeneste med Auth API integration.

Alle endpoints kraever et gyldigt JWT token fra Auth API'et.

Endpoints:
  GET  /notes       -> Hent egne noter
  POST /notes       -> Opret ny note
  DELETE /notes/{id} -> Slet egen note

Koer med:
  uvicorn notes_api:app --reload --port 8001

Swagger docs:
  http://127.0.0.1:8001/docs
"""
import json
import os
import uuid
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import Optional

from auth_service import AuthService


# =============================================================================
# Models
# =============================================================================

class CreateNoteRequest(BaseModel):
    title: str
    content: str


# =============================================================================
# App
# =============================================================================

app = FastAPI(
    title="Notes Microservice",
    description="Note-tjeneste der kraever authentication via Auth API",
    version="1.0.0"
)

auth = AuthService()

DB_FILE = "notes_db.json"
notes_db = {}


def _load_db():
    """Indlaes noter fra JSON fil."""
    global notes_db
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            notes_db = json.load(f)


def _save_db():
    """Gem noter til JSON fil."""
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(notes_db, f, indent=2, ensure_ascii=False)


# Indlaes ved opstart
_load_db()


def _verify_user(token: str) -> str:
    """Verificer token og returner username. Kaster 401 hvis ugyldig."""
    payload = auth.verify_token(token)
    return payload["sub"]


# =============================================================================
# Endpoints
# =============================================================================

@app.get("/notes")
def get_notes(token: str = Header(...)):
    """Hent alle noter for den loggede bruger."""
    username = _verify_user(token)

    user_notes = []
    for note_id, note in notes_db.items():
        if note["owner"] == username:
            user_notes.append({"id": note_id, **note})

    return {"notes": user_notes, "count": len(user_notes)}


@app.post("/notes", status_code=201)
def create_note(request: CreateNoteRequest, token: str = Header(...)):
    """Opret en ny note. Title og content er paakraevet."""
    username = _verify_user(token)

    if not request.title.strip():
        raise HTTPException(status_code=400, detail="Title maa ikke vaere tom")

    if not request.content.strip():
        raise HTTPException(status_code=400, detail="Content maa ikke vaere tom")

    note_id = str(uuid.uuid4())[:8]
    notes_db[note_id] = {
        "title": request.title,
        "content": request.content,
        "owner": username
    }
    _save_db()

    return {"id": note_id, "status": "Note oprettet"}


@app.delete("/notes/{note_id}")
def delete_note(note_id: str, token: str = Header(...)):
    """Slet en note. Kun ejeren kan slette sin egen note."""
    username = _verify_user(token)

    if note_id not in notes_db:
        raise HTTPException(status_code=404, detail="Note ikke fundet")

    if notes_db[note_id]["owner"] != username:
        raise HTTPException(status_code=403, detail="Du kan kun slette dine egne noter")

    del notes_db[note_id]
    _save_db()

    return {"status": "Note slettet"}
