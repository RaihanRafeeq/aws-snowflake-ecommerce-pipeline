
# Setup and Reproduction Guide

## Prerequisites

- Python 3.10 or later
- AWS account with access to S3, Lambda and IAM
- Snowflake account
- Git
- VS Code or another Python editor

## 1. Clone the Repository

```bash
git clone https://github.com/RaihanRafeeq/aws-snowflake-ecommerce-pipeline.git
cd aws-snowflake-ecommerce-pipeline
```

Replace the clone URL if the repository uses a different name.

## 2. Configure Python

Create and activate a virtual environment.

Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 3. Prepare the Data

The repository includes Python scripts for generating and validating
sample e-commerce CSV datasets:

- scripts/generate_data.py
- scripts/validate_data.py

Review their configuration and run them as appropriate.

## 4. Configure AWS S3

Create an S3 bucket and the following prefixes:

- raw/
- processed/
- auto_ingest/customers/
- auto_ingest/products/
- auto_ingest/orders/
- auto_ingest/order_items/
- auto_ingest/payments/

Use your own globally unique S3 bucket name.

## 5. Configure AWS Lambda

Deploy lambda/lambda_function.py as an AWS Lambda function.

Configure:
- An appropriate Python runtime
- An IAM execution role with the required S3 permissions
- An S3 ObjectCreated event notification for raw/
- CloudWatch logging

Verify that uploading a CSV to raw/ produces a processed file
in processed/.

## 6. Configure Snowflake

Create a Snowflake warehouse and execute the relevant SQL files
in snowflake/ in dependency order.

The scripts cover:
- Database and schema creation
- RAW tables
- Storage integration
- CSV file format and external stage
- STAGING tables and transformations
- Analytics views
- Snowpipes
- Streams and scheduled Tasks

IMPORTANT:
The numbered filenames are not a fully executable sequential
installer. Review dependencies and existing objects before
running them.

The SQL scripts use project-specific object names such as
ECOMMERCE_DB and ECOMMERCE_WH. Update these as required.

## 7. Configure S3-to-Snowflake Access

Set up the Snowflake storage integration and AWS IAM trust policy.

Use the example IAM policy files under aws/iam/ as references.

Replace account-specific identifiers, roles, bucket names,
and ARNs with your own values.

Do not commit AWS credentials or private keys.

## 8. Enable Snowpipe Auto-Ingestion

Create the five Snowpipes.

Retrieve the Snowflake-managed notification channel for the pipes
and configure the required S3 event notifications.

Verify that new CSV files uploaded to auto_ingest/ are
automatically ingested into RAW tables.

## 9. Configure Incremental Processing

Create the five append-only Streams and five transformation Tasks.

After initial data is loaded, synchronize existing RAW records
into STAGING using the appropriate initial-load transformations.

Resume the scheduled Tasks when ready to process new data.

## 10. Run an End-to-End Test

1. Upload a source CSV to raw/.
2. Verify Lambda creates a cleaned file in processed/.
3. Copy the processed file to its matching auto_ingest/ prefix.
4. Verify Snowpipe loads the file into RAW.
5. Wait for the scheduled Task to update STAGING.
6. Query the ANALYTICS views.
7. Refresh the Streamlit dashboard.

The copy in step 3 is manual in this implementation.

## 11. Deploy the Dashboard

Create a Streamlit application inside Snowflake.

Use dashboard/streamlit_app.py as the application source.

Configure the application with the required database, schema,
warehouse, and permissions.

## 12. Cost Management

Suspend scheduled Tasks when the pipeline is not in use.

```sql
ALTER TASK ECOMMERCE_DB.STAGING.CUSTOMERS_TRANSFORM_TASK SUSPEND;
ALTER TASK ECOMMERCE_DB.STAGING.PRODUCTS_TRANSFORM_TASK SUSPEND;
ALTER TASK ECOMMERCE_DB.STAGING.ORDERS_TRANSFORM_TASK SUSPEND;
ALTER TASK ECOMMERCE_DB.STAGING.ORDER_ITEMS_TRANSFORM_TASK SUSPEND;
ALTER TASK ECOMMERCE_DB.STAGING.PAYMENTS_TRANSFORM_TASK SUSPEND;
```

Suspend the warehouse when no compute is needed:

```sql
ALTER WAREHOUSE ECOMMERCE_WH SUSPEND;
```

Note: Snowpipe serverless ingestion may continue even while
scheduled Tasks are suspended.
