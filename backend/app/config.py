"""Application configuration. Implements PSM §2/§4 (G4: risk-free rate in config)."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR.parent / "data"
DB_PATH = DATA_DIR / "warrant.db"
LOG_PATH = DATA_DIR / "app.log"
MIGRATE_DIR = BASE_DIR / "scripts" / "migrate"

RISK_FREE_RATE = 0.015
# Collect endpoint is disabled (always 403) unless this env var is set.
COLLECT_TOKEN = os.environ.get("WARRANT_COLLECT_TOKEN")
SCHEDULE_HOUR = 16
SCHEDULE_MINUTE = 30
SCHEDULE_TIMEZONE = "Asia/Taipei"

HOST = "127.0.0.1"
PORT = 8000
