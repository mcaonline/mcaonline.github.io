"""
Export the FastAPI OpenAPI schema to a JSON file for TypeScript codegen.

Usage:
    cd backend
    python export_openapi.py

Outputs: ../frontend/src/api/openapi.json
"""

import json
import sys
from pathlib import Path

# Ensure the backend package is importable
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.main import app

schema = app.openapi()
output_path = Path(__file__).resolve().parent.parent / "frontend" / "src" / "api" / "openapi.json"
output_path.parent.mkdir(parents=True, exist_ok=True)

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(schema, f, indent=2)

print(f"Exported OpenAPI schema to {output_path}")
