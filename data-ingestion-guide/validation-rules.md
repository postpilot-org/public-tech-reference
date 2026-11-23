# Validation Rules

We validate incoming data and may skip invalid records.

## File Names

Give every upload a name nobody has used before, built from the date and UTC time of the upload:

* `customers/customers_YYYYMMDD_HHMMSS.jsonl`, e.g. `customers_20261123_140512.jsonl`
* `orders/orders_YYYYMMDD_HHMMSS.jsonl`, e.g. `orders_20261123_140512.jsonl`

If a second file arrives on the same UTC day with the same name as an earlier one, it replaces the earlier file and
the earlier file's records may never load. No error is returned. A date-only name like `orders_20261123.jsonl`
works for a once-a-day sync, but any extra upload that day (a history backfill, a re-send, a manual test) needs its
own name. If your tool splits an export into parts, keep the part number in the name too.

## Files That Won't Be Processed

A file is not processed if:

* The file name does not end in `.jsonl`. The upload succeeds and no error is returned, but the file is never picked
  up. Name files as described in [File Names](#file-names).
* More than **100** lines are not valid JSON, e.g. unescaped `"` or `\`, or a raw line break inside a value. Build
  each line with a JSON serializer (`json.dumps`, `JSON.stringify`, etc.), not string concatenation.
* File size exceeds **1 GB**.

## Records That Are Skipped

A record is skipped if:

* A required field is missing or null.
* Date fields are not valid ISO 8601 strings.
* An email field is not a valid email address.
* `country_code` is not a 2-letter uppercase ISO 3166-1 code, e.g. `US`.
* Order `total_price` is not greater than 0. Leave refunds, returns and $0 orders out.
* Order `line_items` is empty.
* Customer `full_name` is shorter than 4 characters or contains characters other than letters, spaces, apostrophes,
  hyphens and periods.

A record is also skipped if its mailing address (the customer record, or the order's `shipping_address`) fails these:

* `line1` is blank.
* `company` is blank and `full_name` isn't a first and last name in plain A-Z letters. Accents and non-Latin
  characters aren't supported, e.g. `José García` is skipped unless `company` is set.
* `full_name` or `company` is over 40 characters, or `line1`, `line2`, `city` or `state` is over 200.
* US addresses: `city` or `state` is blank, `state` isn't a 2-letter code like `CA`, `postal_code` isn't a 5-digit ZIP
  like `92618` or `92618-1234` (or is `00000`), `line1` is only dashes, or `line1` or `line2` is over 64 characters.
* UK addresses: `postal_code` isn't a valid UK postcode like `SW1A 1AA`.

## Other Checks

* Numeric fields (**total_price**, **price**) are JSON numbers, not strings, with at most **2 decimal places**.
* **customer_id** in orders corresponds to an existing (or separately provided) customer.
* `id` and `customer_id` contain no PII. Numeric or system IDs are fine as-is; hash an email address or other
  personal data used as an ID (any method, same value in both files).

## JSON Schema

[schemas/customers.schema.json](./schemas/customers.schema.json) and
[schemas/orders.schema.json](./schemas/orders.schema.json) describe one line of each file (JSON Schema 2020-12). They
cover the per-record rules above and work with any JSON Schema validator.

## Validate Before Uploading

[validate-feed.py](./code/validate-feed.py) checks your files locally before upload. It validates each record against
the JSON Schemas above, then adds the file-level checks a schema can't express: unreadable-line count, duplicate IDs
and `customer_id` matching. It needs Python 3.11+ and the `jsonschema` package, makes no network calls, and reports
line numbers and field names only, never field values, so its output is safe to share with PostPilot.

Download the whole `data-ingestion-guide` folder (the script reads the schemas from `../schemas`), then:

```shell
python3 -m pip install jsonschema
python3 code/validate-feed.py customers_20250327.jsonl orders_20250327.jsonl
```

Exit code `0` means no errors. Pass a customers and orders file together to also check that every order's
`customer_id` matches a customer `id`.

To see what it reports, run it on the fake files in [code/samples](./code/samples/README.md).
