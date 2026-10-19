"""
Seed Database Script.
Initializes SQLite hardware database and populates it with verified hardware specs.
"""

import sys
import json
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.config import DATABASE_PATH, SEED_DATA_PATH
from core.domain.models import HardwareSpec
from core.repository.database import initialize_schema
from core.repository.hardware_repo import HardwareRepository


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def seed():
    print(f"[*] Initializing database at: {DATABASE_PATH}")
    initialize_schema()

    repo = HardwareRepository()

    if not SEED_DATA_PATH.exists():
        print(f"[!] Seed file not found at: {SEED_DATA_PATH}")
        sys.exit(1)

    with open(SEED_DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    count = 0
    for item in data:
        spec = HardwareSpec.model_validate(item)
        repo.upsert_hardware_spec(spec)
        count += 1
        print(f" [+] Inserted/Updated: [{spec.category.upper()}] {spec.name} ({spec.id})")

    print(f"\n[OK] Successfully seeded {count} hardware items into SQLite database.")


if __name__ == "__main__":
    seed()
