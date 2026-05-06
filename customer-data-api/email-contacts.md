<!-- markdownlint-disable no-duplicate-heading -->
# Email Contacts (MailMatch via API)

Import customer email addresses to be enriched with postal data through PostPilot's address-append service.

## When to use

* You only have customer emails (no physical addresses).
* You want PostPilot to find and append mailing addresses automatically.

## How it works

1. Submit email addresses to the `api_email_contact` endpoint.
2. PostPilot matches each email to a postal address using data partners.
3. Matched contacts enter your segment and are picked up by your campaign.

## Match Rates

Typical match rates range from **30–50%**, depending on data quality and geography. B2B lists, international records,
and corporate emails tend to perform lower (~20–25%).

## Best for

Email lists, newsletter subscribers, digital-first customer bases, and any brand with an ESP that wants to run direct
mail without collecting physical addresses.

## Endpoint

```http
POST https://api.postpilot.com/v1/{api_key}/api_email_contact
Content-Type: application/json
```

## Request Fields

| Field        | Type   | Required    | Notes                                                                |
|--------------|--------|-------------|----------------------------------------------------------------------|
| `email`      | string | ✅ Required  | The customer's email address.                                        |
| `fullname`   | string | ⬜ Optional | Customer's full name. Improves match accuracy when provided.         |
| `custom_1`   | string | ⬜ Optional | Custom field for segmentation or postcard personalization.           |
| `custom_2`   | string | ⬜ Optional | Custom field for segmentation or postcard personalization.           |
| `custom_3`   | string | ⬜ Optional | Custom field for segmentation or postcard personalization.           |

> **Tip:** Use `custom_1` to differentiate event types when replacing multiple flows with a single endpoint
> (e.g., `"custom_1": "email_unsubscribed"`).

## Response

On success, PostPilot creates or updates the contact record. The contact will enter any matching API Email Contact
segment and be picked up by the associated campaign.

```jsonc
{
  "success": true
}
```

## Examples

### Minimal — email only

```http
POST /v1/{api_key}/api_email_contact
Content-Type: application/json
```

```jsonc
{
  "email": "jane.doe@example.com"
}
```

### Full — with name and custom fields

```http
POST /v1/{api_key}/api_email_contact
Content-Type: application/json
```

```jsonc
{
  "email": "jane.doe@example.com",
  "fullname": "Jane Doe",
  "custom_1": "VIP Customer",
  "custom_2": "Newsletter Subscriber",
  "custom_3": "Premium Plan"
}
```

## See Also

* [API-Triggered Segments & MailMatch via API](https://help.postpilot.com/knowledge/api-triggered-segments-mailmatch-via-api)
* [Full Address Contacts](./full-address-contacts.md) — for contacts with complete addresses already on hand.
