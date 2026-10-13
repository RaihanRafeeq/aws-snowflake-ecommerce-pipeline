
from pathlib import Path
import sys

import pandas as pd

# Project directory
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"

# Load datasets
customers = pd.read_csv(RAW_DIR / "customers.csv")
products = pd.read_csv(RAW_DIR / "products.csv")
orders = pd.read_csv(RAW_DIR / "orders.csv")
order_items = pd.read_csv(RAW_DIR / "order_items.csv")
payments = pd.read_csv(RAW_DIR / "payments.csv")

errors = []


def check(condition, message):
    if condition:
        print(f"PASS: {message}")
    else:
        print(f"FAIL: {message}")
        errors.append(message)


# --------------------------------
# 1. Record Counts
# --------------------------------

print("\n--- RECORD COUNTS ---")

datasets = {
    "Customers": customers,
    "Products": products,
    "Orders": orders,
    "Order Items": order_items,
    "Payments": payments
}

for name, df in datasets.items():
    print(f"{name}: {len(df)}")
    check(len(df) > 0, f"{name} is not empty")


# --------------------------------
# 2. Primary Key Validation
# --------------------------------

print("\n--- PRIMARY KEY VALIDATION ---")

primary_keys = [
    (customers, "customer_id"),
    (products, "product_id"),
    (orders, "order_id"),
    (order_items, "order_item_id"),
    (payments, "payment_id")
]

for df, column in primary_keys:
    check(
        df[column].is_unique and df[column].notna().all(),
        f"{column} is unique and not null"
    )


# --------------------------------
# 3. Foreign Key Validation
# --------------------------------

print("\n--- FOREIGN KEY VALIDATION ---")

check(
    orders["customer_id"].isin(customers["customer_id"]).all(),
    "Orders reference valid customers"
)

check(
    order_items["order_id"].isin(orders["order_id"]).all(),
    "Order items reference valid orders"
)

check(
    order_items["product_id"].isin(products["product_id"]).all(),
    "Order items reference valid products"
)

check(
    payments["order_id"].isin(orders["order_id"]).all(),
    "Payments reference valid orders"
)


# --------------------------------
# 4. Missing Values
# --------------------------------

print("\n--- MISSING VALUE VALIDATION ---")

for name, df in datasets.items():
    check(
        not df.isnull().any().any(),
        f"{name} contains no missing values"
    )


# --------------------------------
# 5. Numeric Validation
# --------------------------------

print("\n--- NUMERIC VALIDATION ---")

check(
    (products["price"] >= 0).all(),
    "Product prices are non-negative"
)

check(
    (order_items["quantity"] > 0).all(),
    "Order item quantities are positive"
)

check(
    (order_items["unit_price"] >= 0).all(),
    "Order item prices are non-negative"
)

check(
    (payments["amount"] >= 0).all(),
    "Payment amounts are non-negative"
)


# --------------------------------
# 6. Order Date Validation
# --------------------------------

print("\n--- ORDER DATE VALIDATION ---")

customer_dates = customers[
    ["customer_id", "signup_date"]
].copy()

merged_orders = orders.merge(
    customer_dates,
    on="customer_id",
    how="left",
    validate="many_to_one"
)

check(
    (
        pd.to_datetime(merged_orders["order_date"])
        >= pd.to_datetime(merged_orders["signup_date"])
    ).all(),
    "Orders occur on or after customer signup"
)


# --------------------------------
# 7. Payment Total Validation
# --------------------------------

print("\n--- PAYMENT TOTAL VALIDATION ---")

item_totals = (
    order_items.assign(
        line_total=lambda df:
            df["quantity"] * df["unit_price"]
    )
    .groupby("order_id")["line_total"]
    .sum()
    .round(2)
)

payment_totals = payments.set_index(
    "order_id"
)["amount"]

check(
    set(item_totals.index) == set(orders["order_id"]),
    "Every order has at least one item"
)

check(
    payments["order_id"].is_unique
    and set(payments["order_id"]) == set(orders["order_id"]),
    "Every order has exactly one payment"
)

check(
    item_totals.sort_index().equals(
        payment_totals.sort_index().round(2)
    ),
    "Payment amounts match order item totals"
)


# --------------------------------
# Final Result
# --------------------------------

print("\n--- VALIDATION SUMMARY ---")

if errors:
    print(f"VALIDATION FAILED: {len(errors)} checks failed")
    sys.exit(1)
else:
    print("ALL DATA VALIDATION CHECKS PASSED")
