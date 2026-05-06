<!-- markdownlint-disable no-duplicate-heading -->
# Full Address Contacts

Import complete customer records with verified postal addresses and email data.

## When to use

* You have full customer information (email + mailing address).
* You're syncing from e-commerce platforms, CRMs, or order systems.

## Best for

E-commerce orders, CRM exports, and platforms with full customer data.

## Endpoint

```http
POST https://api.postpilot.com/v1/{api_key}/api_full_contact
Content-Type: application/json
```

## Request Fields

| Field          | Type   | Required          | Notes                                                                                |
|----------------|--------|-------------------|--------------------------------------------------------------------------------------|
| `reference_id` | string | ✅ Required       | Unique identifier for the recipient (often the customer email or internal ID).       |
| `fullname`     | string | ⚠️ One of three   | Customer's full name. Use **OR** `firstname`+`lastname` **OR** `company`.            |
| `firstname`    | string | ⚠️ One of three   | Customer's first name (use with `lastname`).                                         |
| `lastname`     | string | ⚠️ One of three   | Customer's last name (use with `firstname`).                                         |
| `company`      | string | ⚠️ One of three   | Company name (use when sending to a business).                                       |
| `line1`        | string | ✅ Required       | Street address line 1.                                                               |
| `line2`        | string | ⬜ Optional       | Street address line 2 (apt, suite, etc.).                                            |
| `city`         | string | ✅ Required       | City.                                                                                |
| `state`        | string | ✅ Required (US)  | USPS two-character state abbreviation. Optional or used for province on intl. sends. |
| `postal_code`  | string | ✅ Required       | ZIP / postal code in the destination country's format.                               |
| `country`      | string | ✅ Required       | ISO 3166 two-character country code (e.g., `US`, `DE`, `GB`, `CA`).                  |
| `email`        | string | ⬜ Optional       | Customer's email address.                                                            |
| `custom_1`     | string | ⬜ Optional       | Custom field for segmentation or postcard personalization.                           |
| `custom_2`     | string | ⬜ Optional       | Custom field for segmentation or postcard personalization.                           |
| `custom_3`     | string | ⬜ Optional       | Custom field for segmentation or postcard personalization.                           |

### Name field rules

Provide exactly **one** of:

* `fullname` — e.g., `"John Smith"`
* `firstname` + `lastname` — e.g., `"John"` / `"Smith"`
* `company` — e.g., `"Acme Corp"`

### Address format

* `state` must be a standard USPS two-character abbreviation (e.g., `NY`, `CA`).
* `country` must be a standard ISO 3166 two-character country code (e.g., `US`, `DE`).
* `postal_code` should match the destination country format.

## Response

```jsonc
{
  "success": true
}
```

## Examples

### Full — US address with all fields

```http
POST /v1/{api_key}/api_full_contact
Content-Type: application/json
```

```jsonc
{
  "reference_id": "customer_12345",
  "email": "john.smith@example.com",
  "fullname": "John Smith",
  "line1": "123 Main Street",
  "line2": "Apt 4B",
  "city": "New York",
  "state": "NY",
  "postal_code": "10001",
  "country": "US",
  "custom_1": "Premium Member",
  "custom_2": "Loyalty Program",
  "custom_3": "Birthday: Jan 15"
}
```

### First name / last name format

```http
POST /v1/{api_key}/api_full_contact
Content-Type: application/json
```

```jsonc
{
  "reference_id": "customer_67890",
  "email": "maria.santos@example.com",
  "firstname": "Maria",
  "lastname": "Santos",
  "line1": "456 Oak Avenue",
  "city": "Los Angeles",
  "state": "CA",
  "postal_code": "90001",
  "country": "US"
}
```

### International address

International formats vary. Provide as much detail as available in `line1` and `line2`. The `state` field may be omitted
or used for a province / region as appropriate to the destination.

```http
POST /v1/{api_key}/api_full_contact
Content-Type: application/json
```

```jsonc
{
  "reference_id": "customer_intl_001",
  "email": "thomas.mueller@example.com",
  "fullname": "Thomas Mueller",
  "line1": "Berliner Strasse 123",
  "postal_code": "10115",
  "country": "DE"
}
```

### Minimal required fields

```http
POST /v1/{api_key}/api_full_contact
Content-Type: application/json
```

```jsonc
{
  "reference_id": "ref_minimal_001",
  "fullname": "Jane Wilson",
  "line1": "789 Elm Street",
  "city": "Chicago",
  "state": "IL",
  "postal_code": "60601",
  "country": "US"
}
```

## See Also

* [Email Contacts (MailMatch via API)](./email-contacts.md) — when you only have email addresses.
* [Shopify Customer Events](./shopify-customer-events.md) — to trigger sends to customers already in PostPilot.
