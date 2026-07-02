"""
Builds the SQLite database used for the SQL analysis layer.

Loads the three CSVs from /data into a fresh data/healthcare.db, applying
sql/schema.sql first. Run after data/generate_data.py.

    python sql/build_db.py
"""

import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "healthcare.db"
SCHEMA_PATH = ROOT / "sql" / "schema.sql"
DATA_DIR = ROOT / "data"


def main():
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    try:
        with open(SCHEMA_PATH) as f:
            conn.executescript(f.read())

        machine_metadata = pd.read_csv(DATA_DIR / "machine_metadata.csv")
        equipment_logs = pd.read_csv(DATA_DIR / "equipment_logs.csv")
        maintenance_tickets = pd.read_csv(DATA_DIR / "maintenance_tickets.csv")

        machine_metadata.to_sql("machine_metadata", conn, if_exists="append", index=False)
        equipment_logs.to_sql("equipment_logs", conn, if_exists="append", index=False)
        maintenance_tickets.to_sql("maintenance_tickets", conn, if_exists="append", index=False)
        conn.commit()

        counts = {
            table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in ("machine_metadata", "equipment_logs", "maintenance_tickets")
        }
        print(f"Built {DB_PATH} with tables: {counts}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
