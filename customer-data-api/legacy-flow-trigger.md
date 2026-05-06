<!-- markdownlint-disable no-duplicate-heading -->
# Legacy Flow Trigger (Deprecated)

> **Deprecated.** Use [Full Address Contacts](./full-address-contacts.md) or
> [Email Contacts (MailMatch via API)](./email-contacts.md) with segments instead.

The original API-triggered flow endpoint. New campaigns should use the segment-based endpoints documented elsewhere in
this reference.

## Backwards compatibility

Existing flow trigger URLs remain backwards-compatible. You do not need to change webhook URLs or JSON bodies in your
external system for simple setups already in production. **All new** API-driven campaigns should be built as segments
going forward.

## Integrations that should continue using flows

A handful of integrations cannot send the JSON bodies that segment-based endpoints require, or rely on flow-specific
processing. These should continue to use this endpoint:

* **Recharge** — does not support custom JSON bodies in webhooks.
* **Omnisend** — webhook does not support custom JSON bodies.
* **LoyaltyLion** — native flows integration handles formatting.
* **LifeMatch Birthday** — relies on a LifeMatch process only supported in flows.

## Endpoint

Each flow has its own unique trigger URL. The `api_key` path segment is **flow-specific** — it is an obfuscated
connection token issued when the flow is created. The URL is write-only and requires no additional authentication
headers.

```http
POST https://api.postpilot.com/v1/{api_key}/send_to_customer
Content-Type: application/json
```

## Request Fields

| Field          | Type   | Required          | Notes                                                                          |
|----------------|--------|-------------------|--------------------------------------------------------------------------------|
| `reference_id` | string | ✅ Required       | Unique identifier for the recipient (often the email address).                 |
| `fullname`     | string | ⚠️ One of three   | Customer's full name. Use **OR** `firstname`+`lastname` **OR** `company`.      |
| `firstname`    | string | ⚠️ One of three   | Customer's first name (use with `lastname`).                                   |
| `lastname`     | string | ⚠️ One of three   | Customer's last name (use with `firstname`).                                   |
| `company`      | string | ⚠️ One of three   | Company name (use when sending to a business).                                 |
| `line1`        | string | ✅ Required       | Street address.                                                                |
| `line2`        | string | ⬜ Optional       | Street address line 2 (apt, suite, etc.).                                      |
| `city`         | string | ✅ Required       | City.                                                                          |
| `state`        | string | ✅ Required       | USPS two-character state abbreviation.                                         |
| `postal_code`  | string | ✅ Required       | ZIP / postal code.                                                             |
| `country`      | string | ✅ Required       | ISO 3166 two-character country code.                                           |
| `email`        | string | ⬜ Optional       | Customer's email address.                                                      |

## Example

```http
POST /v1/{api_key}/send_to_customer
Content-Type: application/json
```

```jsonc
{
  "reference_id": "customer@example.com",
  "firstname": "John",
  "lastname": "Doe",
  "email": "customer@example.com",
  "line1": "123 Main St",
  "line2": "Apt 4",
  "city": "New York",
  "state": "NY",
  "postal_code": "10001",
  "country": "US"
}
```

## See Also

* [Using an External API Connection in Flows (legacy)](https://help.postpilot.com/knowledge/using-an-external-api-connection-in-flows)
* [API-Triggered Segments & MailMatch via API](https://help.postpilot.com/knowledge/api-triggered-segments-mailmatch-via-api) — recommended for new integrations.
