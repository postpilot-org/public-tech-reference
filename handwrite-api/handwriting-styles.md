<!-- markdownlint-disable no-duplicate-heading -->
# Handwriting Styles

List the handwriting styles available to your account. Each style's `_id` is used as the `handwriting` value when
[sending a letter](./send-letter.md).

## Endpoint

```http
GET https://api.handwrite.io/v1/handwriting
Authorization: {api_key}
Content-Type: application/json
```

## Response

Returns an array of handwriting objects:

| Field         | Type   | Notes                                                       |
|---------------|--------|-------------------------------------------------------------|
| `_id`         | string | The handwriting style ID — pass as `handwriting` on send.   |
| `name`        | string | Display name of the style.                                  |
| `preview_url` | string | Image URL previewing the handwriting style.                 |

```jsonc
[
  {
    "_id": "5db6f0724cc1751452c5ae8e",
    "name": "Jeremy",
    "preview_url": "http://res.cloudinary.com/handwrite/image/upload/v1572270190/cards/wkwtnagsty79e0tlbiad.jpg"
  }
]
```

## See Also

* [Stationery](./stationery.md) — the other ID you need before sending.
* [Send a Letter](./send-letter.md) — where the `_id` is used.
