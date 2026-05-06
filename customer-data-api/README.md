<!-- markdownlint-disable no-duplicate-heading -->
# PostPilot Customer Data & Targeting API

The PostPilot API enables you to manage customer data and trigger targeted direct mail campaigns programmatically.

## What you can do

* **Import customer contacts** with full postal and email data
* **Sync customer events** from your platform (purchases, signups, custom actions)
* **Trigger campaigns** via API-driven segments based on customer behavior and attributes

## Endpoint Reference

* [Email Contacts (MailMatch via API)](./email-contacts.md) — Submit email-only contacts; PostPilot resolves the address.
* [Full Address Contacts](./full-address-contacts.md) — Submit complete customer records with verified postal addresses.
* [Shopify Customer Events](./shopify-customer-events.md) — Track Shopify customer events to trigger behavior-based sends.
* [Legacy Flow Trigger (deprecated)](./legacy-flow-trigger.md) — Original flow-based trigger, kept for backwards compatibility.

## Getting Started

1. Log in to your PostPilot account.
2. Navigate to **Integrations → API Connection**.
3. Click **Manage** under the API Connection card.
4. Click **New Connection** (or select an existing one).
5. Copy your API key from the **Developer Access** section.

## Base URL

| Environment | URL                          |
|-------------|------------------------------|
| Production  | `https://api.postpilot.com`  |

## Authentication

All API requests authenticate via the API key embedded in the URL path:

```http
POST https://api.postpilot.com/v1/{api_key}/{endpoint}
```

The API key is a connection token generated when you create an API Connection in PostPilot. It serves as both
identification and authorization — no additional headers are required.

> **Security:** Do not share your API connection URLs. Anyone with the URL can call the API on your behalf. You can
> regenerate (rotate) your API key at any time from the **Developer Access** screen — rotating invalidates the previous
> key.

## Endpoint Families

| Endpoint                   | Path                      | Best For                                         | Requires Address? |
|----------------------------|---------------------------|--------------------------------------------------|-------------------|
| MailMatch via API          | `api_email_contact`       | Email-only contacts; PostPilot resolves address  | No                |
| Full Contact               | `api_full_contact`        | Contacts with a complete mailing address         | Yes               |
| Shopify Customer Events    | `shopify_customer_event`  | Triggering sends to existing Shopify customers   | No (uses Shopify data) |

## Custom Fields

All three endpoints support up to 3 custom fields (`custom_1`, `custom_2`, `custom_3`) for:

* **Personalizing postcard content** — pass dynamic values (pet name, product, offer code) and reference them as
  dynamic variables in your postcard design.
* **Advanced segmentation** — filter segments by custom field values to route contacts to different campaigns
  (e.g., `custom_1: "email_unsubscribed"`).

## API Logs

PostPilot provides a built-in **API Logs** screen (available in the API Connection area) showing the last 48 hours of
API calls. Use it to troubleshoot new integrations.

## Migration Note

API-triggered segments replace the older flow-based API approach. Existing flow trigger URLs remain
backwards-compatible, but all new API-driven campaigns should use segments. See the
[help article](https://help.postpilot.com/knowledge/api-triggered-segments-mailmatch-via-api) for migration guidance.

## Postman Collection

A Postman collection covering every endpoint in this reference is checked in alongside this guide:

* [`PostPilot-Customer-Data-and-Targeting.postman_collection.json`](./resources/PostPilot-Customer-Data-and-Targeting.postman_collection.json)

Import the collection, set the `api_key` variable on the collection, and you can issue requests against the Production
base URL immediately.

## Resources

* [API-Triggered Segments & MailMatch via API](https://help.postpilot.com/knowledge/api-triggered-segments-mailmatch-via-api)
* [Creating an API Connection](https://help.postpilot.com/knowledge/creating-an-api-connection-for-external-use)
* [Using an External API Connection in Flows (legacy)](https://help.postpilot.com/knowledge/using-an-external-api-connection-in-flows)
