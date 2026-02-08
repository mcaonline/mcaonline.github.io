from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from contextlib import asynccontextmanager
from typing import List, Dict, Any
import uvicorn
import secrets
import os
from loguru import logger

from .domain.app_constants import APP_NAME, APP_VERSION, BACKEND_PORT, FRONTEND_DEV_PORT, ALLOWED_HOSTS
from .domain.models import (
    ActionDefinition, ConnectionDefinition,
    ProviderInfoResponse, HealthResponse, ExecuteResponse,
    StatusResponse, SessionTokenResponse, HistoryEntryResponse,
)
from .domain.ui_text import UiTextCatalog
from .domain.result import Err
from .domain.types import ActionId, ConnectionId
from .domain.events import ActionChanged, SettingsChanged
from .composition_root import create_services

# --- Bootstrap all services ---
services = create_services()

# --- Session Token (regenerated on each start) ---
SESSION_TOKEN = secrets.token_urlsafe(32)
API_KEY_HEADER = APIKeyHeader(name="X-Session-Token", auto_error=False)

async def verify_session_token(request: Request, token: str = Depends(API_KEY_HEADER)):
    """Verify the session token for API authentication."""
    client_host = request.client.host if request.client else ""

    if client_host not in ALLOWED_HOSTS:
        raise HTTPException(status_code=403, detail="Access denied: Non-local requests forbidden")

    if token and token != SESSION_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid session token")

    return True

# --- Lifespan ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    pid = os.getpid()
    logger.info(f"[{pid}] LIFESPAN START")
    logger.info(f"[{pid}] Starting Action Agent...")
    logger.info(f"[{pid}] Session Token: {SESSION_TOKEN}")
    services.action_agent.update_actions(services.action_catalog.get_all())
    services.action_agent.start()
    yield
    logger.info(f"[{pid}] LIFESPAN STOP")
    logger.info(f"[{pid}] Stopping Action Agent...")
    services.action_agent.stop()

app = FastAPI(title=f"{APP_NAME} Core", lifespan=lifespan)

# CORS - Restricted to localhost only
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        f"http://localhost:{BACKEND_PORT}",
        f"http://127.0.0.1:{BACKEND_PORT}",
        f"http://localhost:{FRONTEND_DEV_PORT}",
        f"http://127.0.0.1:{FRONTEND_DEV_PORT}",
        "tauri://localhost",
        "https://tauri.localhost",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# --- Public Routes (no auth required) ---

@app.get("/health", response_model=HealthResponse)
def health_check():
    return {"status": "ok", "version": APP_VERSION}

@app.get("/ui-text", response_model=Dict[str, str])
def get_ui_text():
    return {k.value: v for k, v in UiTextCatalog._DEFAULTS.items()}

@app.get("/providers", response_model=List[ProviderInfoResponse])
def get_providers():
    return [
        {
            "provider_id": r.provider_id,
            "display_name": r.display_name,
            "capabilities": r.capabilities,
            "requires_auth": r.requires_auth,
            "provider_class": r.provider_class,
        }
        for r in services.provider_registry.list_all()
    ]

@app.get("/session-token", response_model=SessionTokenResponse)
def get_session_token(request: Request):
    """Returns session token only for localhost requests."""
    client_host = request.client.host if request.client else ""
    if client_host not in ALLOWED_HOSTS:
        raise HTTPException(status_code=403, detail="Access denied")
    return {"token": SESSION_TOKEN}

# --- Protected Routes (require localhost + optional token) ---

@app.get("/actions", response_model=List[ActionDefinition], dependencies=[Depends(verify_session_token)])
def get_actions():
    return services.action_catalog.get_all()

@app.post("/actions", response_model=ActionDefinition, dependencies=[Depends(verify_session_token)])
def create_action(action: ActionDefinition):
    services.action_catalog.add(action)
    services.event_bus.publish(ActionChanged())
    return action

@app.put("/actions/{action_id}", response_model=ActionDefinition, dependencies=[Depends(verify_session_token)])
def update_action(action_id: str, action: ActionDefinition):
    if action.id != action_id:
        raise HTTPException(status_code=400, detail="ID mismatch")
    services.action_catalog.update(action)
    services.event_bus.publish(ActionChanged())
    return action

@app.delete("/actions/{action_id}", response_model=StatusResponse, dependencies=[Depends(verify_session_token)])
def delete_action(action_id: str):
    services.action_catalog.delete(ActionId(action_id))
    services.event_bus.publish(ActionChanged())
    return {"status": "deleted"}

@app.post("/actions/{action_id}/execute", response_model=ExecuteResponse, dependencies=[Depends(verify_session_token)])
def execute_action(action_id: str):
    if not action_id.replace("-", "").replace("_", "").isalnum():
        raise HTTPException(status_code=400, detail="Invalid action ID format")

    action = services.action_catalog.get(ActionId(action_id))
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")

    result = services.pipeline.execute(action)
    if isinstance(result, Err):
        raise HTTPException(status_code=422, detail=result.error.message)

    chunks = list(result.value)
    return {"result": "".join(chunks)}

@app.get("/history", response_model=List[HistoryEntryResponse], dependencies=[Depends(verify_session_token)])
def get_history():
    return services.history_repo.get_recent()

@app.get("/settings", dependencies=[Depends(verify_session_token)])
def get_settings():
    return services.settings.model_dump()

@app.patch("/settings", dependencies=[Depends(verify_session_token)])
def patch_settings(new_settings: Dict[str, Any]):
    if "app" in new_settings:
        for k, v in new_settings["app"].items():
            if hasattr(services.settings.app, k):
                setattr(services.settings.app, k, v)

    if "routing_defaults" in new_settings:
        for k, v in new_settings["routing_defaults"].items():
            if hasattr(services.settings.routing_defaults, k):
                setattr(services.settings.routing_defaults, k, v)

    if "history" in new_settings:
        for k, v in new_settings["history"].items():
            if hasattr(services.settings.history, k):
                setattr(services.settings.history, k, v)

    services.event_bus.publish(SettingsChanged())
    return services.settings.model_dump()

# --- Connection Management ---

@app.get("/connections", dependencies=[Depends(verify_session_token)])
def get_connections():
    return services.settings.connections

@app.post("/connections", response_model=ConnectionDefinition, dependencies=[Depends(verify_session_token)])
def create_connection(connection: ConnectionDefinition):
    if any(c['connection_id'] == connection.connection_id for c in services.settings.connections):
        raise HTTPException(status_code=400, detail="Connection ID already exists")

    services.settings.connections.append(connection.model_dump())
    services.event_bus.publish(SettingsChanged())
    return connection

@app.put("/connections/{connection_id}", response_model=ConnectionDefinition, dependencies=[Depends(verify_session_token)])
def update_connection(connection_id: str, connection: ConnectionDefinition):
    for i, c in enumerate(services.settings.connections):
        if c['connection_id'] == connection_id:
            services.settings.connections[i] = connection.model_dump()
            services.event_bus.publish(SettingsChanged())
            return connection
    raise HTTPException(status_code=404, detail="Connection not found")

@app.delete("/connections/{connection_id}", response_model=StatusResponse, dependencies=[Depends(verify_session_token)])
def delete_connection(connection_id: str):
    services.settings.connections = [
        c for c in services.settings.connections if c['connection_id'] != connection_id
    ]
    services.secret_store.delete(ConnectionId(connection_id), "api_key")
    services.event_bus.publish(SettingsChanged())
    return {"status": "deleted"}

# --- Secret Management ---

@app.put("/connections/{connection_id}/secret", response_model=StatusResponse, dependencies=[Depends(verify_session_token)])
def save_connection_secret(connection_id: str, payload: Dict[str, str]):
    secret = payload.get("secret")
    if not secret:
        raise HTTPException(status_code=400, detail="Secret value required")

    if not any(c['connection_id'] == connection_id for c in services.settings.connections):
        raise HTTPException(status_code=404, detail="Connection not found")

    try:
        services.secret_store.save(ConnectionId(connection_id), "api_key", secret)
        return {"status": "saved"}
    except Exception as e:
        logger.error(f"Failed to save secret: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/shutdown", response_model=StatusResponse, dependencies=[Depends(verify_session_token)])
def shutdown_application():
    """Shuts down the backend server."""
    logger.info("Shutdown requested via API")
    import threading
    import time
    import signal
    import sys

    def force_exit():
        time.sleep(0.5)
        logger.info("Exiting process...")
        try:
            os.kill(os.getpid(), signal.SIGINT)
        except Exception:
            pass
        time.sleep(2.0)
        logger.warning("SIGINT did not terminate process, forcing exit...")
        sys.exit(0)

    threading.Thread(target=force_exit, daemon=True).start()
    return {"status": "shutting_down"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=BACKEND_PORT)
