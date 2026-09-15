import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from backend directory or project root
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR.parent / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.7-flash").strip()
PORT = int(os.getenv("PORT", "8000"))
HOST = os.getenv("HOST", "0.0.0.0")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

DATA_DIR = BASE_DIR / "app" / "data"
STATIC_DIR = BASE_DIR / "app" / "static"
CHARTS_DIR = STATIC_DIR / "charts"

# Ensure data and charts directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
CHARTS_DIR.mkdir(parents=True, exist_ok=True)
