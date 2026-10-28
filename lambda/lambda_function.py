
import json
import logging
import csv
import io
from collections import defaultdict
from datetime import date
from decimal import Decimal, InvalidOperation

import boto3

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Create S3 client
s3 = boto3.client("s3")

# S3 configuration
BUCKET_NAME = "ecommerce-pipeline-4488"
RAW_PREFIX = "raw/"

# Files to read
CSV_FILES = [
    "customers.csv",
    "products.csv",
    "orders.csv",
    "order_items.csv",
    "payments.csv"
]


def read_csv_from_s3(filename):
    """
    Read a CSV file from S3 and return
    its rows as a list of dictionaries.
    """

    object_key = RAW_PREFIX + filename

    logger.info("Reading file: %s", object_key)

    response = s3.get_object(
        Bucket=BUCKET_NAME,
        Key=object_key
    )

    csv_content = (
        response["Body"]
        .read()
        .decode("utf-8-sig")
    )

    reader = csv.DictReader(
        io.StringIO(csv_content)
    )

    records = list(reader)

    logger.info(
        "Successfully read %s records from %s",
        len(records),
        filename
    )

    return records


def clean_records(records):
    """Remove surrounding whitespace from CSV values."""
    return [
        {
            key: value.strip() if isinstance(value, str) else value
            for key, value in record.items()
        }
        for record in records
    ]


def validate_primary_key(records, key, dataset):
    values = [row[key] for row in records]

    if not all(values):
        raise ValueError(f"{dataset}: missing primary key")

    if len(values) != len(set(values)):
        raise ValueError(f"{dataset}: duplicate primary key")


def validate_foreign_key(records, key, valid_values, dataset):
    for row in records:
        if row[key] not in valid_values:
            raise ValueError(
                f"{dataset}: invalid {key} = {row[key]}"
            )


def validate_positive_number(value, field, allow_zero=False):
    try:
        number = Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f"Invalid numeric value for {field}")

    if not number.is_finite():
        raise ValueError(f"Non-finite numeric value for {field}")

    if allow_zero:
        if number < 0:
            raise ValueError(f"{field} cannot be negative")
    elif number <= 0:
        raise ValueError(f"{field} must be positive")

    return number


def validate_datasets(data):
    """Validate relationships and business rules."""

    primary_keys = {
        "customers.csv": "customer_id",
        "products.csv": "product_id",
        "orders.csv": "order_id",
        "order_items.csv": "order_item_id",
        "payments.csv": "payment_id"
    }

    # Required values and primary keys
    for filename, records in data.items():
        if not records:
            raise ValueError(f"{filename}: empty dataset")

        for row in records:
            if any(
                value is None or value == ""
                for value in row.values()
            ):
                raise ValueError(
                    f"{filename}: missing value detected"
                )

        validate_primary_key(
            records, primary_keys[filename], filename
        )

    customers = {
        row["customer_id"]: row
        for row in data["customers.csv"]
    }

    products = {
        row["product_id"]: row
        for row in data["products.csv"]
    }

    orders = {
        row["order_id"]: row
        for row in data["orders.csv"]
    }

    items = data["order_items.csv"]
    payments = data["payments.csv"]

    # Foreign key validation
    validate_foreign_key(
        data["orders.csv"],
        "customer_id",
        set(customers),
        "orders"
    )

    validate_foreign_key(
        items, "order_id", set(orders), "order_items"
    )

    validate_foreign_key(
        items, "product_id", set(products), "order_items"
    )

    validate_foreign_key(
        payments, "order_id", set(orders), "payments"
    )

    # Product price validation
    for product in products.values():
        validate_positive_number(
            product["price"], "price", allow_zero=True
        )

    # Order date validation
    for order in orders.values():
        signup_date = date.fromisoformat(
            customers[order["customer_id"]]["signup_date"]
        )
        order_date = date.fromisoformat(order["order_date"])

        if order_date < signup_date:
            raise ValueError(
                f"Order {order['order_id']} predates signup"
            )

    # Calculate order totals
    order_totals = defaultdict(lambda: Decimal("0.00"))

    for item in items:
        quantity = validate_positive_number(
            item["quantity"], "quantity"
        )

        if quantity != quantity.to_integral_value():
            raise ValueError("Quantity must be an integer")

        price = validate_positive_number(
            item["unit_price"],
            "unit_price",
            allow_zero=True
        )

        order_totals[item["order_id"]] += quantity * price

    if set(order_totals) != set(orders):
        raise ValueError("Some orders have no order items")

    # Verify one payment per order
    payment_order_ids = [
        payment["order_id"] for payment in payments
    ]

    if (
        len(payment_order_ids) != len(set(payment_order_ids))
        or set(payment_order_ids) != set(orders)
    ):
        raise ValueError("Each order must have one payment")

    # Validate payment amounts
    for payment in payments:
        amount = validate_positive_number(
            payment["amount"], "amount", allow_zero=True
        )

        expected = order_totals[payment["order_id"]]

        if abs(amount - expected) > Decimal("0.01"):
            raise ValueError(
                f"Payment mismatch for order {payment['order_id']}"
            )

    return True


def write_csv_to_s3(filename, records):
    """
    Write cleaned CSV records to
    the processed/ prefix in S3.
    """

    if not records:
        raise ValueError(
            f"Cannot write empty dataset: {filename}"
        )

    output = io.StringIO()

    writer = csv.DictWriter(
        output,
        fieldnames=list(records[0].keys()),
        lineterminator="\n"
    )

    writer.writeheader()
    writer.writerows(records)

    object_key = "processed/" + filename

    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=object_key,
        Body=output.getvalue().encode("utf-8"),
        ContentType="text/csv"
    )

    logger.info(
        "Wrote %s records to %s",
        len(records),
        object_key
    )

    return object_key


def run_negative_test():
    """
    Verify that duplicate primary keys
    are rejected by the validation logic.
    """

    invalid_customers = [
        {"customer_id": "101"},
        {"customer_id": "101"}
    ]

    try:
        validate_primary_key(
            invalid_customers,
            "customer_id",
            "customers"
        )

    except ValueError as error:
        logger.info(
            "Expected validation error caught: %s",
            error
        )

        return {
            "test": "duplicate_primary_key",
            "result": "PASSED",
            "error_detected": str(error)
        }

    raise AssertionError(
        "Negative test failed: duplicate IDs were accepted"
    )


def lambda_handler(event, context):

    # Run a safe negative test when explicitly requested
    if isinstance(event, dict) and event.get("test_mode") == "negative":
        return {
            "statusCode": 200,
            "body": json.dumps(run_negative_test())
        }

    logger.info("Starting e-commerce ETL pipeline")

    datasets = {}

    # EXTRACT and CLEAN
    for filename in CSV_FILES:
        records = read_csv_from_s3(filename)
        datasets[filename] = clean_records(records)

    # VALIDATE
    validate_datasets(datasets)

    logger.info("Data validation successful")

    # LOAD processed datasets
    processed_files = []

    for filename, records in datasets.items():

        object_key = write_csv_to_s3(
            filename,
            records
        )

        processed_files.append(object_key)

    record_counts = {
        filename: len(records)
        for filename, records in datasets.items()
    }

    logger.info("ETL pipeline completed successfully")

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "ETL pipeline completed",
            "validation": "PASSED",
            "processed_files": processed_files,
            "record_counts": record_counts
        })
    }
