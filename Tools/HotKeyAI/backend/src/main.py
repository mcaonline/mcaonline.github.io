from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import List, Dict, Any
import uvicorn
from pathlib import Path

from .config.settings import settings, SETTINGS_FILE
from .domain.models import HotkeyDefinition, ConnectionDefinition
from .domain.hotkey_catalog import HotkeyCatalogService
from .infrastructure.hotkeys import HotkeyAgent
from .infrastructure.clipboard import clipboard
from .infrastructure.secrets import secret_store
from .application.pipeline import ExecutionPipeline
from .infrastructure.history import HistoryRepository

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
    hotkey_agent.start()
    yield
    print("Stopping Hotkey Agent...")
    hotkey_agent.stop()

app = FastAPI(title="HotKeyAI Core", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routes ---

@app.get("/health")
def health_check():
    return {"status": "ok", "version": "0.1.0"}

@app.get("/hotkeys", response_model=List[HotkeyDefinition])
def get_hotkeys():
    return hotkey_catalog.get_all()

@app.post("/hotkeys")
def create_hotkey(hotkey: HotkeyDefinition):
    hotkey_catalog.add(hotkey)
    return hotkey

@app.put("/hotkeys/{hotkey_id}")
def update_hotkey(hotkey_id: str, hotkey: HotkeyDefinition):
    if hotkey.id != hotkey_id:
        raise HTTPException(status_code=400, detail="ID mismatch")
    hotkey_catalog.update(hotkey)
    return hotkey

@app.delete("/hotkeys/{hotkey_id}")
def delete_hotkey(hotkey_id: str):
    hotkey_catalog.delete(hotkey_id)
    return {"status": "deleted"}

@app.post("/execute/{hotkey_id}")
def execute_hotkey(hotkey_id: str):
    hotkey = hotkey_catalog.get(hotkey_id)
    if not hotkey:
        raise HTTPException(status_code=404, detail="Hotkey not found")
    
    results = []
    for chunk in pipeline.execute(hotkey):
        results.append(chunk)
    
    return {"result": "".join(results)}

@app.get("/history")
def get_history():
    return history_repo.get_recent()

@app.get("/settings")
def get_settings():
    return settings.model_dump()

@app.post("/settings")
def update_settings(new_settings: Dict[str, Any]):
    return {"status": "updated (mock)"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
