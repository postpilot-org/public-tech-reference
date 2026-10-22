#! /usr/bin/env python3
"""
PostPilot data feed validator.

Checks customers*.jsonl and orders*.jsonl files on your machine before you upload them, using the same rules
PostPilot's ingestion pipeline applies, plus a few data-quality checks for problems we see often.

Usage:
    python3 validate-feed.py customers_20260101.jsonl orders_20260101.jsonl
    python3 validate-feed.py orders/*.jsonl --examples 10

Privacy:
    * Runs locally. Uses only the Python standard library and makes no network calls.
    * Prints line numbers, field names and counts. It never prints a field value, so the report contains no
      customer data and can be shared with PostPilot as-is.
    * Your file contains customer PII. Run this yourself; don't upload the file to an online tool or AI assistant.

Exit codes: 0 = no errors, 1 = errors found, 2 = could not run.

Requires Python 3.8+.
"""

import argparse
import datetime
import json
import math
import os
import re
import sys
from collections import Counter, OrderedDict

MAX_FILE_BYTES = 1024 ** 3
MAX_BAD_LINES = 100  # more unreadable lines than this and the whole file is rejected

EMAIL_RE = re.compile(r"^[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}$")
COUNTRY_RE = re.compile(r"^[A-Z]{2}$")
CURRENCY_RE = re.compile(r"^[A-Z]{3}$")
TIMESTAMP_RE = re.compile(
    r"^(\d{4})-(\d{1,2})-(\d{1,2})"
    r"(?:[ T](\d{1,2}):(\d{1,2})(?::(\d{1,2})(?:\.\d{1,6})?)?)?"
    r"(\s*(?:Z|UTC|[+-]\d{1,2}(?::?\d{2})?))?$",
    re.ASCII,
)
OLDEST_PLAUSIBLE_YEAR = 1990
# Mailing-address rules applied after loading (they drop rows the first pass accepted). The name check is ASCII on
# purpose: the pipeline's \w only matches A-Z, 0-9 and _, so accented and non-Latin names fail it today. Its \s is
# ASCII too, so a non-breaking space between names fails.
GATE_NAME_RE = re.compile(r"(\w+\.*[\t\n\f\r ]+\w+)|(^Redacted$)", re.ASCII)
UNICODE_NAME_RE = re.compile(r"\w+\.*[\t\n\f\r ]+\w+")
US_ZIP_RE = re.compile(r"^[0-9]{5}(-[0-9]{4})?$")
UK_POSTCODE_RE = re.compile(r"^[A-Z0-9]{2,4}[\t\n\f\r ]?[A-Z0-9]{3}$", re.ASCII)
# Plain decimal only: float() alone would accept "1_000", "inf" and non-ASCII digits.
DECIMAL_RE = re.compile(r"[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?", re.ASCII)
INTEGER_RE = re.compile(r"-?\d+", re.ASCII)

ADDRESS_FIELDS = OrderedDict([
    ("id", "string"), ("full_name", "string"), ("company", "string"), ("email", "string"),
    ("line1", "string"), ("line2", "string"), ("city", "string"), ("state", "string"),
    ("postal_code", "string"), ("country_code", "string"),
])
METADATA_FIELDS = OrderedDict([("tags", ("array", "string"))])

CUSTOMER_SCHEMA = OrderedDict([
    ("id", "string"), ("full_name", "string"), ("company", "string"), ("email", "string"),
    ("line1", "string"), ("line2", "string"), ("city", "string"), ("state", "string"),
    ("country_code", "string"), ("postal_code", "string"), ("created_at", "string"), ("updated_at", "string"),
    ("metadata", ("struct", METADATA_FIELDS)),
])
LINE_ITEM_FIELDS = OrderedDict([("id", "string"), ("name", "string"), ("price", "float"), ("quantity", "int")])
ORDER_SCHEMA = OrderedDict([
    ("id", "string"), ("customer_id", "string"), ("total_price", "float"), ("currency", "string"),
    ("coupon_codes", ("array", "string")),
    ("shipping_address", ("struct", ADDRESS_FIELDS)),
    ("billing_address", ("struct", ADDRESS_FIELDS)),
    ("metadata", ("struct", METADATA_FIELDS)),
    ("line_items", ("array", ("struct", LINE_ITEM_FIELDS))),
    ("created_at", "string"), ("updated_at", "string"),
])
# In the documentation but not read by the pipeline.
ORDER_DOC_ONLY_FIELDS = {"email"}


class Report:
    """Collects issues by severity. Stores line numbers only, never values."""

    def __init__(self, max_examples):
        self.max_examples = max_examples
        self.issues = OrderedDict()  # (severity, message) -> [count, [line numbers]]
        self.notes = []

    def add(self, severity, message, line_no=None):
        entry = self.issues.setdefault((severity, message), [0, []])
        entry[0] += 1
        if line_no is not None and len(entry[1]) < self.max_examples:
            entry[1].append(line_no)

    def count(self, severity):
        return sum(c for (sev, _), (c, _) in self.issues.items() if sev == severity)

    def print(self):
        for severity, title in (("fatal", "FILE REJECTED"), ("must_fix", "MUST FIX BEFORE UPLOADING"),
                                ("bad_line", "UNREADABLE LINES"),
                                ("error", "RECORDS THAT WILL BE SKIPPED"), ("warning", "WARNINGS")):
            rows = [(msg, c, lines) for (sev, msg), (c, lines) in self.issues.items() if sev == severity]
            if not rows:
                continue
            print("\n  " + title)
            for msg, c, lines in sorted(rows, key=lambda r: -r[1]):
                where = ""
                if lines:
                    where = "  (line " + ", ".join(str(n) for n in lines) + (", ..." if c > len(lines) else "") + ")"
                print("    - {:>9,}  {}{}".format(c, msg, where))
        if self.notes:
            print("\n  NOTES")
            for note in self.notes:
                print("    - " + note)


def describe_json_error(err, text):
    msg = err.msg
    # Python's wording for comma mistakes varies by version, so read the text around the error instead.
    before = text[:err.pos].rstrip()
    after = text[err.pos:].lstrip()
    if before.endswith(",") and after.startswith(","):
        return "invalid JSON: two commas in a row"
    closer = after.lstrip(",").lstrip()[:1]
    if msg.startswith("Illegal trailing comma") or (before.endswith(",") and closer in ("}", "]")):
        return "invalid JSON: trailing comma before " + (closer or "}")
    if msg.startswith("Invalid \\escape") or msg.startswith("Invalid \\u"):
        return "invalid JSON: unescaped backslash inside a value (write \\ as \\\\)"
    if msg.startswith("Unterminated string"):
        return "invalid JSON: value cut off at end of line, usually a raw line break inside a value (write it as \\n)"
    if msg.startswith("Invalid control character"):
        return "invalid JSON: raw tab or control character inside a value (write tab as \\t)"
    if msg.startswith("Expecting ',' delimiter") or msg.startswith("Expecting ':' delimiter"):
        if 0 < err.pos <= len(text) and text[err.pos - 1] == '"':
            return 'invalid JSON: unescaped double quote inside a value (write " as \\")'
    if msg.startswith("Extra data"):
        return "invalid JSON: more than one JSON object on a line, or text after the object"
    if msg.startswith("Expecting value") and err.pos == 0:
        return "invalid JSON: line does not start a JSON object, often the second half of a record split by a raw line break"
    return "invalid JSON: " + msg


def reject_constant(name):
    raise ValueError("{} is not valid JSON".format(name))


def type_name(value):
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    return "object"


def check_types(record, schema, path, report, line_no):
    """Mirrors how the pipeline loads each field. Returns False if the line can't be loaded at all."""
    loadable = True
    for field, ftype in schema.items():
        if field not in record or record[field] is None:
            continue
        value = record[field]
        label = path + field
        if isinstance(ftype, tuple) and ftype[0] == "struct":
            if not isinstance(value, dict):
                report.add("bad_line", "`{}` must be an object, got {}".format(label, type_name(value)), line_no)
                loadable = False
            elif not check_types(value, ftype[1], label + ".", report, line_no):
                loadable = False
        elif isinstance(ftype, tuple) and ftype[0] == "array":
            if not isinstance(value, list):
                report.add("bad_line", "`{}` must be an array, got {}".format(label, type_name(value)), line_no)
                loadable = False
                continue
            inner = ftype[1]
            for item in value:
                if isinstance(inner, tuple):
                    if not isinstance(item, dict):
                        report.add("bad_line", "`{}[]` items must be objects, got {}".format(label, type_name(item)), line_no)
                        loadable = False
                    elif not check_types(item, inner[1], label + "[].", report, line_no):
                        loadable = False
                elif item is not None and not isinstance(item, str):
                    report.add("warning", "`{}[]` items should be strings, got {}".format(label, type_name(item)), line_no)
        elif ftype == "string":
            if isinstance(value, (dict, list)):
                report.add("bad_line", "`{}` must be a string, got {}".format(label, type_name(value)), line_no)
                loadable = False
            elif not isinstance(value, str):
                report.add("warning", "`{}` should be a string, got {} (wrap the value in quotes)".format(label, type_name(value)), line_no)
        elif ftype == "float":
            if isinstance(value, bool) or isinstance(value, (dict, list)):
                report.add("bad_line", "`{}` must be a number, got {}".format(label, type_name(value)), line_no)
                loadable = False
            elif isinstance(value, str):
                if parse_number(value) is None:
                    report.add("bad_line", "`{}` must be a number, got non-numeric text".format(label), line_no)
                    loadable = False
                else:
                    report.add("warning", "`{}` sent as text, send it as a JSON number".format(label), line_no)
        elif ftype == "int":
            if isinstance(value, bool) or isinstance(value, (dict, list)):
                report.add("bad_line", "`{}` must be a whole number, got {}".format(label, type_name(value)), line_no)
                loadable = False
            elif isinstance(value, float) and not value.is_integer():
                report.add("bad_line", "`{}` must be a whole number, got a decimal".format(label), line_no)
                loadable = False
            elif isinstance(value, str):
                if not INTEGER_RE.fullmatch(value.strip()):
                    report.add("bad_line", "`{}` must be a whole number, got non-numeric text".format(label), line_no)
                    loadable = False
                else:
                    report.add("warning", "`{}` sent as text, send it as a JSON number".format(label), line_no)
    return loadable


def parse_number(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        if not DECIMAL_RE.fullmatch(value.strip()):
            return None
        try:
            number = float(value.strip())
        except ValueError:
            return None
        return number if math.isfinite(number) else None
    return None


def parse_timestamp(value):
    """Returns a naive UTC-ish datetime if the pipeline would accept the value, else None."""
    if not isinstance(value, str):
        return None
    m = TIMESTAMP_RE.match(value.strip())
    if not m:
        return None
    year, month, day, hour, minute, second, _tz = m.groups()
    try:
        return datetime.datetime(int(year), int(month), int(day), int(hour or 0), int(minute or 0), int(second or 0))
    except ValueError:
        return None


def has_timezone(value):
    m = TIMESTAMP_RE.match(value.strip())
    return bool(m and m.group(7))


def decimals(value):
    text = value if isinstance(value, str) else repr(value)
    if "e" in text.lower() or "." not in text:
        return 0
    return len(text.split(".")[1].rstrip("0"))


def valid_full_name(value):
    # Letters, spaces, apostrophes, hyphens and periods only, at least 4 characters.
    name = value.strip()
    return len(name) >= 4 and all(ch.isalpha() or ch.isspace() or ch in "'-." for ch in name)


def is_blank(value):
    return isinstance(value, str) and value.strip() == ""


def as_id(value):
    if value is None or isinstance(value, (dict, list, bool)):
        return None
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return str(value)


def text(record, field):
    value = record.get(field)
    return "" if value is None else str(value)


def check_present(record, field, label, report, line_no):
    if record.get(field) is not None:
        return True
    report.add("error", "`{}` is missing or null".format(label), line_no)
    return False


def check_required_string(record, field, label, report, line_no):
    if not check_present(record, field, label, report, line_no):
        return False
    if is_blank(record.get(field)):
        report.add("warning", "`{}` is blank (accepted, but unusable)".format(label), line_no)
    return True


def check_email(value, label, report, line_no):
    if value is None:
        report.add("error", "`{}` is missing or null".format(label), line_no)
        return False
    if not isinstance(value, str) or not EMAIL_RE.match(value.lower()):
        report.add("error", "`{}` is not a valid email address".format(label), line_no)
        return False
    return True


def check_country(value, label, report, line_no):
    if value is None:
        report.add("error", "`{}` is missing or null".format(label), line_no)
        return False
    if not isinstance(value, str) or not COUNTRY_RE.match(value):
        report.add("error", "`{}` must be a 2-letter uppercase ISO 3166 code like US".format(label), line_no)
        return False
    return True


def name_issues(address, prefix):
    if text(address, "company").strip():
        return
    name = text(address, "full_name").replace("\0", "")
    if GATE_NAME_RE.search(name):
        return
    if UNICODE_NAME_RE.search(name):
        yield "full_name", "must use plain A-Z letters (accents and non-Latin characters aren't supported), or set `{}company`".format(prefix)
    else:
        yield "full_name", "needs a first and last name, or set `{}company`".format(prefix)


def us_issues(address):
    for field in ("city", "state"):
        if address.get(field) is not None and not text(address, field).strip():
            yield field, "is blank, required for US addresses"
    if len(text(address, "state")) > 2:
        yield "state", "must be a 2-letter code like CA for US addresses"
    if re.match(r"^-+$", text(address, "line1")):
        yield "line1", "is only dashes"
    if address.get("postal_code") is None:
        return
    zip_code = text(address, "postal_code")
    if not US_ZIP_RE.match(zip_code):
        yield "postal_code", "must be a 5-digit ZIP like 92618 or 92618-1234 for US addresses"
    elif zip_code.startswith("00000"):
        yield "postal_code", "is 00000"


def uk_issues(address):
    if address.get("postal_code") is not None and not UK_POSTCODE_RE.match(text(address, "postal_code").upper()):
        yield "postal_code", "is not a valid UK postcode like SW1A 1AA"


def mailing_address_issues(address, prefix, check_name):
    country = text(address, "country_code").upper()
    street_limit = 64 if country == "US" else 200
    if check_name:
        yield from name_issues(address, prefix)
    if address.get("line1") is not None and not text(address, "line1").strip():
        yield "line1", "is blank"
    limits = (("full_name", 40), ("company", 40), ("line1", street_limit), ("line2", street_limit),
              ("city", 200), ("state", 200))
    for field, limit in limits:
        if len(text(address, field).replace("\0", "")) > limit:
            yield field, "is longer than {} characters".format(limit)
    if country == "US":
        yield from us_issues(address)
    if country in ("UK", "GB"):
        yield from uk_issues(address)


def check_mailing_address(address, prefix, report, line_no, check_name=True):
    ok = True
    for field, problem in mailing_address_issues(address, prefix, check_name):
        report.add("error", "`{}{}` {}".format(prefix, field, problem), line_no)
        ok = False
    return ok


def check_dates(record, report, line_no, stats, now):
    ok = True
    parsed = {}
    for field in ("created_at", "updated_at"):
        value = record.get(field)
        if value is None:
            report.add("error", "`{}` is missing or null".format(field), line_no)
            ok = False
            continue
        ts = parse_timestamp(value)
        if ts is None:
            report.add("error", "`{}` is not an ISO 8601 date/time like 2025-03-27T10:15:00Z".format(field), line_no)
            ok = False
            continue
        parsed[field] = ts
        if not has_timezone(value):
            report.add("warning", "`{}` has no time zone, add Z or an offset like -05:00".format(field), line_no)
        if ts.year < OLDEST_PLAUSIBLE_YEAR:
            report.add("warning", "`{}` is before {}, check the field is mapped to the right date".format(field, OLDEST_PLAUSIBLE_YEAR), line_no)
        if ts > now + datetime.timedelta(days=1):
            report.add("warning", "`{}` is in the future".format(field), line_no)
    if "created_at" in parsed and "updated_at" in parsed:
        stats["dated"] += 1
        if parsed["updated_at"] < parsed["created_at"]:
            report.add("warning", "`updated_at` is earlier than `created_at`", line_no)
        if parsed["updated_at"] == parsed["created_at"]:
            stats["updated_equals_created"] += 1
        stats["created_dates"][parsed["created_at"].date()] += 1
    return ok


def validate_customer(record, report, line_no, stats, now):
    ok = check_required_string(record, "id", "id", report, line_no)
    for field in ("line1", "city", "state", "postal_code"):
        ok = check_present(record, field, field, report, line_no) and ok
    name = record.get("full_name")
    name_ok = False
    if name is None:
        report.add("error", "`full_name` is missing or null", line_no)
    elif not isinstance(name, str) or not valid_full_name(name):
        report.add("error", "`full_name` must be 4+ characters of letters, spaces, apostrophes, hyphens or periods", line_no)
    else:
        name_ok = True
    ok = name_ok and ok
    ok = check_email(record.get("email"), "email", report, line_no) and ok
    ok = check_country(record.get("country_code"), "country_code", report, line_no) and ok
    ok = check_mailing_address(record, "", report, line_no, check_name=name_ok) and ok
    ok = check_dates(record, report, line_no, stats, now) and ok
    return ok


def validate_address(address, label, report, line_no, mailing):
    # Only the shipping address goes through the mailing-address rules, billing just needs the first pass.
    if address is None:
        report.add("error", "`{}` is missing or null".format(label), line_no)
        return False
    ok = True
    for field in ("line1", "city", "state", "postal_code"):
        ok = check_present(address, field, label + "." + field, report, line_no) and ok
    ok = check_country(address.get("country_code"), label + ".country_code", report, line_no) and ok
    ok = check_email(address.get("email"), label + ".email", report, line_no) and ok
    for field in ("id",) if mailing else ("id", "full_name"):
        if address.get(field) is None:
            report.add("warning", "`{}.{}` is missing (required by the documentation)".format(label, field), line_no)
    if mailing:
        ok = check_mailing_address(address, label + ".", report, line_no) and ok
    return ok


def validate_order(record, report, line_no, stats, now):
    ok = True
    for field in ("id", "customer_id", "currency"):
        ok = check_required_string(record, field, field, report, line_no) and ok
    currency = record.get("currency")
    if isinstance(currency, str) and currency.strip() and not CURRENCY_RE.match(currency):
        report.add("warning", "`currency` should be a 3-letter uppercase ISO code like USD", line_no)

    total = parse_number(record.get("total_price"))
    if record.get("total_price") is None:
        report.add("error", "`total_price` is missing or null", line_no)
        ok = False
    elif total is not None and total <= 0:
        report.add("error", "`total_price` must be greater than 0 (leave refunds, returns and $0 orders out)", line_no)
        ok = False
    elif total is not None and decimals(record["total_price"]) > 2:
        report.add("warning", "`total_price` has more than 2 decimal places", line_no)

    ok = validate_address(record.get("shipping_address"), "shipping_address", report, line_no, mailing=True) and ok
    ok = validate_address(record.get("billing_address"), "billing_address", report, line_no, mailing=False) and ok

    items = record.get("line_items")
    if not items:
        report.add("error", "`line_items` is missing or empty", line_no)
        ok = False
    else:
        amounts = []
        for item in items:
            for field in ("id", "name", "price", "quantity"):
                if item.get(field) is None:
                    report.add("warning", "`line_items[].{}` is missing (required by the documentation)".format(field), line_no)
            price, qty = parse_number(item.get("price")), parse_number(item.get("quantity"))
            if price is not None and decimals(item["price"]) > 2:
                report.add("warning", "`line_items[].price` has more than 2 decimal places", line_no)
            if qty is not None and qty <= 0:
                report.add("warning", "`line_items[].quantity` is 0 or negative", line_no)
            if price is not None and qty is not None:
                amounts.append(round(price * qty, 2))
        if total is not None and len(amounts) > 1:
            item_sum = round(sum(amounts), 2)
            if abs(item_sum - total) > 0.01 and any(abs(a - total) <= 0.01 for a in amounts):
                report.add("warning", "`total_price` equals one line item, not the whole order", line_no)

    if record.get("email") is None:
        report.add("warning", "`email` is missing (required by the documentation)", line_no)

    ok = check_dates(record, report, line_no, stats, now) and ok
    return ok


def new_stats():
    return {"dated": 0, "updated_equals_created": 0, "created_dates": Counter()}


def validate_file(path, kind, max_examples, ids_out, refs_out):
    report = Report(max_examples)
    name = os.path.basename(path)
    print("\n" + "=" * 78)
    print("{}  ({})".format(name, kind))
    print("=" * 78)

    if not name.endswith(".jsonl"):
        report.add("fatal", "file name must end in .jsonl (.json, .ndjson and .csv files are not processed)")
    if not name.startswith(kind):
        report.add("fatal", "file name must start with `{}` and go in the {}/ folder".format(kind, kind))
    size = os.path.getsize(path)
    if size == 0:
        report.add("fatal", "file is empty")
    if size > MAX_FILE_BYTES:
        report.add("fatal", "file is larger than 1 GB, split it into smaller files")

    schema = CUSTOMER_SCHEMA if kind == "customers" else ORDER_SCHEMA
    validate = validate_customer if kind == "customers" else validate_order
    stats = new_stats()
    now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    seen_ids = set()
    unknown_fields = Counter()
    total = loaded = valid = blank = bad_lines = 0

    with open(path, "rb") as fh:
        for line_no, raw in enumerate(fh, start=1):
            if line_no == 1:
                if raw.startswith(b"\xef\xbb\xbf"):
                    report.add("bad_line", "file starts with a byte-order mark (BOM), save as UTF-8 without BOM", 1)
                    raw = raw[3:]
                head = raw.lstrip()
                if head.startswith(b"["):
                    report.add("fatal", "file is a JSON array; JSONL needs one object per line, no surrounding [ ]")
                    break
                if head and not head.startswith(b"{") and b"," in head:
                    report.add("fatal", "file looks like CSV, it must be JSONL (one JSON object per line)")
                    break
            try:
                text = raw.decode("utf-8").rstrip("\r\n")
            except UnicodeDecodeError:
                report.add("bad_line", "line is not valid UTF-8", line_no)
                bad_lines += 1
                total += 1
                continue
            if not text.strip():
                blank += 1
                continue
            total += 1
            try:
                record = json.loads(text, parse_constant=reject_constant)
            except json.JSONDecodeError as err:
                report.add("bad_line", describe_json_error(err, text), line_no)
                bad_lines += 1
                continue
            except ValueError:
                report.add("bad_line", "invalid JSON: NaN or Infinity is not allowed, use null", line_no)
                bad_lines += 1
                continue
            if not isinstance(record, dict):
                report.add("bad_line", "line is valid JSON but not an object { ... }", line_no)
                bad_lines += 1
                continue
            if not check_types(record, schema, "", report, line_no):
                bad_lines += 1
                continue
            loaded += 1
            for field in record:
                if field not in schema and not (kind == "orders" and field in ORDER_DOC_ONLY_FIELDS):
                    unknown_fields[field] += 1

            record_id = as_id(record.get("id"))
            if record_id is not None:
                if record_id in seen_ids:
                    report.add("warning", "`id` repeats an earlier line, only the version with the latest `updated_at` is kept", line_no)
                seen_ids.add(record_id)
                if "@" in record_id:
                    report.add("must_fix", "`id` contains an email address. IDs must not contain PII: hash it (any method, same value in both files)", line_no)
            if kind == "orders":
                ref = as_id(record.get("customer_id"))
                if ref is not None:
                    refs_out.append(ref)
                    if "@" in ref:
                        report.add("must_fix", "`customer_id` contains an email address. IDs must not contain PII: send the same hashed value as the customer `id`", line_no)

            if validate(record, report, line_no, stats, now):
                valid += 1

    ids_out.update(seen_ids)

    if bad_lines > MAX_BAD_LINES:
        report.add("fatal", "{:,} unreadable lines, more than the limit of {}, so the whole file is rejected".format(bad_lines, MAX_BAD_LINES))
    if blank:
        report.notes.append("{:,} blank lines skipped".format(blank))
    for field, count in unknown_fields.most_common(10):
        report.notes.append("`{}` is not a PostPilot field and is ignored ({:,} line(s)), check the spelling if you meant a documented field".format(field, count))
    if stats["dated"] >= 10 and stats["updated_equals_created"] == stats["dated"]:
        report.notes.append("`updated_at` equals `created_at` on every record, it should change whenever the record changes")
    dates = stats["created_dates"]
    if dates:
        first, last = min(dates), max(dates)
        report.notes.append("`created_at` runs {} to {}".format(first, last))
        if kind == "orders" and (last - first).days <= 400:
            missing = [first + datetime.timedelta(days=d) for d in range((last - first).days + 1)
                       if first + datetime.timedelta(days=d) not in dates]
            if missing:
                shown = ", ".join(str(d) for d in missing[:10]) + (", ..." if len(missing) > 10 else "")
                report.notes.append("{} day(s) in that range have no orders: {}".format(len(missing), shown))

    report.print()

    fatal = report.count("fatal") > 0
    must_fix = report.count("must_fix") > 0
    print("\n  Lines: {:,}   Loaded: {:,}   Passed validation: {:,}   Unreadable: {:,}".format(total, loaded, valid, bad_lines))
    if fatal:
        status = "FAIL, PostPilot will not process this file"
    elif must_fix:
        status = "FIX BEFORE UPLOADING, IDs contain PII"
    elif bad_lines or valid < loaded:
        status = "PASS WITH ERRORS, {:,} line(s) will be dropped".format(bad_lines + (loaded - valid))
    else:
        status = "PASS"
    print("  Result: " + status)
    return not fatal and not must_fix and bad_lines == 0 and valid == loaded


def cross_check(customer_ids, order_refs):
    print("\n" + "=" * 78)
    print("customers <-> orders")
    print("=" * 78)
    if not customer_ids or not order_refs:
        print("  Skipped, need at least one readable customers file and one orders file.")
        return True
    matched = sum(1 for ref in order_refs if ref in customer_ids)
    pct = 100.0 * matched / len(order_refs)
    print("  {:,} of {:,} orders ({:.1f}%) have a `customer_id` that matches a customer `id`.".format(matched, len(order_refs), pct))
    if matched < len(order_refs):
        normalized = {i.strip().lower() for i in customer_ids}
        fuzzy = sum(1 for ref in order_refs if ref not in customer_ids and ref.strip().lower() in normalized)
        if fuzzy:
            print("  {:,} more would match if both sides were trimmed and lowercased the same way.".format(fuzzy))
        print("  `customer_id` on orders must be the exact `id` you send in the customers file.")
        print("  If these are incremental files, unmatched orders may belong to customers sent earlier.")
    if matched == 0:
        print("  Result: FAIL, no orders match any customer, check that both files use the same ID")
        return False
    print("  Result: PASS" if matched == len(order_refs) else "  Result: CHECK")
    return True


def main():
    parser = argparse.ArgumentParser(description="Validate PostPilot customers/orders JSONL files locally before upload.")
    parser.add_argument("files", nargs="+", help="customers*.jsonl and/or orders*.jsonl files")
    parser.add_argument("--examples", type=int, default=5, help="line numbers to show per issue (default 5)")
    args = parser.parse_args()

    customer_ids, order_refs = set(), []
    all_ok = True
    has_customers = has_orders = False
    for path in args.files:
        if not os.path.isfile(path):
            print("Not a file: {}".format(path), file=sys.stderr)
            return 2
        name = os.path.basename(path).lower()
        if name.startswith("customer"):
            kind, has_customers = "customers", True
        elif name.startswith("order"):
            kind, has_orders = "orders", True
        else:
            print("Can't tell if {} is a customers or orders file. Name it customers_YYYYMMDD.jsonl or "
                  "orders_YYYYMMDD.jsonl.".format(path), file=sys.stderr)
            return 2
        all_ok = validate_file(path, kind, args.examples, customer_ids if kind == "customers" else set(),
                               order_refs) and all_ok

    if has_customers and has_orders:
        all_ok = cross_check(customer_ids, order_refs) and all_ok

    print("\nNo field values were printed. This report is safe to share with PostPilot.")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
