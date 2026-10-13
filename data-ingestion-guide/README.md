# PostPilot Customer Data Ingestion Guide

## Overview

* Transport: AWS S3
* File format: JSONL (one JSON object per line)
* Encoding: UTF-8
* Date/time format: ISO 8601 (e.g. 2025-03-27T10:15:00Z)
* Decimals: 2-digit precision (e.g. 129.99)
* Max file size: 1 GB per file
* Minimum sync interval: every 60 minutes
* Data types:
  * Customers
  * Orders(with nested line items)

## Documentation

* [Data Exchange FAQ](data-exchange-faq.md)
* [Data Exchange via Amazon S3](data-exchange-via-amazon-s3.md)
* [File Reference: Customers](file-reference-customers.md)
* [File Reference: Orders](file-reference-orders.md)

## Sync Frequency & Windows

* Upload new/updated files to S3 at most every **60 minutes**.
* Each file should contain all new and updated records since the previous run.
* Overlapping windows (re-sending some records) is OK and recommended.
* Inserts and updates are treated as upserts based on your id.

## Validation Rules

We validate incoming data and may skip invalid records.

A file is rejected entirely if:

* The file name does not end in `.jsonl`.
* More than **100** lines are not valid JSON, e.g. unescaped `"` or `\`, or a raw line break inside a value. Build
  each line with a JSON serializer (`json.dumps`, `JSON.stringify`, etc.), not string concatenation.
* File size exceeds **1 GB**.

A record is skipped if:

* A required field is missing or null.
* Date fields are not valid ISO 8601 strings.
* An email field is not a valid email address.
* `country_code` is not a 2-letter uppercase ISO 3166-1 code, e.g. `US`.
* Order `total_price` is not greater than 0. Leave refunds, returns and $0 orders out.
* Order `line_items` is empty.
* Customer `full_name` is shorter than 4 characters or contains characters other than letters, spaces, apostrophes,
  hyphens and periods.

We also check:

* Numeric fields (**total_price**, **price**) have at most **2 decimal places**.
* **customer_id** in orders corresponds to an existing (or separately provided) customer.
* `id` and `customer_id` contain no PII. Numeric or system IDs are fine as-is; hash an email address or other
  personal data used as an ID (any method, same value in both files).

### Validate Before Uploading

[validate-feed.py](./code/validate-feed.py) runs these checks locally against your files before upload. It requires
Python 3.8+ with no dependencies, makes no network calls, and reports line numbers and field names only, never field
values, so its output is safe to share with PostPilot.

```shell
python3 validate-feed.py customers_20250327.jsonl orders_20250327.jsonl
```

Exit code `0` means no errors. Pass a customers and orders file together to also check that every order's
`customer_id` matches a customer `id`.

To see what it reports, run it on the fake files in [code/samples](./code/samples/README.md).
