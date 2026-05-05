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

## File Transfer
* [Data Exchange via Amazon S3](data-exchange-via-amazon-s3.md)

## Contracts & Schema
* 
* [File Reference: Customers](file-reference-customers.md)
* [File Reference: Orders](file-reference-orders.md)

## Sync Frequency & Windows
* Upload new/updated files to S3 at most every **60 minutes**.
* Each file should contain all new and updated records since the previous run.
* Overlapping windows (re-sending some records) is OK and recommended.
* Inserts and updates are treated as upserts based on your id.

## Validation Rules

We validate incoming data and may skip invalid records.

We check:

* Required fields are present.
* Date fields are valid ISO 8601 strings.
* Numeric fields (**total_price**, **price**) have at most **2 decimal places**.
* **customer_id** in orders corresponds to an existing (or separately provided) customer .
* File size does not exceed **1 GB**.

We recommend basic validation on your side before uploading.
