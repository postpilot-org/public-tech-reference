<!-- markdownlint-disable no-duplicate-heading -->
# Customer Schema

Each line in the **customer** JSONL file is a single customer object.

**Example customer JSON object**

```jsonc
{
    "id": "cust_1001",
    "full_name": "Jane Doe",
    "company": "...",
    "email": "jane.doe@example.com", "line1": "123 Main St",
    "line2": "Apt 4B",
    "city": "Irvine",
    "state": "CA",
    "country_code": "US",
    "postal_code": "92618-1234",
    "created_at": "2024-11-15T09:12:00Z",
    "updated_at": "2025-03-27T10:15:00Z",
    "metadata": {
        "tags": [...]
    }
}
```

**Customer fields**

| Field | Type | Required | Notes                                                                                       |
|---|---|---|---------------------------------------------------------------------------------------------|
| `id` | string | ✅ Required | Your unique, stable customer ID, e.g. a numeric account ID sent as a string. Must not contain PII: if it's an email address or other personal data, hash it (any method) |
| `full_name` | string | ✅ Required | First and last name, 4+ characters: plain A-Z letters, spaces, apostrophes, hyphens, periods. Accents and non-Latin characters aren't supported unless `company` is set |
| `company` | string | ⬜ Optional | Company name if present                                                                     |
| `email` | string | ✅ Required | Primary email address of the customer, unhashed                                             |
| `line1` | string | ✅ Required | Primary address line1 of the customer                                                       |
| `line2` | string | ⬜ Optional | Primary address line2 of the customer                                                       |
| `city` | string | ✅ Required | Primary address city of the customer                                                        |
| `state` | string | ✅ Required | Primary address state of the customer. 2-letter code for US addresses, e.g. `CA`            |
| `postal_code` | string | ✅ Required | Primary address postal_code of the customer. US: `92618` or `92618-1234`                    |
| `country_code` | string | ✅ Required | ISO 3166-1 alpha-2, uppercase (e.g. `US`), Primary address country_code of the customer    |
| `created_at` | string | ✅ Required | ISO 8601 — Customer creation date                                                           |
| `updated_at` | string | ✅ Required | ISO 8601 — Customer update date. Any address, email update should trigger this field change |
| `metadata` | object | ⬜ Optional |                                                                                             |
| `metadata.tags` | array\<string\> | ⬜ Optional | Custom tags for filters                                                                     |


**Customer JSONL file example**

```jsonl
{"id":"cust_1001","full_name":"Jane Doe","email":"jane.doe@example.com","line1":"123 Main St","line2":"Apt 4B","city":"Irvine","state":"CA","country_code":"US","postal_code":"92618-1234","created_at":"2024-11-15T09:12:00Z","updated_at":"2025-03-27T10:15:00Z","metadata":{"tags":["PREMIUM"]}}
{"id":"cust_1002","full_name":"John Smith","email":"john.smith@example.com","line1":"456 Oak Ave","line2":null,"city":"Austin","state":"TX","country_code":"US","postal_code":"73301","created_at":"2024-12-01T11:30:00Z","updated_at":"2025-03-27T11:00:00Z"}
```