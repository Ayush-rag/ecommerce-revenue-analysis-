"""Run the whole project from start to finish:

    python main.py

1. Clean the real Olist data            -> data/processed/
2. Load it into a SQL database          -> data/olist.db
3. Run the SQL revenue queries          -> outputs/
4. Backtest + forecast next 3 months    -> outputs/forecast.csv
5. Build the interactive dashboard      -> docs/index.html
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

import build_dashboard  # noqa: E402
import clean_data  # noqa: E402
import load_database  # noqa: E402
import run_analysis  # noqa: E402

if __name__ == "__main__":
    print("\nE-commerce Revenue Analysis & Forecast - pipeline\n" + "-" * 50)
    clean_data.main()
    load_database.main()
    run_analysis.main()        # steps 3 and 4
    build_dashboard.main()
    print("\nDone. Open docs/index.html in your browser to see the dashboard.\n")
