"""
Single Source of Truth for application metadata.
All app-wide constants MUST be defined here.
Other files import from this module; non-Python files are
stamped by sync_constants.py.
"""

APP_NAME = "PasteSuiteAI"
APP_VERSION = "0.1.0"
APP_IDENTIFIER = "com.pastesuite.ai"

# Network
BACKEND_PORT = 8000
FRONTEND_DEV_PORT = 1420
ALLOWED_HOSTS = ("127.0.0.1", "localhost", "::1")

# OS integration
SERVICE_NAME = "PasteSuiteAI"
APP_DIR_NAME = "PasteSuiteAI"
ENV_PREFIX = "PASTE_SUITE_AI_"
