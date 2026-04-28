<!-- markdownlint-disable no-duplicate-heading -->
# Data Transfer via S3

To support secure B2B data transfer operations from customers, PostPilot supports encrypted file drops via Amazon S3.

## Design Notes

* PostPilot currently supports two forms of S3 Bucket access via IAM Role:
  * [Authorization via AWS Cross-Account Access from Customer's AWS Infrastructure](#trust-policy-aws-cross-account)
  * [Authorization via GCP ServiceAccount OIDC Federated Identity](#trust-policy-gcp-serviceaccount-federated-identity)
* Each customer is issued a dedicated S3 Bucket, IAM Role and accompanying KMS Key to which only the customer (and
  PostPilot) has access to. This ensures maximum customer data security while hosted in PostPilot cloud infrastructure.
* All customer Data Feed infrastructure is maintained within a single AWS account. Data files are then shared and
  transferred to other AWS and/or GCP accounts within the PostPilot organization. This allows PostPilot to isolate
  customer access to a single account without having to grant customer or 3rd party access to other accounts containing
  production workloads.
* All customer data files are transitioned from S3 `Standard` storage class to `One-Zone Infrequent Access` after 30
  days to minimize storage costs. Additionally, all customer data files are permanently deleted after 90 days via S3
  Object Lifecycle Policy. The 90-day expiration window is maintained in case any troubleshooting tasks are necessary
  that may require re-running files, etc.

## Trust Policy: AWS Cross-Account

To configure AWS cross-account access, customers are required to provide two data elements for proper configuration of
the dedicated IAM Role trust policy.

* The customer's 12-digit AWS Account Number required for the cross-account IAM Role trust policy grant.
  * _This is the account number from which the client will be making the `aws sts assume-role` request._
* A customer-generated static token to be presented with every `aws sts assume-role` request.
  * _A 20-character (minimum) random alphanumeric string is required._
  * _Example Shell Script: [token.example.rb](./code/token.example.rb)_

```jsonc
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "CustomerCrossAccountTrustPolicy",
      "Effect": "Allow",
      "Action": "sts:AssumeRole",
      "Principal": {
        "AWS": "arn:aws:iam::{CUST_ACCT_NUM}:root"
      },
      "Condition": {
        "StringEquals": {
          "sts:ExternalId": "{20_CHAR_TOKEN}"
        }
      }
    }
  ]
}
```

### References

* [AWS Docs: Cross-Account Confused Deputy Prevention][confused-deputy-prevention]

[confused-deputy-prevention]: https://docs.aws.amazon.com/IAM/latest/UserGuide/confused-deputy.html#mitigate-confused-deputy

## Trust Policy: GCP ServiceAccount Federated Identity

To configure AWS access via a GCP OIDC Federated ServiceAccount identity, customers are required to provide the GCP
ServiceAccount ID for proper configuration of the dedicated IAM Role trust policy.

```jsonc
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "CustomerGCPTrustPolicy",
      "Effect": "Allow",
      "Principal": {
          "Federated": "accounts.google.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "accounts.google.com:oaud": "postpilot-data-feed...",
          "accounts.google.com:sub": "{CUST_GCP_SA_ID_NUM}",
          "accounts.google.com:aud": "{CUST_GCP_SA_ID_NUM}"
        }
      }
    }
  ]
}
```

### References

* [AWS Security Blog: Access AWS Using a GCP Native Workload Identity][access-aws-using-gcp-identity]

[access-aws-using-gcp-identity]: https://aws.amazon.com/blogs/security/access-aws-using-a-google-cloud-platform-native-workload-identity/

## Customer IAM Role

_The AWS IAM Role below is helpful for customers to determine permitted operations via S3/KMS clients as well as to_
_identify the appropriate JSON file locations._

```jsonc
// "{PP_CUST_ID} indicates internal PostPilot CustomerID
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "CustomerDataFeedS3BucketAccess",
      "Effect": "Allow",
      "Action": [
        "s3:ListBucketMultipartUploads",
        "s3:ListBuckets",
        "s3:ListObjects"
      ],
      "Resource": "arn:aws:s3:::postpilot-data-feed-{PP_CUST_ID}"
    },
    {
      "Sid": "CustomerDataFeedS3ObjectAccess",
      "Effect": "Allow",
      "Action": [
          "s3:AbortMultipartUpload",
          "s3:GetObject",
          "s3:ListMultipartUploadParts",
          "s3:PutObject"
      ],
      "Resource": [
          "arn:aws:s3:::postpilot-data-feed-{PP_CUST_ID}/orders/orders*.jsonl",
          "arn:aws:s3:::postpilot-data-feed-{PP_CUST_ID}/orders/orders*.json",
          "arn:aws:s3:::postpilot-data-feed-{PP_CUST_ID}/customers/customers*.jsonl",
          "arn:aws:s3:::postpilot-data-feed-{PP_CUST_ID}/customers/customers*.json"
      ]
    },
    {
        "Sid": "CustomerDataFeedKMSAccess",
        "Effect": "Allow",
        "Action": [
            "kms:Decrypt",
            "kms:DescribeKey",
            "kms:Encrypt",
            "kms:GenerateDataKey"
        ],
        "Resource": "arn:aws:kms:us-east-2:000000000000:key/mrk-00000000000000000000000000000000"
    }
  ]
}
```

## Example Scripts

Example scripts written in Python and Ruby provide a complete example of the AWS SDK operations required to upload
`customer/customers_YYYYMMDD.jsonl` and `orders/orders_YYYYMMDD.jsonl` files to the customer's S3 Bucket. These scripts
can be easily modified with customer-specific parameters for initial testing purposes.

### Python Scripts

* [Upload via AWS Cross-Account Access](./code/aws-cross-account.example.py)
* [Upload via GCP Federated Identity](./code/gcp-federated-id.example.py)

### Ruby Scripts

* [Upload via AWS Cross-Account Access](./code/aws-cross-account.example.rb)
* [Upload via GCP Federated Identity](./code/gcp-federated-id.example.rb)
