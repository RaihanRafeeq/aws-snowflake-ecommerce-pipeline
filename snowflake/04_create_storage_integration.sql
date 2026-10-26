
CREATE STORAGE INTEGRATION IF NOT EXISTS ECOMMERCE_S3_INTEGRATION
    TYPE = EXTERNAL_STAGE
    STORAGE_PROVIDER = 'S3'
    ENABLED = TRUE
    STORAGE_AWS_ROLE_ARN = 'arn:aws:iam::325836185375:role/snowflake-s3-access-role'
    STORAGE_ALLOWED_LOCATIONS = (
        's3://ecommerce-pipeline-4488/processed/'
    )
    COMMENT = 'Read-only S3 integration for the e-commerce pipeline';

