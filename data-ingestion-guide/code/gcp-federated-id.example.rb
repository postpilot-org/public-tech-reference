#! /usr/bin/env ruby

require 'aws-sdk-s3'
require 'aws-sdk-sts'
require "google/iam/credentials/v1"
require 'json'

# IAM Role ARN created and provided by PostPilot...
ROLE_ARN = "arn:aws:iam::000000000000:role/data-feed/postpilot-data-feed..."
# S3 Bucket name created and provided by PostPilot...
S3_BUCKET_NAME   = "postpilot-data-feed..."
S3_BUCKET_REGION = 'us-east-2'
# GCP authentication: SA JSON credentials shown for example only. A more secure approach should be used in production...
GCP_CREDENTIALS_FILE = File.expand_path('path/to/credentials.json')


# Authenticate GCP Service Account and request OIDC token for AWS sts:AssumeRoleWithWebIdentity...
gcp_iam_client = ::Google::Iam::Credentials::V1::IAMCredentials::Client.new do |config|
  config.credentials = GCP_CREDENTIALS_FILE
end

service_account_email = JSON.parse(File.read(GCP_CREDENTIALS_FILE)).fetch('client_email')
request_name          =  "projects/-/serviceAccounts/#{service_account_email}"

id_token_response = gcp_iam_client.generate_id_token(
  name: request_name, audience: S3_BUCKET_NAME, include_email: true
)


# Assume IAM Role in PostPilot customer-access account...
sts_client = Aws::STS::Client.new(region: S3_BUCKET_REGION)
assume_role_response = sts_client.assume_role_with_web_identity(
  role_arn:           ROLE_ARN,
  role_session_name: 'S3PutObjectSession',
  web_identity_token: id_token_response.token
)

credentials = assume_role_response.credentials
temp_credentials = Aws::Credentials.new(
  credentials.access_key_id,
  credentials.secret_access_key,
  credentials.session_token
)


# Initialize the S3 client with assumed temporary credentials...
s3_client = Aws::S3::Client.new(credentials: temp_credentials, region: S3_BUCKET_REGION)

customers_file_name = "customers_2026022012.jsonl"
s3_client.put_object(
  bucket: S3_BUCKET_NAME,
  key:  "customers/#{customers_file_name}",
  body: File.read("path/to/#{customers_file_name}"),
  content_type: 'application/json'
)

puts "Successfully uploaded object 'customers/#{customers_file_name}' to bucket '#{S3_BUCKET_NAME}'..."

orders_file_name = "orders_2026022012.jsonl"
s3_client.put_object(
  bucket: S3_BUCKET_NAME,
  key:  "orders/#{orders_file_name}",
  body: File.read("path/to/#{orders_file_name}"),
  content_type: 'application/json'
)

puts "Successfully uploaded object 'orders/#{orders_file_name}' to bucket '#{S3_BUCKET_NAME}'..."
