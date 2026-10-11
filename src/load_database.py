"""Step 2 - Load the clean tables into a SQL database (SQLite, built into Python)."""
import sqlite3

import pandas as pd

from config import CLEAN_DIR, DB_PATH, SCHEMA_SQL

# Parents before children, so foreign keys always point at existing rows
TABLES = ["customers", "orders", "products", "order_items", "payments"]


def main():
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(SCHEMA_SQL.read_text())
        counts = {}
        for name in TABLES:
            df = pd.read_csv(CLEAN_DIR / f"{name}.csv.gz")
            df.to_sql(name, conn, if_exists="append", index=False)
            counts[name] = conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
        sales_rows = conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0]

    summary = ", ".join(f"{k} {v:,}" for k, v in counts.items())
    print(f"[2/5] Loaded SQLite database: {summary}")
    print(f"      `sales` view (delivered items, Jan 2017 - Aug 2018): {sales_rows:,} rows")


if __name__ == "__main__":
    main()
