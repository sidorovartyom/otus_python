"""Initialize database - create tables."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from airflow_monitor.db.database import init_database

if __name__ == "__main__":
    print("Initializing database...")
    init_database()
    print("Done!")
