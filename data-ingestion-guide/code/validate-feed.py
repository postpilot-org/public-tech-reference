#! /usr/bin/env python3
"""
PostPilot data feed validator.

Checks customers*.jsonl and orders*.jsonl files on your machine before you upload them. Each record is checked
against the JSON Schemas in ../schemas (the same rules PostPilot's ingestion pipeline applies), then this script
adds the checks a schema can't express: file-level limits, duplicate IDs, customer_id matching and data-quality
warnings.

Usage:
    python3 -m pip install jsonschema
    python3 validate-feed.py customers_20260101.jsonl orders_20260101.jsonl
    python3 validate-feed.py orders/*.jsonl --examples 10

Privacy:
    * Runs locally and makes no network calls.
    * Prints line numbers, field names and counts. It never prints a field value, so the report contains no
      customer data and can be shared with PostPilot as-is.
    * Your file contains customer PII. Run this yourself; don't upload the file to an online tool or AI assistant.

Exit codes: 0 = no errors, 1 = errors found, 2 = could not run.

Requires Python 3.11+.
"""

import sys

def fail(message):
    print(message, file=sys.stderr)
    sys.exit(2)


if sys.version_info < (3, 11):
    fail("validate-feed.py needs Python 3.11 or newer.")

import argparse
import copy
import datetime
import json
import math
import re
from collections import Counter
from pathlib import Path

try:
    from jsonschema import Draft202012Validator
except ImportError:
    fail("validate-feed.py needs the jsonschema package: python3 -m pip install jsonschema")

MAX_FILE_BYTES = 1024 ** 3
MAX_BAD_LINES = 100  # more unreadable lines than this and the whole file is moved aside unprocessed
SCHEMA_DIR = Path(__file__).resolve().parent.parent / "schemas"

CURRENCY_RE = re.compile(r"^[A-Z]{3}$")
TIMESTAMP_RE = re.compile(
    r"^(\d{4})-(\d{1,2})-(\d{1,2})"
    r"(?:[ T](\d{1,2}):(\d{1,2})(?::(\d{1,2})(?:\.\d{1,6})?)?)?"
    r"(\s*(?:Z|UTC|[+-]\d{1,2}(?::?\d{2})?))?$",
    re.ASCII,
)
OLDEST_PLAUSIBLE_YEAR = 1990
# Plain decimal only: float() alone would accept "1_000", "inf" and non-ASCII digits.
DECIMAL_RE = re.compile(r"[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?", re.ASCII)
INTEGER_RE = re.compile(r"-?\d+", re.ASCII)
SECTIONS = (
    ("fatal", "FILE WON'T BE PROCESSED"),
    ("must_fix", "MUST FIX BEFORE UPLOADING"),
    ("bad_line", "UNREADABLE LINES"),
    ("error", "RECORDS THAT WILL BE SKIPPED"),
    ("warning", "WARNINGS"),
)


class Report:
    """Collects issues by severity. Stores line numbers only, never values."""

    def __init__(self, max_examples):
        self.max_examples = max_examples
        self.issues = {}  # (severity, message) -> [count, [line numbers]]
        self.notes = []

    def add(self, severity, message, line_no=None):
        entry = self.issues.setdefault((severity, message), [0, []])
        entry[0] += 1
        if line_no is not None and len(entry[1]) < self.max_examples:
            entry[1].append(line_no)

    def count(self, severity):
        return sum(c for (sev, _), (c, _) in self.issues.items() if sev == severity)

    def print(self):
        for severity, title in SECTIONS:
            rows = [(msg, c, lines) for (sev, msg), (c, lines) in self.issues.items() if sev == severity]
            if not rows:
                continue
            print(f"\n  {title}")
            for msg, c, lines in sorted(rows, key=lambda r: -r[1]):
                where = ""
                if lines:
                    more = ", ..." if c > len(lines) else ""
                    where = f"  (line {', '.join(map(str, lines))}{more})"
                print(f"    - {c:>9,}  {msg}{where}")
        if self.notes:
            print("\n  NOTES")
            for note in self.notes:
                print(f"    - {note}")


def describe_json_error(err, text):
    msg = err.msg
    # Python's wording for comma mistakes varies by version, so read the text around the error instead.
    before = text[:err.pos].rstrip()
    after = text[err.pos:].lstrip()
    if before.endswith(",") and after.startswith(","):
        return "invalid JSON: two commas in a row"
    closer = after.lstrip(",").lstrip()[:1]
    if msg.startswith("Illegal trailing comma") or (before.endswith(",") and closer in ("}", "]")):
        return f"invalid JSON: trailing comma before {closer or '}'}"
    if msg.startswith(("Invalid \\escape", "Invalid \\u")):
        return "invalid JSON: unescaped backslash inside a value (write \\ as \\\\)"
    if msg.startswith("Unterminated string"):
        return "invalid JSON: value cut off at end of line, usually a raw line break inside a value (write it as \\n)"
    if msg.startswith("Invalid control character"):
        return "invalid JSON: raw tab or control character inside a value (write tab as \\t)"
    if msg.startswith(("Expecting ',' delimiter", "Expecting ':' delimiter")):
        if 0 < err.pos <= len(text) and text[err.pos - 1] == '"':
            return 'invalid JSON: unescaped double quote inside a value (write " as \\")'
    if msg.startswith("Extra data"):
        return "invalid JSON: more than one JSON object on a line, or text after the object"
    if msg.startswith("Expecting value") and err.pos == 0:
        return "invalid JSON: line does not start a JSON object, often the second half of a record split by a raw line break"
    return f"invalid JSON: {msg}"


def reject_constant(name):
    raise ValueError(f"{name} is not valid JSON")


def type_name(value):
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string"
    return "array" if isinstance(value, list) else "object"


def field_path(parts):
    """['line_items', 0, 'price'] -> 'line_items[].price'. Indexes are dropped so issues group across items."""
    out = ""
    for part in parts:
        out += "[]" if isinstance(part, int) else (f".{part}" if out else part)
    return out


def a_type(name):
    return {"array": "an array", "object": "an object", "integer": "a whole number"}.get(name, f"a {name}")


def classify(err):
    """
    Turns one schema error into (severity, message) pairs.

    Built from the error's path, keyword and our schema's descriptions only. Never use err.message or
    err.instance in output: both contain the field value, which is customer data.
    """
    path = field_path(err.absolute_path)
    value = err.instance
    keyword = err.validator

    if keyword == "required":
        prefix = f"{path}." if path else ""
        return [("error", f"`{prefix}{field}` is missing or null")
                for field in err.validator_value if field not in value]

    if keyword == "type":
        expected = err.validator_value if isinstance(err.validator_value, list) else [err.validator_value]
        if value is None:
            return [("error", f"`{path}` is missing or null")]
        is_container = isinstance(value, (dict, list))
        wants_container = any(t in ("object", "array") for t in expected)
        if is_container or wants_container:
            # The pipeline loads into typed columns: a shape mismatch makes the whole line unloadable.
            return [("bad_line", f"`{path}` must be {a_type(expected[0])}, got {type_name(value)}")]
        return [("error", f"`{path}` must be {a_type(expected[0])}, got {type_name(value)}")]

    if keyword == "not" and path in ("id", "customer_id"):
        hint = "hash it (any method, same value in both files)" if path == "id" \
            else "send the same hashed value as the customer `id`"
        return [("must_fix", f"`{path}` contains an email address. IDs must not contain PII: {hint}")]

    in_rule = any(step in ("then", "else") for step in err.schema_path)
    description = err.schema.get("description", "").rstrip(".") if isinstance(err.schema, dict) else ""
    if in_rule and description:
        return [("error", f"`{path}` is not valid: {description}")]
    if keyword == "minLength":
        return [("error", f"`{path}` is shorter than {err.validator_value} characters")]
    if keyword == "maxLength":
        return [("error", f"`{path}` is longer than {err.validator_value} characters")]
    if keyword == "minItems":
        return [("error", f"`{path}` is empty")]
    if keyword == "pattern" and err.validator_value == "\\S":
        return [("error", f"`{path}` is blank")]
    if description:
        return [("error", f"`{path}` is not valid: {description}")]
    return [("error", f"`{path}` is not in the expected format")]


def parse_number(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str) and DECIMAL_RE.fullmatch(value.strip()):
        number = float(value.strip())
        return number if math.isfinite(number) else None
    return None


def number_issues(value, label, whole):
    """Numbers sent as text still load if the pipeline can cast them; anything else makes the line unloadable."""
    if value is None or isinstance(value, (dict, list)):
        return []  # missing values and shape mismatches are reported by the schema
    kind = "a whole number" if whole else "a number"
    if isinstance(value, bool):
        return [("bad_line", f"`{label}` must be {kind}, got boolean")]
    if isinstance(value, str):
        ok = INTEGER_RE.fullmatch(value.strip()) if whole else parse_number(value) is not None
        if not ok:
            return [("bad_line", f"`{label}` must be {kind}, got non-numeric text")]
        return [("warning", f"`{label}` sent as text, send it as a JSON number")]
    if whole and isinstance(value, float) and not value.is_integer():
        return [("bad_line", f"`{label}` must be a whole number, got a decimal")]
    return []


def decimals(value):
    text = value if isinstance(value, str) else repr(value)
    if "e" in text.lower() or "." not in text:
        return 0
    return len(text.split(".")[1].rstrip("0"))


def date_issues(record, stats, now):
    issues, parsed = [], {}
    for field in ("created_at", "updated_at"):
        value = record.get(field)
        match = TIMESTAMP_RE.match(value.strip()) if isinstance(value, str) else None
        if not match:
            continue  # the schema reports missing and badly formatted dates
        year, month, day, hour, minute, second, tz = match.groups()
        try:
            ts = datetime.datetime(int(year), int(month), int(day), int(hour or 0), int(minute or 0), int(second or 0))
        except ValueError:
            issues.append(("error", f"`{field}` is not a real date/time"))
            continue
        parsed[field] = ts
        if not tz:
            issues.append(("warning", f"`{field}` has no time zone, add Z or an offset like -05:00"))
        if ts.year < OLDEST_PLAUSIBLE_YEAR:
            issues.append(("warning", f"`{field}` is before {OLDEST_PLAUSIBLE_YEAR}, check the field is mapped to the right date"))
        if ts > now + datetime.timedelta(days=1):
            issues.append(("warning", f"`{field}` is in the future"))
    if len(parsed) == 2:
        stats["dated"] += 1
        if parsed["updated_at"] < parsed["created_at"]:
            issues.append(("warning", "`updated_at` is earlier than `created_at`"))
        if parsed["updated_at"] == parsed["created_at"]:
            stats["updated_equals_created"] += 1
        stats["created_dates"][parsed["created_at"].date()] += 1
    return issues


def quality_issues(record, kind):
    """Data-quality warnings. None of these skip a record."""
    issues = []
    for field in ("id", "customer_id") if kind == "orders" else ("id",):
        value = record.get(field)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            issues.append(("warning", f"`{field}` should be a string, got number (wrap the value in quotes)"))
        elif isinstance(value, str) and not value.strip():
            issues.append(("warning", f"`{field}` is blank (accepted, but unusable)"))
    if kind == "customers":
        return issues

    currency = record.get("currency")
    if isinstance(currency, str) and not currency.strip():
        issues.append(("warning", "`currency` is blank (accepted, but unusable)"))
    elif isinstance(currency, str) and not CURRENCY_RE.match(currency):
        issues.append(("warning", "`currency` should be a 3-letter uppercase ISO code like USD"))
    if record.get("email") is None:
        issues.append(("warning", "`email` is missing (required by the documentation)"))

    total = parse_number(record.get("total_price"))
    if total is not None and decimals(record["total_price"]) > 2:
        issues.append(("warning", "`total_price` has more than 2 decimal places"))
    for label, fields in (("shipping_address", ("id",)), ("billing_address", ("id", "full_name"))):
        address = record.get(label)
        if isinstance(address, dict):
            issues += [("warning", f"`{label}.{f}` is missing (required by the documentation)")
                       for f in fields if address.get(f) is None]

    amounts = []
    for item in record.get("line_items") or []:
        if not isinstance(item, dict):
            continue
        issues += [("warning", f"`line_items[].{f}` is missing (required by the documentation)")
                   for f in ("id", "name", "price", "quantity") if item.get(f) is None]
        price, qty = parse_number(item.get("price")), parse_number(item.get("quantity"))
        if price is not None and decimals(item["price"]) > 2:
            issues.append(("warning", "`line_items[].price` has more than 2 decimal places"))
        if qty is not None and qty <= 0:
            issues.append(("warning", "`line_items[].quantity` is 0 or negative"))
        if price is not None and qty is not None:
            amounts.append(round(price * qty, 2))
    if total is not None and len(amounts) > 1:
        if abs(round(sum(amounts), 2) - total) > 0.01 and any(abs(a - total) <= 0.01 for a in amounts):
            issues.append(("warning", "`total_price` equals one line item, not the whole order"))
    return issues


def is_number_for_string(err):
    if err.validator != "type" or type_name(err.instance) != "number":
        return False
    expected = err.validator_value if isinstance(err.validator_value, list) else [err.validator_value]
    return "string" in expected


def check_record(record, kind, validator, stats, now):
    """Returns this line's issues as a set of (severity, message)."""
    issues = set()
    errors = list(validator.iter_errors(record))
    numbers_as_text = [list(e.absolute_path) for e in errors if is_number_for_string(e)]
    if numbers_as_text:
        # The pipeline casts a number in a text field to text, then validates it. Do the same, so a number
        # in a field like postal_code still gets the ZIP check.
        as_text = copy.deepcopy(record)
        for parts in numbers_as_text:
            *parents, last = parts
            target = as_text
            for part in parents:
                target = target[part]
            target[last] = json.dumps(target[last])
            issues.add(("warning", f"`{field_path(parts)}` should be a string, got number (wrap the value in quotes)"))
        errors = list(validator.iter_errors(as_text))
    for err in errors:
        issues.update(classify(err))
    if kind == "orders":
        issues.update(number_issues(record.get("total_price"), "total_price", whole=False))
        for item in record.get("line_items") or []:
            if isinstance(item, dict):
                issues.update(number_issues(item.get("price"), "line_items[].price", whole=False))
                issues.update(number_issues(item.get("quantity"), "line_items[].quantity", whole=True))
    if any(sev == "bad_line" for sev, _ in issues):
        return {i for i in issues if i[0] == "bad_line"}  # the line never loads, nothing else applies
    issues.update(date_issues(record, stats, now))
    issues.update(quality_issues(record, kind))
    return issues


def as_id(value):
    if value is None or isinstance(value, (dict, list, bool)):
        return None
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return str(value)


def file_issues(path, kind, report):
    name = path.name
    if path.suffix != ".jsonl":
        report.add("fatal", "file name must end in .jsonl. Other extensions upload without an error but are never processed")
    if not name.startswith(kind):
        report.add("fatal", f"file name must start with `{kind}` and go in the {kind}/ folder")
    size = path.stat().st_size
    if size == 0:
        report.add("fatal", "file is empty")
    if size > MAX_FILE_BYTES:
        report.add("fatal", "file is larger than 1 GB, split it into smaller files")


def validate_file(path, kind, validator, max_examples, ids_out, refs_out):
    report = Report(max_examples)
    print("\n" + "=" * 78)
    print(f"{path.name}  ({kind})")
    print("=" * 78)
    file_issues(path, kind, report)

    known_fields = set(validator.schema["properties"])
    stats = {"dated": 0, "updated_equals_created": 0, "created_dates": Counter()}
    now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    seen_ids = set()
    unknown_fields = Counter()
    total = loaded = valid = blank = bad_lines = 0

    with path.open("rb") as fh:
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

            issues = check_record(record, kind, validator, stats, now)
            for severity, message in sorted(issues):
                report.add(severity, message, line_no)
            if any(sev == "bad_line" for sev, _ in issues):
                bad_lines += 1
                continue
            loaded += 1
            if not any(sev == "error" for sev, _ in issues):
                valid += 1
            unknown_fields.update(f for f in record if f not in known_fields)

            record_id = as_id(record.get("id"))
            if record_id is not None:
                if record_id in seen_ids:
                    report.add("warning", "`id` repeats an earlier line, only the version with the latest `updated_at` is kept", line_no)
                seen_ids.add(record_id)
            if kind == "orders" and (ref := as_id(record.get("customer_id"))) is not None:
                refs_out.append(ref)

    ids_out.update(seen_ids)

    if bad_lines > MAX_BAD_LINES:
        report.add("fatal", f"{bad_lines:,} unreadable lines, more than the limit of {MAX_BAD_LINES}, so the whole file is set aside unprocessed")
    if blank:
        report.notes.append(f"{blank:,} blank lines skipped")
    for field, count in unknown_fields.most_common(10):
        report.notes.append(f"`{field}` is not a PostPilot field and is ignored ({count:,} line(s)), check the spelling if you meant a documented field")
    if stats["dated"] >= 10 and stats["updated_equals_created"] == stats["dated"]:
        report.notes.append("`updated_at` equals `created_at` on every record, it should change whenever the record changes")
    dates = stats["created_dates"]
    if dates:
        first, last = min(dates), max(dates)
        report.notes.append(f"`created_at` runs {first} to {last}")
        if kind == "orders" and (last - first).days <= 400:
            days = (first + datetime.timedelta(days=d) for d in range((last - first).days + 1))
            missing = [d for d in days if d not in dates]
            if missing:
                shown = ", ".join(map(str, missing[:10])) + (", ..." if len(missing) > 10 else "")
                report.notes.append(f"{len(missing)} day(s) in that range have no orders: {shown}")

    report.print()

    fatal = report.count("fatal") > 0
    must_fix = report.count("must_fix") > 0
    print(f"\n  Lines: {total:,}   Loaded: {loaded:,}   Passed validation: {valid:,}   Unreadable: {bad_lines:,}")
    if fatal:
        status = "FAIL, PostPilot will not process this file"
    elif must_fix:
        status = "FIX BEFORE UPLOADING, IDs contain PII"
    elif bad_lines or valid < loaded:
        status = f"PASS WITH ERRORS, {bad_lines + (loaded - valid):,} line(s) will be dropped"
    else:
        status = "PASS"
    print(f"  Result: {status}")
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
    print(f"  {matched:,} of {len(order_refs):,} orders ({pct:.1f}%) have a `customer_id` that matches a customer `id`.")
    if matched < len(order_refs):
        normalized = {i.strip().lower() for i in customer_ids}
        fuzzy = sum(1 for ref in order_refs if ref not in customer_ids and ref.strip().lower() in normalized)
        if fuzzy:
            print(f"  {fuzzy:,} more would match if both sides were trimmed and lowercased the same way.")
        print("  `customer_id` on orders must be the exact `id` you send in the customers file.")
        print("  If these are incremental files, unmatched orders may belong to customers sent earlier.")
    if matched == 0:
        print("  Result: FAIL, no orders match any customer, check that both files use the same ID")
        return False
    print("  Result: PASS" if matched == len(order_refs) else "  Result: CHECK")
    return True


def load_validator(schema_dir, kind):
    path = schema_dir / f"{kind}.schema.json"
    if not path.is_file():
        fail(f"Schema not found: {path}. Download the whole data-ingestion-guide folder, or pass --schemas DIR.")
    schema = json.loads(path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def main():
    parser = argparse.ArgumentParser(description="Validate PostPilot customers/orders JSONL files locally before upload.")
    parser.add_argument("files", nargs="+", type=Path, help="customers*.jsonl and/or orders*.jsonl files")
    parser.add_argument("--examples", type=int, default=5, help="line numbers to show per issue (default 5)")
    parser.add_argument("--schemas", type=Path, default=SCHEMA_DIR, help="folder holding the *.schema.json files")
    args = parser.parse_args()

    validators = {kind: load_validator(args.schemas, kind) for kind in ("customers", "orders")}
    customer_ids, order_refs = set(), []
    kinds_seen = set()
    all_ok = True
    for path in args.files:
        if not path.is_file():
            print(f"Not a file: {path}", file=sys.stderr)
            return 2
        name = path.name.lower()
        if name.startswith("customer"):
            kind = "customers"
        elif name.startswith("order"):
            kind = "orders"
        else:
            print(f"Can't tell if {path} is a customers or orders file. Name it customers_YYYYMMDD.jsonl or "
                  "orders_YYYYMMDD.jsonl.", file=sys.stderr)
            return 2
        kinds_seen.add(kind)
        ids_out = customer_ids if kind == "customers" else set()
        all_ok = validate_file(path, kind, validators[kind], args.examples, ids_out, order_refs) and all_ok

    if kinds_seen == {"customers", "orders"}:
        all_ok = cross_check(customer_ids, order_refs) and all_ok

    print("\nNo field values were printed. This report is safe to share with PostPilot.")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
