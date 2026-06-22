# Data Exchange: FAQ

## Frequently Asked Questions

### What are the steps or process for establishing data exchange via S3?

1. Customers work with their PostPilot sales representative to determine if establishing a dedicated external data
  exchange is right for their organization's needs. At this point in the process, the sales representative will have
  provisioned the customer's PostPilot account and share the customer's `PostPilot Account Number`.
1. Customer technical integration teams must review the ["Data Exchange via Amazon S3"][data-exchange-via-s3]
  documentation to determine which integration pattern is appropriate for their situation and tech stack:
  a. [AWS Cross-Account Access][data-exchange-aws]
  a. [GCP Federated ServiceAccount Identity][data-exchange-gcp]
1. Once the customer chooses the appropriate access pattern, they must share their AWS or GCP account details with their
   sales representative to be passed along to PostPilot's Cloud Infrastructure team.
1. PostPilot's Cloud Infrastructure team provisions the customer's S3 and security infrastructure and distributes the
   following infrastructure information for customer use:
  a. `S3 Bucket Name`
  a. `IAM Role ARN`
1. Customer is able to use the [Python or Ruby code examples][data-exchange-code] to begin automating and testing their
   data file drops.
1. Once access is verified and the customer is exchanging files successfully in S3, the data transfer job will be
   enabled to begin transferring the files for processing in PostPilot's ETL pipelines.

### I'm getting an HTTP 403 Response Code from my Upload Script... What's the Issue?

HTTP 403 error responses from the AWS SDK indicate that an S3 operation was attempted that is not allowed.

_Please refer to the [IAM Role Privileges][data-exchange-iam] granted to each customer and confirm the permitted S3_
_operations. To ensure a safe, secure and consistent environment for PostPilot customers, customer permissions are_
_highly restricted to allow only the operations required for file uploads._

[data-exchange-via-s3]: https://github.com/postpilot-org/public-tech-reference/blob/main/data-ingestion-guide/data-exchange-via-amazon-s3.md
[data-exchange-aws]: https://github.com/postpilot-org/public-tech-reference/blob/main/data-ingestion-guide/data-exchange-via-amazon-s3.md#trust-policy-aws-cross-account
[data-exchange-gcp]: https://github.com/postpilot-org/public-tech-reference/blob/main/data-ingestion-guide/data-exchange-via-amazon-s3.md#trust-policy-gcp-serviceaccount-federated-identity
[data-exchange-code]: https://github.com/postpilot-org/public-tech-reference/blob/main/data-ingestion-guide/data-exchange-via-amazon-s3.md#example-scripts
[data-exchange-iam]: https://github.com/postpilot-org/public-tech-reference/blob/main/data-ingestion-guide/data-exchange-via-amazon-s3.md#customer-iam-role
