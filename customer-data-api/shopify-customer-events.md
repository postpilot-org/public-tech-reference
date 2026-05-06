<!-- markdownlint-disable no-duplicate-heading -->
# Shopify Customer Events

Track custom customer events and behaviors for Shopify customers to enable behavior-based targeting.

## When to use

* You have Shopify customers already synced to PostPilot.
* You want to trigger campaigns based on custom events (e.g., abandoned cart, product view, milestone reached).

## How it works

1. Your platform sends an event (email or Shopify customer ID) to the `shopify_customer_event` endpoint.
2. PostPilot links the event to the existing Shopify customer record.
3. The customer enters any matching "API Shopify customer event occurred" segment.
4. The associated campaign picks them up and sends a postcard.

## Use cases

* Send direct mail after specific customer actions.
* Target based on browsing behavior or purchase milestones.
* Trigger winback cards on subscription pause / cancel.
* Follow up support interactions with a handwritten note.

## Best for

Shopify brands using external platforms (Braze, Bloomreach, Gorgias, Recharge, etc.) that can fire webhooks or API
calls based on customer behavior.

## Endpoint

```http
POST https://api.postpilot.com/v1/{api_key}/shopify_customer_event
Content-Type: application/json
```

## Request Fields

Provide exactly one identifier (`email` **OR** `customer_id`).

| Field         | Type   | Required        | Notes                                                                                       |
|---------------|--------|-----------------|---------------------------------------------------------------------------------------------|
| `email`       | string | ⚠️ One of two   | Customer's email address. PostPilot matches to the Shopify customer via email.              |
| `customer_id` | string | ⚠️ One of two   | Shopify customer ID. More precise than email matching when available.                       |
| `custom_1`    | string | ⬜ Optional     | Event metadata (e.g., loyalty tier, product category) for segmentation or personalization.  |
| `custom_2`    | string | ⬜ Optional     | Additional event metadata.                                                                  |
| `custom_3`    | string | ⬜ Optional     | Additional event metadata.                                                                  |

> **Tip:** Use custom fields to store event context like cart value, product category, or customer tier — useful for
> filtering in PostPilot segments.

## Response

```jsonc
{
  "success": true
}
```

## Examples

### Identify by email

```http
POST /v1/{api_key}/shopify_customer_event
Content-Type: application/json
```

```jsonc
{
  "email": "customer@example.com"
}
```

### Identify by Shopify customer ID

```http
POST /v1/{api_key}/shopify_customer_event
Content-Type: application/json
```

```jsonc
{
  "customer_id": "shopify_customer_123456",
  "custom_1": "Loyalty Member",
  "custom_2": "Preferred Customer",
  "custom_3": "Birthday: March 15"
}
```

### Email plus custom event metadata

```http
POST /v1/{api_key}/shopify_customer_event
Content-Type: application/json
```

```jsonc
{
  "email": "customer@example.com",
  "custom_1": "Loyalty Member",
  "custom_2": "Preferred Customer",
  "custom_3": "Birthday: March 15"
}
```

## Custom field patterns

| `custom_1` value          | Example campaign                       |
|---------------------------|----------------------------------------|
| `cart_abandoned`          | Abandoned cart postcard.               |
| `subscription_paused`     | Winback card.                          |
| `vip_tier_gold`           | Loyalty reward mailer.                 |

## See Also

* [Full Address Contacts](./full-address-contacts.md) — to import the full customer record before triggering events.
* [Email Contacts (MailMatch via API)](./email-contacts.md) — when no Shopify customer record exists.
