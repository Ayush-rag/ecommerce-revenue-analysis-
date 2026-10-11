# Rebuilding the Dashboard in Power BI

This guide recreates the dashboard in **Power BI Desktop** (free, Windows). It takes about 60 minutes.

## 1. Get one clean sales table

Run `python main.py` first. Then export the `sales` view to CSV, so Power BI gets the same rows the SQL analysis used:

```bash
python -c "import sqlite3, pandas as pd; pd.read_sql('SELECT * FROM sales', sqlite3.connect('data/olist.db')).to_csv('powerbi/sales.csv', index=False)"
```

Also load `outputs/forecast.csv` for the forecast.

## 2. Load into Power BI

1. **Get data → Text/CSV** → `powerbi/sales.csv` → **Transform Data**.
2. Check the types: `order_date` = Date, `revenue` and `freight` = Fixed decimal, `weekday` = Whole number. Rename the table to **Sales**.
3. **Get data → Text/CSV** → `outputs/forecast.csv`. Rename it **Forecast**.
4. **Close & Apply**.

## 3. Add columns

```DAX
Month Start = DATE(YEAR(Sales[order_date]), MONTH(Sales[order_date]), 1)
Year = YEAR(Sales[order_date])
Day Name = FORMAT(Sales[order_date], "ddd")
```

Sort `Day Name` by `weekday`.

## 4. Measures

```DAX
Revenue = SUM(Sales[revenue])

Orders = DISTINCTCOUNT(Sales[order_id])

Customers = DISTINCTCOUNT(Sales[customer_unique_id])

Items Sold = COUNTROWS(Sales)

Avg Order Value = DIVIDE([Revenue], [Orders])

Items per Order = DIVIDE([Items Sold], [Orders])

Freight % = DIVIDE(SUM(Sales[freight]), [Revenue])

Revenue Share = DIVIDE([Revenue], CALCULATE([Revenue], ALLSELECTED(Sales[category])))

Revenue Prev Month =
CALCULATE([Revenue], DATEADD(Sales[order_date], -1, MONTH))

MoM Growth % = DIVIDE([Revenue] - [Revenue Prev Month], [Revenue Prev Month])

Revenue Same Month Last Year =
CALCULATE([Revenue], SAMEPERIODLASTYEAR(Sales[order_date]))

YoY Growth % = DIVIDE([Revenue] - [Revenue Same Month Last Year], [Revenue Same Month Last Year])
```

For the time-intelligence measures (`DATEADD`, `SAMEPERIODLASTYEAR`) to work, create a date table and mark it as a date table:
`Dates = CALENDAR(DATE(2017,1,1), DATE(2018,12,31))`, then relate `Dates[Date]` to `Sales[order_date]`.

## 5. Build the page

| Position | Visual | Fields |
|---|---|---|
| Top | **Slicer** (buttons) | `Year` |
| Top | **Slicer** (dropdown) | `state` |
| Row 2 | 5 × **Card** | Revenue, Orders, Avg Order Value, Items per Order, Freight % |
| Row 3 | **Line chart** | X: `Month Start` · Y: `Revenue`. Add `Forecast[forecast]` as a second line on the same axis, and use **Error bars** with `low` / `high` for the range. |
| Row 4 left | **Bar chart** | Y: `category` · X: `Revenue` · Top N filter = 10 |
| Row 4 right | **Bar chart** | Y: `state` · X: `Revenue` · Top N filter = 10 |
| Row 5 left | **Column chart** | X: `Day Name` · Y: `Revenue Share` |
| Row 5 right | **Table** | `Month Start`, Revenue, MoM Growth %, YoY Growth % |

## 6. Check your numbers

With no filters, your cards should show:

| Card | Value |
|---|---|
| Revenue | R$13,181,027 |
| Orders | 96,211 |
| Avg Order Value | R$137.00 |
| Items per Order | 1.14 |
| Freight % | 16.6% |

Save as `powerbi/ecommerce_revenue.pbix`, take a screenshot for `images/`, and add both to the repo.
