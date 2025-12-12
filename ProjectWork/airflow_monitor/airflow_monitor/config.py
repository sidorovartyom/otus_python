"""Configuration module."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Database connections
AIRFLOW_DB_URL = os.getenv(
    "AIRFLOW_DB_URL",
    "postgresql://airflow:airflow@localhost:5432/airflow"
)

OWN_DB_PATH = os.getenv(
    "OWN_DB_PATH",
    str(PROJECT_ROOT / "airflow_monitor.db")
)

# Analysis settings
DEFAULT_PERIOD_DAYS = int(os.getenv("DEFAULT_PERIOD_DAYS", "7"))
ANOMALY_CONTAMINATION = float(os.getenv("ANOMALY_CONTAMINATION", "0.1"))

# Telegram settings (optional)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# Health score thresholds
HEALTH_EXCELLENT = 90
HEALTH_GOOD = 75
HEALTH_FAIR = 60

# Health score weights
HEALTH_WEIGHTS = {
    "success_rate": 0.7,
    "stability": 0.3
}
