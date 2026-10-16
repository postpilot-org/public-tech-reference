# Validator Samples

Fake records (`example.com` addresses) for trying [validate-feed.py](../validate-feed.py).

```shell
python3 validate-feed.py samples/customers_sample.jsonl samples/orders_sample.jsonl            # passes, exit 0
python3 validate-feed.py samples/customers_with_errors.jsonl samples/orders_with_errors.jsonl  # fails, exit 1
```

## customers_with_errors.jsonl

| Line | Problem | Reported as |
|---|---|---|
| 1 | None | |
| 2 | Email address as `id` | Must fix |
| 3 | Unescaped `"` in `full_name` | Unreadable |
| 4 | Invalid `email` | Skipped |
| 5 | `country_code` is `usa` | Skipped |
| 6 | `full_name` under 4 characters | Skipped |
| 7 | `created_at` is `03/14/2025` | Skipped |
| 8 | `created_at` has no time zone | Warning |
| 9 | `city` missing | Skipped |
| 10 | `id` sent as a number | Warning |
| 11 | `id` repeats line 1 | Warning |
| 12 | `updated_at` before `created_at` | Warning |
| 13-14 | Raw line break inside `line1` splits one record in two | Unreadable (both) |
| 15 | Unescaped `\` in `line1` | Unreadable |
| 16 | Trailing comma | Unreadable |
| 17 | Unknown field `Tags` | Note |
| 18 | Blank `line1` | Skipped |
| 19 | `metadata` is a string | Unreadable |

## orders_with_errors.jsonl

| Line | Problem | Reported as |
|---|---|---|
| 1 | None | |
| 2 | `customer_id` is `guest-<email>` | Must fix |
| 3 | `total_price` is 0 | Skipped |
| 4 | `total_price` is negative (refund) | Skipped |
| 5 | `total_price` sent as text | Warning |
| 6 | `total_price` has 3 decimals | Warning |
| 7 | `currency` is `usd` | Warning |
| 8 | `line_items` empty | Skipped |
| 9 | `total_price` equals one line item | Warning |
| 10 | `billing_address.country_code` is `United States` | Skipped |
| 11 | `shipping_address` missing | Skipped |
| 12 | Double comma | Unreadable |
| 13 | `quantity` is 1.5 | Unreadable |
| 14 | `quantity` is 0 | Warning |
| 15 | Top-level `email` missing | Warning |
| 16 | `customer_id` matches no customer | Customers/orders check |
| 17 | Dates in the future | Warning |

Run together, the two error files match 8 of 15 readable orders to a customer. The other 7 point at a customer that
doesn't exist (line 16), an unreadable customers line (`cust_1003`), or a customer whose `id` was changed by one of
the errors above (email, number, duplicate), plus the `guest-<email>` order.
