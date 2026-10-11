"""Step 1 - Clean the raw Olist files.

The raw data is the real Brazilian E-Commerce Public Dataset by Olist
(99,441 orders, Sep 2016 - Oct 2018). Each fix is logged with how many
rows it touched.
"""
import pandas as pd

from config import CLEAN_DIR, MISSING_TRANSLATIONS, OUTPUT_DIR, RAW_DIR


def read(name: str, **kw) -> pd.DataFrame:
    return pd.read_csv(RAW_DIR / f"{name}.csv.gz", **kw)


def nice(name: str) -> str:
    """'bed_bath_table' -> 'Bed bath table'"""
    return name.replace("_", " ").strip().capitalize()


def clean() -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
    log = []

    orders = read("olist_orders_dataset")
    items = read("olist_order_items_dataset")
    customers = read("olist_customers_dataset")
    products = read("olist_products_dataset")
    payments = read("olist_order_payments_dataset")
    translation = read("product_category_name_translation")

    for label, df in [("orders", orders), ("order items", items), ("customers", customers),
                      ("products", products), ("payments", payments)]:
        log.append((f"Raw rows: {label}", len(df)))

    # 1. Duplicates (none expected, but always check)
    dupes = sum(int(df.duplicated().sum()) for df in (orders, items, customers, products, payments))
    log.append(("Duplicate rows found across all files", dupes))
    orders, items, customers, products, payments = (
        df.drop_duplicates() for df in (orders, items, customers, products, payments))

    # 2. Dates stored as text -> real dates
    for col in ["order_purchase_timestamp", "order_approved_at",
                "order_delivered_customer_date", "order_estimated_delivery_date"]:
        orders[col] = pd.to_datetime(orders[col])
    log.append(("Order date columns converted from text to dates", 4))

    # 3. Products with no category -> 'Unknown'
    missing_cat = products["product_category_name"].isna()
    log.append(("Products with no category, labelled 'Unknown'", int(missing_cat.sum())))

    # 4. Portuguese category names -> English (2 categories are missing from the translation file)
    lookup = dict(zip(translation["product_category_name"], translation["product_category_name_english"]))
    untranslated = products["product_category_name"].notna() & ~products["product_category_name"].isin(lookup)
    log.append(("Products whose category had no English name (added by hand)", int(untranslated.sum())))
    lookup.update(MISSING_TRANSLATIONS)
    products["category"] = products["product_category_name"].map(lookup).map(nice, na_action="ignore")
    products["category"] = products["category"].fillna("Unknown")

    # 5. Payments that can't be analysed: type 'not_defined' or a value of 0
    bad_pay = (payments["payment_type"] == "not_defined") | (payments["payment_value"] <= 0)
    log.append(("Payment rows removed (type 'not_defined' or value 0)", int(bad_pay.sum())))
    payments = payments[~bad_pay].copy()
    payments["payment_type"] = payments["payment_type"].map(nice)

    # 6. Orders marked delivered but with no delivery date (kept, but flagged)
    no_date = (orders["order_status"] == "delivered") & orders["order_delivered_customer_date"].isna()
    log.append(("Delivered orders with no delivery date (kept, flagged)", int(no_date.sum())))

    # 7. What the revenue rule will leave out (applied later in the SQL `sales` view)
    not_delivered = orders["order_status"] != "delivered"
    log.append(("Orders not delivered (cancelled, unavailable, in progress) - excluded from revenue",
                int(not_delivered.sum())))
    month = orders["order_purchase_timestamp"].dt.strftime("%Y-%m")
    outside = (month < "2017-01") | (month > "2018-08")
    log.append(("Orders outside Jan 2017 - Aug 2018 (incomplete months) - excluded from revenue",
                int(outside.sum())))

    # Keep only the columns the analysis uses
    tables = {
        "orders": orders[["order_id", "customer_id", "order_status", "order_purchase_timestamp",
                          "order_delivered_customer_date", "order_estimated_delivery_date"]],
        "order_items": items[["order_id", "order_item_id", "product_id", "seller_id", "price", "freight_value"]],
        "customers": customers[["customer_id", "customer_unique_id", "customer_city", "customer_state"]],
        "products": products[["product_id", "category"]],
        "payments": payments[["order_id", "payment_sequential", "payment_type",
                              "payment_installments", "payment_value"]],
    }
    return tables, pd.DataFrame(log, columns=["step", "rows"])


def main():
    tables, log = clean()
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)
    for name, df in tables.items():
        df.to_csv(CLEAN_DIR / f"{name}.csv.gz", index=False)
    log.to_csv(OUTPUT_DIR / "cleaning_log.csv", index=False)

    print("[1/5] Cleaned the real Olist data:")
    for step, rows in log.itertuples(index=False):
        print(f"      {step:<84} {rows:>7,}")


if __name__ == "__main__":
    main()
