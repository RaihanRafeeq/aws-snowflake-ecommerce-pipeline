
import random
from pathlib import Path

import pandas as pd
from faker import Faker

from datetime import timedelta

# Configuration
NUM_CUSTOMERS = 1000
NUM_PRODUCTS = 100
NUM_ORDERS = 5000
SEED = 42
MIN_ITEMS_PER_ORDER = 1
MAX_ITEMS_PER_ORDER = 5

random.seed(SEED)
Faker.seed(SEED)
fake = Faker()

# Output directory
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

# Generate customers
customers = []

for customer_id in range(1, NUM_CUSTOMERS + 1):
    customers.append({
        "customer_id": customer_id,
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "email": fake.unique.email(),
        "city": fake.city(),
        "country": fake.country(),
        "signup_date": fake.date_between(
            start_date="-3y",
            end_date="today"
        )
    })

customers_df = pd.DataFrame(customers)

# Generate products
categories = [
    "Electronics",
    "Clothing",
    "Home",
    "Books",
    "Sports"
]

products = []

for product_id in range(1, NUM_PRODUCTS + 1):
    category = random.choice(categories)

    products.append({
        "product_id": product_id,
        "product_name": f"{category} Product {product_id}",
        "category": category,
        "price": round(random.uniform(5, 1000), 2)
    })

products_df = pd.DataFrame(products)


# --------------------------------
# Generate Orders
# --------------------------------

orders = []

order_statuses = [
    "Delivered",
    "Shipped",
    "Processing",
    "Cancelled"
]

for order_id in range(1, NUM_ORDERS + 1):

    # Select an existing customer
    customer = random.choice(customers)

    customer_id = customer["customer_id"]

    # Orders cannot happen before customer signup
    signup_date = customer["signup_date"]

    order_date = fake.date_between(
        start_date=signup_date,
        end_date="today"
    )

    # Select order status
    status = random.choices(
        order_statuses,
        weights=[70, 15, 10, 5],
        k=1
    )[0]

    order = {
        "order_id": order_id,
        "customer_id": customer_id,
        "order_date": order_date,
        "status": status
    }

    orders.append(order)

orders_df = pd.DataFrame(orders)


# --------------------------------
# Generate Order Items
# --------------------------------

order_items = []

order_item_id = 1

for order in orders:

    order_id = order["order_id"]

    # Random number of products per order
    num_items = random.randint(
        MIN_ITEMS_PER_ORDER,
        MAX_ITEMS_PER_ORDER
    )

    # Select unique products for each order
    selected_products = random.sample(
        products,
        k=num_items
    )

    for product in selected_products:

        quantity = random.randint(1, 5)

        order_item = {
            "order_item_id": order_item_id,
            "order_id": order_id,
            "product_id": product["product_id"],
            "quantity": quantity,
            "unit_price": product["price"]
        }

        order_items.append(order_item)

        order_item_id += 1

order_items_df = pd.DataFrame(order_items)


# --------------------------------
# Generate Payments
# --------------------------------

payments = []

payment_methods = [
    "Credit Card",
    "Debit Card",
    "UPI",
    "Net Banking",
    "Digital Wallet"
]

# Calculate total amount for each order
order_totals = (
    order_items_df.assign(
        line_total=lambda df: df["quantity"] * df["unit_price"]
    )
    .groupby("order_id")["line_total"]
    .sum()
    .round(2)
    .to_dict()
)

for payment_id, order in enumerate(orders, start=1):

    order_id = order["order_id"]
    order_status = order["status"]

    # Determine payment status
    if order_status in ["Delivered", "Shipped"]:
        payment_status = "Completed"

    elif order_status == "Processing":
        payment_status = "Pending"

    else:
        payment_status = random.choice(
            ["Failed", "Refunded"]
        )

    payment = {
        "payment_id": payment_id,
        "order_id": order_id,
        "payment_method": random.choice(payment_methods),
        "amount": round(float(order_totals[order_id]), 2),
        "payment_status": payment_status
    }

    payments.append(payment)

payments_df = pd.DataFrame(payments)


# Save CSV files
customers_df.to_csv(
    RAW_DIR / "customers.csv",
    index=False
)

products_df.to_csv(
    RAW_DIR / "products.csv",
    index=False
)

orders_df.to_csv(
    RAW_DIR / "orders.csv",
    index=False
)

order_items_df.to_csv(
    RAW_DIR / "order_items.csv",
    index=False
)
payments_df.to_csv(
    RAW_DIR / "payments.csv",
    index=False
)

print("Payments generated:", len(payments_df))
print("Order items generated:", len(order_items_df))
print("Orders generated:", len(orders_df))
print("Customers generated:", len(customers_df))
print("Products generated:", len(products_df))
print("Files saved to:", RAW_DIR)
