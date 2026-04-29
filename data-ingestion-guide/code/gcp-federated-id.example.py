#!/usr/bin/env python3

import json
import os
import boto3
from google.cloud import iam_credentials_v1

# IAM Role ARN created and provided by PostPilot...
ROLE_ARN = "arn:aws:iam::000000000000:role/data-feed/postpilot-data-feed..."
# S3 Bucket name created and provided by PostPilot...
S3_BUCKET_NAME   = "postpilot-data-feed..."
S3_BUCKET_REGION = "us-east-2"
# GCP authentication: SA JSON credentials shown for example only. A more secure approach should be used in production...
GCP_CREDENTIALS_FILE = os.path.expanduser("~/path/to/credentials.json")


# Authenticate GCP Service Account and request OIDC token for AWS sts:AssumeRoleWithWebIdentity...
with open(GCP_CREDENTIALS_FILE) as f:
    service_account_email = json.load(f)["client_email"]

gcp_iam_client = iam_credentials_v1.IAMCredentialsClient.from_service_account_file(GCP_CREDENTIALS_FILE)

request_name = f"projects/-/serviceAccounts/{service_account_email}"

id_token_response = gcp_iam_client.generate_id_token(
    name=request_name,
    audience=S3_BUCKET_NAME,
    include_email=True,
)

print(id_token_response.token)

# Assume IAM Role in PostPilot customer-access account...
sts_client = boto3.client("sts", region_name=S3_BUCKET_REGION)
assume_role_response = sts_client.assume_role_with_web_identity(
    RoleArn=ROLE_ARN,
    RoleSessionName="S3PutObjectSession",
    WebIdentityToken=id_token_response.token,
)

credentials = assume_role_response["Credentials"]

print(credentials)

# Initialize the S3 client with assumed temporary credentials...
s3_client = boto3.client(
    "s3",
    region_name=S3_BUCKET_REGION,
    aws_access_key_id=credentials["AccessKeyId"],
    aws_secret_access_key=credentials["SecretAccessKey"],
    aws_session_token=credentials["SessionToken"],
)

CUSTOMERS_FILE_NAME = "customers_2026032012.jsonl"
with open(f"/path/to/{CUSTOMERS_FILE_NAME}", "rb") as f:
    s3_client.put_object(
        Bucket=S3_BUCKET_NAME,
        Key=f"customers/{CUSTOMERS_FILE_NAME}",
        Body=f,
        ContentType="application/json",
    )

print(f"Successfully uploaded object 'customers/{CUSTOMERS_FILE_NAME}' to bucket '{S3_BUCKET_NAME}'...")

ORDERS_FILE_NAME = "orders_2026032012.jsonl"
with open(f"/path/to/{ORDERS_FILE_NAME}", "rb") as f:
    s3_client.put_object(
        Bucket=S3_BUCKET_NAME,
        Key=f"orders/{ORDERS_FILE_NAME}",
        Body=f,
        ContentType="application/json",
    )

print(f"Successfully uploaded object 'orders/{ORDERS_FILE_NAME}' to bucket '{S3_BUCKET_NAME}'...")
