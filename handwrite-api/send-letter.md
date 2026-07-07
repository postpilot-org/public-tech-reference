<!-- markdownlint-disable no-duplicate-heading -->
# Send a Letter

Send one or more handwritten letters. Requires a handwriting style ID and a stationery ID — fetch those first from
[Handwriting Styles](./handwriting-styles.md) and [Stationery](./stationery.md).

## Endpoint

```http
POST https://api.handwrite.io/v1/send
Authorization: {api_key}
Content-Type: application/json
```

## Request Fields

| Field         | Type   | Required    | Notes                                                          |
|---------------|--------|-------------|----------------------------------------------------------------|
| `message`     | string | ✅ Required  | The letter body. **Max 320 characters.**                      |
| `handwriting` | string | ✅ Required  | Handwriting style `_id` (from `GET /handwriting`).            |
| `card`        | string | ✅ Required  | Stationery `_id` (from `GET /stationery`).                    |
| `recipients`  | array  | ✅ Required  | 1–10 recipient objects. Each recipient receives the letter.   |
| `from`        | object | ⬜ Optional | Return address printed on the envelope.                        |

### Recipient object

| Field       | Type   | Required    | Notes                                        |
|-------------|--------|-------------|----------------------------------------------|
| `street1`   | string | ✅ Required  | Address line 1.                             |
| `city`      | string | ✅ Required  |                                             |
| `state`     | string | ✅ Required  | 2-letter capitalized abbreviation (e.g., `CA`). |
| `zip`       | string | ✅ Required  | Exactly 5 digits.                           |
| `firstName` | string | ⬜ Optional |                                              |
| `lastName`  | string | ⬜ Optional |                                              |
| `company`   | string | ⬜ Optional |                                              |
| `street2`   | string | ⬜ Optional | Address line 2 (apt, suite, etc.).           |

### From object

All fields optional: `firstName`, `lastName`, `street1`, `street2`, `city`, `state`, `zip`.

## Batch Mode

The endpoint also accepts an **array** of message objects (each with its own `message`, `handwriting`, `card`,
`recipients`, and optional `from`). A single batch request may produce at most **1,000 orders** (message × recipient
combinations). Prefer batching over many single calls to stay within the
[rate limit](./README.md#rate-limiting).

## Response

Returns an array of created order objects — one per recipient:

```jsonc
[
  {
    "_id": "5dba45e8f2b173cb5dff0300",
    "message": "Hey dude,\nIt was great meeting you last week at the party. We'd love to have you back at the next one!\n\nBest,\n-Jackie",
    "to": {
      "firstName": "The",
      "lastName": "Dude",
      "company": "Unemployed",
      "street1": "25 Main Street",
      "city": "Los Angeles",
      "state": "CA",
      "zip": "90210"
    },
    "from": {
      "firstName": "Jackie",
      "lastName": "Treehorn",
      "street1": "1 Random Street",
      "street2": "Apt 33A",
      "city": "Malibu",
      "state": "CA",
      "zip": "90263"
    },
    "status": "processing",
    "handwriting": "5db6f0724cc1751452c5ae8e",
    "card": "5db6f0724cc1751452c5ae8e",
    "createdAt": "2019-10-31T02:24:40.648Z"
  }
]
```

Store each returned `_id` — it is the `orderId` used to [track the order](./orders.md).

## Examples

### Single recipient with return address

```http
POST /v1/send
Authorization: {api_key}
Content-Type: application/json
```

```jsonc
{
  "message": "Hey dude,\nIt was great meeting you last week at the party. We'd love to have you back at the next one!\n\nBest,\n-Jackie",
  "handwriting": "5db6f0724cc1751452c5ae8e",
  "card": "5db6f1854cc1751452c5ae93",
  "recipients": [
    {
      "firstName": "The",
      "lastName": "Dude",
      "company": "Unemployed",
      "street1": "25 Main Street",
      "city": "Los Angeles",
      "state": "CA",
      "zip": "90210"
    }
  ],
  "from": {
    "firstName": "Jackie",
    "lastName": "Treehorn",
    "street1": "1 Random Street",
    "street2": "Apt 33A",
    "city": "Malibu",
    "state": "CA",
    "zip": "90263"
  }
}
```

### Minimal — one recipient, no return address

```jsonc
{
  "message": "Thanks for your first order — it means a lot to a small shop like ours!",
  "handwriting": "5db6f0724cc1751452c5ae8e",
  "card": "5db6f1854cc1751452c5ae93",
  "recipients": [
    {
      "street1": "25 Main Street",
      "city": "Los Angeles",
      "state": "CA",
      "zip": "90210"
    }
  ]
}
```

## See Also

* [Orders](./orders.md) — track the letters you just sent.
* [Handwriting Styles](./handwriting-styles.md) / [Stationery](./stationery.md) — source the required IDs.
