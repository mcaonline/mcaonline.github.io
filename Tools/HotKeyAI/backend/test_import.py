"""Quick test: does main.py import cleanly?"""
try:
    from src.main import app
    print("Import OK")
    for r in app.routes:
        print(f"  {getattr(r, 'methods', '?')} {r.path}")
except Exception as e:
    print(f"IMPORT FAILED: {type(e).__name__}: {e}")
