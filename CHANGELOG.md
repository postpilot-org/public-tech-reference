# `public-tech-reference` Changelog

_The following sections summarize the changes made throughout this project (by topic) and include the approximate date_
_each of the changes were made._

## `Data Ingestion Guide`

### [06/22/2026]

* Adds `Data Ingestion FAQ` section to address common customer issues.

### [05/05/2026]

* Adds `Customers Schema` documentation.
* Adds `Orders Schema` documentation.
* Readme updates to include links to new schema documentation and example scripts.

### [04/28/2026]

* Adds `Data Exchange via Amazon S3` documentation.
* Adds Ruby/Python example scripts for S3 file uploads via AWS cross-account configuration.
* Adds Ruby/Python example scripts for S3 file uploads via GCP ServiceAccount OIDC federated identity.

## `Customer Data & Targeting API`

### [05/06/2026]

* Adds `Customer Data & Targeting API` reference, covering the `api_email_contact`, `api_full_contact`, and
  `shopify_customer_event` endpoints, plus the legacy `send_to_customer` flow trigger.
* Includes the `PostPilot — Customer Data & Targeting` Postman collection under
  `customer-data-api/resources/`.
* Root `README.md` updated to link to the new API reference.
