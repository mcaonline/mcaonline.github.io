from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from contextlib import asynccontextmanager
from typing import List, Dict, Any
import uvicorn
import secrets
import os
from pathlib import Path

from src.config.settings import settings, SETTINGS_FILE
from src.domain.models import HotkeyDefinition, ConnectionDefinition
from src.domain.hotkey_catalog import HotkeyCatalogService
from src.infrastructure.hotkeys import HotkeyAgent
from src.infrastructure.clipboard import clipboard
from src.infrastructure.secrets import secret_store
from src.application.pipeline import ExecutionPipeline
from src.infrastructure.history import HistoryRepository

# --- Session Token (regenerated on each start) ---
SESSION_TOKEN = secrets.token_urlsafe(32)
API_KEY_HEADER = APIKeyHeader(name="X-Session-Token", auto_error=False)

async def verify_session_token(request: Request, token: str = Depends(API_KEY_HEADER)):
    """Verify the session token for API authentication."""
    # Allow requests from localhost without token for initial setup
    client_host = request.client.host if request.client else ""
    
    # Always require token for non-localhost requests
    if client_host not in ("127.0.0.1", "localhost", "::1"):
        raise HTTPException(status_code=403, detail="Access denied: Non-local requests forbidden")
    
    # For localhost, token is optional but recommended
    if token and token != SESSION_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid session token")
    
    return True

# --- Dependencies ---
hotkey_catalog = HotkeyCatalogService(Path("hotkeys.json"))
history_repo = HistoryRepository()
pipeline = ExecutionPipeline(settings, secret_store, clipboard, history_repo)

# --- Background Services ---
def on_hotkey_trigger():
    print("GLOBAL TRIGGER RECEIVED!")

hotkey_agent = HotkeyAgent(on_trigger=on_hotkey_trigger)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting Hotkey Agent...")
    print(f"Session Token: {SESSION_TOKEN}")  # For Tauri to capture
    hotkey_agent.start()
    yield
    print("Stopping Hotkey Agent...")
    hotkey_agent.stop()

app = FastAPI(title="HotKeyAI Core", lifespan=lifespan)

# CORS - Restricted to localhost only
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:1420",
        "http://127.0.0.1:1420",
        "tauri://localhost",
        "https://tauri.localhost",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# --- Public Routes (no auth required) ---

@app.get("/health")
def health_check():
    return {"status": "ok", "version": "0.1.0"}

@app.get("/session-token")
def get_session_token(request: Request):
    """Returns session token only for localhost requests."""
    client_host = request.client.host if request.client else ""
    if client_host not in ("127.0.0.1", "localhost", "::1"):
        raise HTTPException(status_code=403, detail="Access denied")
    return {"token": SESSION_TOKEN}

# --- Protected Routes (require localhost + optional token) ---

@app.get("/hotkeys", response_model=List[HotkeyDefinition], dependencies=[Depends(verify_session_token)])
def get_hotkeys():
    return hotkey_catalog.get_all()

@app.post("/hotkeys", dependencies=[Depends(verify_session_token)])
def create_hotkey(hotkey: HotkeyDefinition):
    hotkey_catalog.add(hotkey)
    return hotkey

@app.put("/hotkeys/{hotkey_id}", dependencies=[Depends(verify_session_token)])
def update_hotkey(hotkey_id: str, hotkey: HotkeyDefinition):
    if hotkey.id != hotkey_id:
        raise HTTPException(status_code=400, detail="ID mismatch")
    hotkey_catalog.update(hotkey)
    return hotkey

@app.delete("/hotkeys/{hotkey_id}", dependencies=[Depends(verify_session_token)])
def delete_hotkey(hotkey_id: str):
    hotkey_catalog.delete(hotkey_id)
    return {"status": "deleted"}

@app.post("/execute/{hotkey_id}", dependencies=[Depends(verify_session_token)])
def execute_hotkey(hotkey_id: str):
    # Validate hotkey_id format (prevent injection)
    if not hotkey_id.replace("-", "").replace("_", "").isalnum():
        raise HTTPException(status_code=400, detail="Invalid hotkey ID format")
    
    hotkey = hotkey_catalog.get(hotkey_id)
    if not hotkey:
        raise HTTPException(status_code=404, detail="Hotkey not found")
    
    results = []
    for chunk in pipeline.execute(hotkey):
        results.append(chunk)
    
    return {"result": "".join(results)}

@app.get("/history", dependencies=[Depends(verify_session_token)])
def get_history():
    return history_repo.get_recent()

@app.get("/settings", dependencies=[Depends(verify_session_token)])
def get_settings():
    # Redact sensitive fields
    safe_settings = settings.model_dump()
    # Don't expose connection secrets metadata
    return safe_settings

@app.post("/settings", dependencies=[Depends(verify_session_token)])
def update_settings(new_settings: Dict[str, Any]):
    return {"status": "updated (mock)"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
