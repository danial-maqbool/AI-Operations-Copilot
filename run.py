import os
import sys
import subprocess
import webbrowser
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def ensure_env():
    env_file = BASE_DIR / ".env"
    env_example = BASE_DIR / ".env.example"
    if not env_file.exists() and env_example.exists():
        print("[OpsPilot] Creating .env from .env.example...")
        env_file.write_text(env_example.read_text(encoding="utf-8"), encoding="utf-8")

def ensure_frontend_built():
    frontend_dir = BASE_DIR / "frontend"
    dist_dir = frontend_dir / "dist"
    if not (dist_dir / "index.html").exists():
        print("[OpsPilot] Building frontend production bundle...")
        npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
        subprocess.run([npm_cmd, "run", "build"], cwd=frontend_dir, check=True)

def main():
    ensure_env()
    ensure_frontend_built()
    
    # Import config after env setup
    from backend.config import settings
    print(f"[OpsPilot] Starting Operations Copilot on http://{settings.HOST}:{settings.PORT}")
    print(f"[OpsPilot] AI Enabled: {settings.AI_ENABLED} (Model: {settings.GEMINI_MODEL})")
    
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.HOST, port=settings.PORT, reload=False)

if __name__ == "__main__":
    main()
