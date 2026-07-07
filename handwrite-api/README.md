<!-- markdownlint-disable no-duplicate-heading -->
# Handwrite.io API

The Handwrite.io API enables you to send real, robot-penned handwritten letters programmatically — pick a handwriting
style and stationery, submit a message and recipients, and track each order through to mailing.

## What you can do

* **List handwriting styles** available to your account.
* **List stationery/cards** available to your account.
* **Send handwritten letters** to one or many recipients, individually or in batches.
* **Track orders** through their lifecycle (`processing` → `written` → `complete`).

## Endpoint Reference

* [Handwriting Styles](./handwriting-styles.md) — List the handwriting styles available to your account.
* [Stationery](./stationery.md) — List the stationery/cards available to your account.
* [Send a Letter](./send-letter.md) — Send one or more handwritten letters.
* [Orders](./orders.md) — Retrieve an order and check its status and proofs.

## Base URL

| Environment | URL                             |
|-------------|---------------------------------|
| All         | `https://api.handwrite.io/v1`   |

There is a single base URL — the environment is determined by the API key you authenticate with (see below).

## Authentication

All requests require your API key in the `Authorization` header:

```http
GET https://api.handwrite.io/v1/handwriting
Authorization: {api_key}
Content-Type: application/json
```

Keys are environment-prefixed:

| Prefix     | Environment | Notes                                        |
|------------|-------------|----------------------------------------------|
| `test_hw`  | Testing     | No usage charges; letters are not mailed.    |
| `live_hw`  | Production  | Charged per your plan; letters are mailed.   |

> **Security:** Treat API keys as secrets. Do not commit them to source control or expose them in client-side code.

## Rate Limiting

The API allows **60 requests per minute** per API key. Every response includes rate-limit headers:

| Header                  | Meaning                              |
|-------------------------|--------------------------------------|
| `X-RateLimit-Limit`     | Maximum requests per minute.         |
| `X-RateLimit-Remaining` | Requests remaining in the window.    |
| `X-RateLimit-Reset`     | When the current window resets.      |

Exceeding the limit returns **HTTP 429** with a `rate_limit_exceeded` error. For high-volume sends, prefer the
[batch mode](./send-letter.md#batch-mode) of the `send` endpoint (up to 1,000 orders per request) over many
single-recipient calls.

## HTTP Response Codes

| Code | Meaning                                        |
|------|------------------------------------------------|
| 200  | Success                                        |
| 400  | Bad Request — invalid parameters.              |
| 401  | Unauthorized — invalid or missing API key.     |
| 404  | Not Found — resource doesn't exist.            |
| 429  | Too Many Requests — rate limit exceeded.       |
| 500  | Internal Server Error                          |
| 503  | Service Unavailable — maintenance.             |

## Typical Workflow

1. `GET /handwriting` — choose a handwriting style `_id`.
2. `GET /stationery` — choose a card `_id`.
3. `POST /send` — submit your message, style, card, and recipient(s).
4. `GET /order/{orderId}` — poll order status and retrieve proof images.

## Postman Collection

A Postman collection covering every endpoint in this reference is checked in alongside this guide:

* [`Handwrite.io-API.postman_collection.json`](./resources/Handwrite.io-API.postman_collection.json)

Import the collection and set the `apiKey` collection variable (the `baseUrl` variable is pre-set to Production). The
`orderId` variable feeds the **Get an Order** request.

## Resources

* [Official Handwrite.io API documentation](https://documentation.handwrite.io/)
