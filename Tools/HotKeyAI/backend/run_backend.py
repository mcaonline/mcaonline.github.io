"""Entry point for PyInstaller build - runs the backend as a module."""
import sys
import os

# Add the parent directory to path so relative imports work
if getattr(sys, 'frozen', False):
    # Running as PyInstaller bundle
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, base_path)

# Now import and run the actual main module
from src.main import app
from src.domain.app_constants import BACKEND_PORT
import uvicorn

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=BACKEND_PORT)
