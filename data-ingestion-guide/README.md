# PostPilot Customer Data Ingestion Guide

## Overview

* Transport: AWS S3
* File format: JSONL (one JSON object per line)
* Encoding: UTF-8
* Date/time format: ISO 8601 (e.g. 2025-03-27T10:15:00Z)
* Amounts: JSON numbers (not strings) with up to 2 decimal places (e.g. 129.99 or 129.9)
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
* [Validation Rules](validation-rules.md)

## Sync Frequency & Windows

* Upload new/updated files to S3 at most every **60 minutes**.
* Each file should contain all new and updated records since the previous run.
* Overlapping windows (re-sending some records) is OK and recommended.
* Inserts and updates are treated as upserts based on your id.
* Send the complete record every time, not only the fields that changed. Each update replaces the stored record, and
  a record missing a required field is skipped.
* If the same id is sent more than once, the version with the latest `updated_at` is kept.
* The feed doesn't delete records. Leave deleted customers and orders out of later files.

## Validation Rules

We validate incoming data and may skip invalid records. See [Validation Rules](validation-rules.md) for what makes a
file go unprocessed or a record get skipped, the JSON Schemas, and a script to check your files before upload.
