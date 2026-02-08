from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from contextlib import asynccontextmanager
from typing import List, Dict, Any
import uvicorn
import secrets
import os
from pathlib import Path
from loguru import logger

from .config.settings import settings, SETTINGS_FILE
from .domain.models import HotkeyDefinition, ConnectionDefinition
from .domain.hotkey_catalog import HotkeyCatalogService
from .domain.ui_text import UiTextCatalog
from .infrastructure.hotkeys import HotkeyAgent
from .infrastructure.clipboard import clipboard
from .infrastructure.secrets import secret_store
from .application.pipeline import ExecutionPipeline
from .infrastructure.history import HistoryRepository

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
def on_hotkey_trigger(hotkey_id: Optional[str] = None):
    logger.debug(f"Hotkey trigger received: {hotkey_id}")
    # If hotkey_id is provided, execute it directly.
    # Otherwise, it's the panel trigger.
    if hotkey_id:
         # Execute directly (fire and forget in background)
         # We need to run inside an async context or similar if pipeline is async? 
         # Pipeline.execute is likely a generator. We should consume it.
         # For simplicity in this sync callback, we can just spawn another thread or run sync if pipeline allows.
         # Actually, better to just log for now and implement the actual execution logic.
         pass

hotkey_agent = HotkeyAgent(on_trigger=on_hotkey_trigger)

@asynccontextmanager
async def lifespan(app: FastAPI):
    pid = os.getpid()
    logger.info(f"[{pid}] LIFESPAN START")
    logger.info(f"[{pid}] Starting Hotkey Agent...")
    logger.info(f"[{pid}] Session Token: {SESSION_TOKEN}")
    hotkey_agent.update_hotkeys(hotkey_catalog.get_all())
    hotkey_agent.start()
    yield
    logger.info(f"[{pid}] LIFESPAN STOP")
    logger.info(f"[{pid}] Stopping Hotkey Agent...")
    hotkey_agent.stop()

app = FastAPI(title="Paste & Speech AI Core", lifespan=lifespan)

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

@app.get("/ui-text")
def get_ui_text():
    return UiTextCatalog._DEFAULTS

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
    hotkey_agent.update_hotkeys(hotkey_catalog.get_all())
    return hotkey

@app.put("/hotkeys/{hotkey_id}", dependencies=[Depends(verify_session_token)])
def update_hotkey(hotkey_id: str, hotkey: HotkeyDefinition):
    if hotkey.id != hotkey_id:
        raise HTTPException(status_code=400, detail="ID mismatch")
    hotkey_catalog.update(hotkey)
    hotkey_agent.update_hotkeys(hotkey_catalog.get_all())
    return hotkey

@app.delete("/hotkeys/{hotkey_id}", dependencies=[Depends(verify_session_token)])
def delete_hotkey(hotkey_id: str):
    hotkey_catalog.delete(hotkey_id)
    hotkey_agent.update_hotkeys(hotkey_catalog.get_all())
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
    return settings.model_dump()


@app.patch("/settings", dependencies=[Depends(verify_session_token)])
def patch_settings(new_settings: Dict[str, Any]):
    # Recursive update helper
    def update_recursive(target, updates):
        for k, v in updates.items():
            if isinstance(v, dict) and isinstance(getattr(target, k, None), dict):
                # We need to handle nested Pydantic models vs dicts.
                # For MVP, assuming settings are Pydantic models, we might need model_dump first or setattr
                # tailored approach:
                current_val = getattr(target, k)
                if hasattr(current_val, "model_dump"): # It's a sub-model
                    # This is tricky without a proper recursive update method on the settings object
                    # Simplified: just overwrite top-level sections if they are dicts in the payload
                    pass 
                
    # Simplified approach for the MVP:
    # Expecting payloads like {"app": {"ui_opacity": 0.5}}
    # We will manually map known top-level sections
    
    if "app" in new_settings:
        for k, v in new_settings["app"].items():
            if hasattr(settings.app, k):
                setattr(settings.app, k, v)

    if "routing_defaults" in new_settings:
        for k, v in new_settings["routing_defaults"].items():
            if hasattr(settings.routing_defaults, k):
                setattr(settings.routing_defaults, k, v)
                
    if "history" in new_settings:
        for k, v in new_settings["history"].items():
            if hasattr(settings.history, k):
                setattr(settings.history, k, v)

    settings.save(SETTINGS_FILE)
    return settings.model_dump()

# --- Connection Management ---

@app.get("/connections", dependencies=[Depends(verify_session_token)])
def get_connections():
    return settings.connections

@app.post("/connections", dependencies=[Depends(verify_session_token)])
def create_connection(connection: ConnectionDefinition):
    # Check if duplicate
    if any(c['connection_id'] == connection.connection_id for c in settings.connections):
        raise HTTPException(status_code=400, detail="Connection ID already exists")
    
    settings.connections.append(connection.model_dump())
    settings.save(SETTINGS_FILE)
    return connection

@app.put("/connections/{connection_id}", dependencies=[Depends(verify_session_token)])
def update_connection(connection_id: str, connection: ConnectionDefinition):
    for i, c in enumerate(settings.connections):
        if c['connection_id'] == connection_id:
            settings.connections[i] = connection.model_dump()
            settings.save(SETTINGS_FILE)
            return connection
    raise HTTPException(status_code=404, detail="Connection not found")

@app.delete("/connections/{connection_id}", dependencies=[Depends(verify_session_token)])
def delete_connection(connection_id: str):
    settings.connections = [c for c in settings.connections if c['connection_id'] != connection_id]
    # Also delete secret from store
    secret_store.delete(connection_id, "api_key")
    settings.save(SETTINGS_FILE)
    return {"status": "deleted"}

# --- Secret Management ---


@app.put("/connections/{connection_id}/secret", dependencies=[Depends(verify_session_token)])
def save_connection_secret(connection_id: str, payload: Dict[str, str]):
    secret = payload.get("secret")
    if not secret:
        raise HTTPException(status_code=400, detail="Secret value required")
    
    # Verify connection exists
    if not any(c['connection_id'] == connection_id for c in settings.connections):
        raise HTTPException(status_code=404, detail="Connection not found")

    try:
        secret_store.save(connection_id, "api_key", secret)
        return {"status": "saved"}
    except Exception as e:
        logger.error(f"Failed to save secret: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
