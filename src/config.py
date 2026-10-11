"""Shared settings: file paths and analysis choices."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

RAW_DIR = ROOT / "data" / "raw"
CLEAN_DIR = ROOT / "data" / "processed"
DB_PATH = ROOT / "data" / "olist.db"

SCHEMA_SQL = ROOT / "sql" / "01_create_tables.sql"
QUERIES_SQL = ROOT / "sql" / "02_revenue_queries.sql"

OUTPUT_DIR = ROOT / "outputs"
EXCEL_REPORT = OUTPUT_DIR / "revenue_report.xlsx"
FORECAST_CSV = OUTPUT_DIR / "forecast.csv"
DASHBOARD_HTML = ROOT / "docs" / "index.html"
IMAGES_DIR = ROOT / "images"

# The analysis window (Jan 2017 - Aug 2018, complete months only) and the
# revenue rule (item prices of DELIVERED orders) live in ONE place: the
# `sales` view in sql/01_create_tables.sql.

# Forecast settings
FORECAST_MONTHS = 3        # predict Sep, Oct, Nov 2018
BACKTEST_MONTHS = 6        # hide the last 6 months, forecast them, measure the error

CURRENCY = "R$"            # Brazilian real

# Two categories in the product file have no English name in the translation file
MISSING_TRANSLATIONS = {
    "pc_gamer": "pc_gamer",
    "portateis_cozinha_e_preparadores_de_alimentos": "portable_kitchen_food_preparers",
}
