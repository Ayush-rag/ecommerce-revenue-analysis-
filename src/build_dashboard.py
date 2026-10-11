"""Step 5 - Build the interactive HTML dashboard (docs/index.html).

Summarises the database into small tables (month x state, month x state x
category, month x state x weekday), embeds them with Plotly.js in ONE page,
and lets the browser recalculate everything when the Year / State filters
change. Works offline and on GitHub Pages.
"""
import json
import os
import re
import sqlite3

import pandas as pd
import plotly

from config import DASHBOARD_HTML, DB_PATH, FORECAST_CSV, OUTPUT_DIR

TEMPLATE = os.path.join(os.path.dirname(__file__), "dashboard_template.html")


def dashboard_data() -> dict:
    with sqlite3.connect(DB_PATH) as conn:
        q = lambda sql: pd.read_sql_query(sql, conn)
        ms = q("""SELECT month, state, ROUND(SUM(revenue), 2) revenue, COUNT(DISTINCT order_id) orders,
                         COUNT(*) items, ROUND(SUM(freight), 2) freight
                  FROM sales GROUP BY month, state ORDER BY month, state""")
        msc = q("""SELECT month, state, category, ROUND(SUM(revenue), 2) revenue
                   FROM sales GROUP BY month, state, category""")
        msw = q("""SELECT month, state, weekday, ROUND(SUM(revenue), 2) revenue
                   FROM sales GROUP BY month, state, weekday""")

    sql_dir = OUTPUT_DIR / "sql_results"
    monthly = pd.read_csv(sql_dir / "monthly_revenue.csv")
    nov = monthly.loc[monthly["revenue"].idxmax()]

    months = sorted(ms["month"].unique())
    states = sorted(ms["state"].unique())
    categories = sorted(msc["category"].unique())
    mi, si, ci = ({v: i for i, v in enumerate(lst)} for lst in (months, states, categories))

    scores = pd.read_csv(OUTPUT_DIR / "forecast_method_scores.csv")
    return {
        "months": months,
        "states": states,
        "categories": categories,
        "ms": [[mi[r.month], si[r.state], r.revenue, r.orders, r.items, r.freight] for r in ms.itertuples()],
        "msc": [[mi[r.month], si[r.state], ci[r.category], r.revenue] for r in msc.itertuples()],
        "msw": [[mi[r.month], si[r.state], r.weekday, r.revenue] for r in msw.itertuples()],
        "forecast": pd.read_csv(FORECAST_CSV).to_dict("records"),
        "scores": scores.to_dict("records"),
        "bestMethod": scores.iloc[0]["method"],
        "loyalty": pd.read_csv(sql_dir / "customer_loyalty.csv").to_dict("records"),
        "payments": pd.read_csv(sql_dir / "payment_methods.csv").to_dict("records"),
        "blackFriday": {"month": nov["month"], "growth": float(nov["mom_growth_pct"])},
    }


def insights_html() -> str:
    md = (OUTPUT_DIR / "insights.md").read_text(encoding="utf-8")
    items = re.findall(r"^\d+\.\s+(.*)$", md, flags=re.MULTILINE)
    return "".join(f"<li>{re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)}</li>" for s in items)


def main():
    plotly_js = open(os.path.join(os.path.dirname(plotly.__file__), "package_data", "plotly.min.js"),
                     encoding="utf-8").read()
    html = open(TEMPLATE, encoding="utf-8").read()
    html = (html.replace("__DATA__", json.dumps(dashboard_data(), separators=(",", ":")))
                .replace("__INSIGHTS__", insights_html())
                .replace("__PLOTLY_JS__", plotly_js))   # last, so its text is never searched

    DASHBOARD_HTML.parent.mkdir(exist_ok=True)
    DASHBOARD_HTML.write_text(html, encoding="utf-8")
    print("[5/5] Built interactive dashboard -> docs/index.html")


if __name__ == "__main__":
    main()
