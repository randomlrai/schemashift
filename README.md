# SchemaShift

Detects and reports schema drift between dataset versions in CSV or JSON formats.

---

## Installation

```bash
pip install schemashift
```

---

## Usage

Compare two dataset versions and get a detailed drift report:

```python
from schemashift import SchemaShift

detector = SchemaShift()

report = detector.compare("data_v1.csv", "data_v2.csv")
print(report.summary())
```

**Example output:**

```
Schema Drift Report
-------------------
Added columns   : ['email', 'signup_date']
Removed columns : ['phone']
Type changes    : {'age': int -> str}
Nullable changes: {'user_id': False -> True}
```

You can also compare JSON files:

```python
report = detector.compare("schema_old.json", "schema_new.json")
report.export("drift_report.json")
```

Run from the command line:

```bash
schemashift compare data_v1.csv data_v2.csv
```

---

## Features

- Detects added, removed, and renamed columns
- Tracks data type and nullability changes
- Supports CSV and JSON formats
- CLI and Python API
- Exportable drift reports (JSON, plain text)

---

## License

This project is licensed under the [MIT License](LICENSE).