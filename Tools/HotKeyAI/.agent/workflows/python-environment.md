---
description: Python virtual environment and linting configuration for HotKeyAI
---

# Python Environment Setup

This project uses a virtual environment at `backend/.venv/`.

## Why Red Lint Errors Appear

VS Code's Pyre2 / Pylance linter shows red errors when it can't find imported packages. This happens when:
1. The Python interpreter isn't set to the project's venv
2. The `PYTHONPATH` doesn't include the `backend/src` directory

**These errors are IDE-only** - the code runs correctly when executed from the venv.

## Fix: Configure VS Code Python Interpreter

1. Open Command Palette: `Ctrl+Shift+P`
2. Type: "Python: Select Interpreter"
3. Choose: `backend/.venv/Scripts/python.exe`

Or verify `.vscode/settings.json` has:
```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/backend/.venv/Scripts/python.exe",
    "python.analysis.extraPaths": ["${workspaceFolder}/backend/src"],
    "python.analysis.autoSearchPaths": true
}
```

## Import Style

This project uses **relative imports** within packages:
```python
# Correct (relative)
from .base import IProvider
from ..domain.models import HotkeyDefinition

# Avoid (absolute from src)
from src.domain.models import HotkeyDefinition
```

## Running the Backend

// turbo
```bash
cd backend
.venv\Scripts\activate
python -m src.main
```
