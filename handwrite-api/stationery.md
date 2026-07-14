<!-- markdownlint-disable no-duplicate-heading -->
# Stationery

List the stationery/cards available to your account. Each card's `_id` is used as the `card` value when
[sending a letter](./send-letter.md).

## Endpoint

```http
GET https://api.handwrite.io/v1/stationery
Authorization: {api_key}
Content-Type: application/json
```

## Response

Returns an array of stationery objects:

| Field         | Type   | Notes                                             |
|---------------|--------|---------------------------------------------------|
| `_id`         | string | The stationery ID — pass as `card` on send.       |
| `name`        | string | Display name of the card.                         |
| `preview_url` | string | Image URL previewing the stationery.              |

```jsonc
[
  {
    "_id": "5db6f1854cc1751452c5ae93",
    "name": "Classic White",
    "preview_url": "http://res.cloudinary.com/handwrite/image/upload/v1572270464/cards/yflijfai9wm38czthluk.jpg"
  }
]
```

## See Also

* [Handwriting Styles](./handwriting-styles.md) — the other ID you need before sending.
* [Send a Letter](./send-letter.md) — where the `_id` is used.
