<!-- markdownlint-disable no-duplicate-heading -->
# Orders

Retrieve a single order by its ID to check its status and download proof images. Order IDs are returned by
[Send a Letter](./send-letter.md).

## Endpoint

```http
GET https://api.handwrite.io/v1/order/{orderId}
Authorization: {api_key}
Content-Type: application/json
```

| URL Param  | Type   | Required    | Notes                                     |
|------------|--------|-------------|-------------------------------------------|
| `orderId`  | string | ✅ Required  | The `_id` returned when the letter was sent. |

## Order Status Values

| Status       | Meaning                                                        |
|--------------|----------------------------------------------------------------|
| `processing` | Order is being prepared.                                       |
| `written`    | Letter has been handwritten but not yet mailed.                |
| `complete`   | Letter has been mailed.                                        |
| `problem`    | A technical issue occurred — Handwrite support resolves these. |
| `cancelled`  | Order was cancelled (rare).                                    |

## Response

| Field         | Type   | Notes                                                            |
|---------------|--------|------------------------------------------------------------------|
| `_id`         | string | Order ID.                                                        |
| `message`     | string | The letter body as submitted.                                    |
| `status`      | string | One of the status values above.                                  |
| `handwriting` | string | Handwriting style ID used.                                       |
| `card`        | string | Stationery ID used.                                              |
| `createdAt`   | string | ISO 8601 timestamp.                                              |
| `environment` | string | `live` or `test`, per the API key used to create the order.      |
| `to`          | object | Recipient address.                                               |
| `from`        | object | Return address (if provided).                                    |
| `proofs`      | array  | Proof images: `job_type` (`card` or `envelope`) + `image_url`.   |

```jsonc
{
  "_id": "5f44086e69217700172ac110",
  "message": "Hey there, hope all is well!",
  "status": "complete",
  "handwriting": "5dc30652bc08d20016f1ec33",
  "card": "5f33fde848cc140017f0364a",
  "createdAt": "2020-08-24T18:35:26.686Z",
  "environment": "live",
  "to": {
    "firstName": "Jamie",
    "lastName": "Stockton",
    "company": "Stockton Lumber",
    "street1": "8284 Random Road",
    "city": "Sarasota",
    "state": "FL",
    "zip": "34240"
  },
  "from": {
    "firstName": "Terrance",
    "lastName": "McGhee",
    "street1": "293 Hungerford Drive",
    "street2": "",
    "city": "Rockville",
    "state": "MD",
    "zip": "20850"
  },
  "proofs": [
    {
      "job_type": "card",
      "image_url": "https://s3.us-east-2.amazonaws.com/any-random-image.jpg"
    },
    {
      "job_type": "envelope",
      "image_url": "https://s3.us-east-2.amazonaws.com/another-random-image.jpg"
    }
  ]
}
```

## See Also

* [Send a Letter](./send-letter.md) — where order IDs come from.
