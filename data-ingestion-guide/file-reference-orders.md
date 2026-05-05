<!-- markdownlint-disable no-duplicate-heading -->
# Order Schema

Each line in the **order** JSONL file is a single order object.

Example order JSON object

```jsonc
{
    "id": "ord_9001",
    "customer_id": "cust_1001",
    "total_price": 129.99,
    "currency": "USD",
    "coupon_codes": ["WELCOME10"],
    "shipping_address": {
        "id": "cust_1001",
        "full_name": "Jane Doe",
        "company": "...",
        "email": "jane.doe@example.com",
        "line1": "123 Main St",
        "line2": "Apt 4B",
        "city": "Irvine",
        "state": "CA",
        "postal_code": "92618-1234"
        "country_code": "US"
    },
    "billing_address": {
        "id": "cust_1001",
        "full_name": "Jane Doe",
        "company": "...",
        "email": "jane.doe@example.com",
        "line1": "123 Main St",
        "line2": "Apt 4B",
        "city": "Irvine",
        "state": "CA",
        "postal_code": "92618-1234",
        "country_code": "US"
    },
    "metadata": {
        "tags": [...]
    },
    "line_items": [
        {
            "id": "li_1",
            "name": "T-Shirt",
            "price": 29.99,
        "quantity": 2
        },
        {
            "id": "li_2",
            "name": "Jeans",
            "price": 70.01,
            "quantity": 1
        }
    ],
    "created_at": "2025-03-27T09:55:00Z",
    "updated_at": "2025-03-27T10:10:00Z"
}
```

**Order fields**

Top-level:

| Field | Type              | Required | Notes                                                                                |
|---|-------------------|---|--------------------------------------------------------------------------------------|
| `id` | string            | ✅ Required | Unique Order Id                                                                      |
| `customer_id` | string            | ✅ Required | Unique Customer Id                                                                   |
| `total_price` | number            | ✅ Required | Total order price                                                                    |
| `currency` | string            | ✅ Required | ISO currency code, e.g. `USD`                                                        |
| `email` | string            | ✅ Required | Email address                                                                        |
| `coupon_codes` | array\<string\>   | ⬜ Optional | Coupon codes if used                                                                 |
| `shipping_address` | JSON              | ✅ Required | Shipping address                                                                     |
| `billing_address` | JSON              | ✅ Required | Billing Address                                                                      |
| `line_items` | array\<LineItem\> | ✅ Required | Order line item list                                                                 |
| `created_at` | string            | ✅ Required | ISO 8601 Order creation date                                                                            |
| `updated_at` | string            | ✅ Required | ISO 8601 — must change whenever any attribute of the order or its line items changes |
| `metadata` | Map<String,Any>   | ⬜ Optional | Generic Field for storing tags or custom variables                                                           |

LineItem Type:

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | string | ✅ Required |Product Id |
| `name` | string | ✅ Required |Product Name |
| `price` | number | ✅ Required | Unit price with 2 decimal places |
| `quantity` | integer | ✅ Required |Number of items in the line item |

Address Type:

| Field | Type | Required | Notes                                                                                       |
|---|---|---|---------------------------------------------------------------------------------------------|
| `id` | string | ✅ Required | Your unique, stable customer ID                                                             |
| `full_name` | string | ✅ Required | Full name                                                                                   |
| `company` | string | ⬜ Optional | Company name if present                                                                     |
| `email` | string | ✅ Required | Primary email address of the customer                                                       |
| `line1` | string | ✅ Required | Primary address line1 of the customer                                                       |
| `line2` | string | ⬜ Optional | Primary address line2 of the customer                                                       |
| `city` | string | ✅ Required | Primary address city of the customer                                                        |
| `state` | string | ✅ Required | Primary address state of the customer                                                       |
| `postal_code` | string | ✅ Required | Primary address postal_code of the customer                                                 |
| `country_code` | string | ✅ Required | ISO 3166, Primary address country_code of the customer                                      |


** Order JSONL file example**

```jsonl
{"id":"ord_9001","customer_id":"cust_1001","total_price":129.99,"currency":"USD","email":"jane.doe@example.com","coupon_codes":["WELCOME10"],"shipping_address": {"id":"cust_1001","full_name":"JaneDoe","email":"jane.doe@example.com","line1":"123 Main St","line2":"Apt4B","city":"Irvine","state":"CA","postal_code":"92618-1234"},"billing_address":{"id":"cust_1001","full_name":"Jane Doe","email":"jane.doe@example.com","line1":"123 Main St","line2":"Apt 4B","city":"Irvine","state":"CA","postal_code":"92618-1234"},"browser_ip":"203.0.113.42","line_items":[{"id":"li_1","name":"T-Shirt","price":29.99,"quantity":2},{"id":"li_2","name":"Jeans","price":70.01,"quantity":1}],"created_at":"2025-03-27T09:55:00Z","updated_at":"2025-03-27T10:10:00Z"}
{"id":"ord_9002","customer_id":"cust_1002","total_price":59.98,"currency":"USD","email":"john.smith@example.com","coupon_codes":[],,"shipping_address": {"id":"cust_1001","full_name":"Jane Doe","email":"jane.doe@example.com","line1":"123 Main St","line2":"Apt 4B","city":"Irvine","state":"CA","postal_code":"92618-1234"},"billing_address": {"id":"cust_1001","full_name":"Jane Doe","email":"jane.doe@example.com","line1":"123 Main St","line2":"Apt 4B","city":"Irvine","state":"CA","postal_code":"92618-1234"},"browser_ip":"198.51.100.23","line_items":[{"id":"li_3","name":"Hat","price":29.99,"quantity":2}],"created_at":"2025-03-27T09:58:00Z","updated_at":"2025-03-27T09:58:00Z"}
```
