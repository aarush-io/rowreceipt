# Python API

Import from `rowreceipt`. CPython 3.11+ with SQLite 3.37+ supports both file adapters.

| API | Behavior |
|---|---|
| `Contract.read(path)`, `Contract.from_dict(document)` | Validate the logical dataset structure and normalize defaults. |
| `Contract.as_dict()`, `Contract.digest()` | Export the normalized contract and the raw 32-byte digest. |
| `read_key(path)`, `read_mapping(path)` | Read a raw key or a column-mapping object. Create a new key with the CLI or `secrets.token_bytes(32)`. |
| `sqlite_rows(path, table, contract, mapping=None)` | Stream a read transaction from one ordinary table. Close the iterator after an early exit. |
| `csv_rows(path, contract, mapping=None)` | Stream typed rows from a stable CSV. Close the iterator after an early exit. |
| `capture(rows, contract, key, *, scratch_dir=None)` | Consume a typed iterable and return a `Receipt`. No receipt is emitted on failure. The caller owns the source iterator. |
| `Receipt.read(path)`, `Receipt.from_dict(document)`, `receipt.to_bytes()` | Parse a structural receipt or render canonical bytes. Authentication occurs in comparison. |
| `compare(left, right, key)` | Verify both receipts and return a `Comparison` with `match`, `left_rows`, `right_rows` and a tuple of bucket differences. |

Adapters yield tuples or lists in contract field order. Supported column values are `None`, signed 64-bit `int`, finite `float`, `str` and `bytes` under their respective field declarations. Use well-defined snapshot semantics when implementing an adapter. Capture may raise `ReceiptError` for bad data or compatibility problems, `OSError` for local I/O failures and exceptions from your input iterator.

```python
from contextlib import closing

from rowreceipt import Contract, Receipt, capture, compare, read_key, sqlite_rows

contract = Contract.read("inventory.contract.json")
key = read_key("exchange.key")
with closing(sqlite_rows("inventory.db", "inventory", contract)) as rows:
    local = capture(rows, contract, key)

remote = Receipt.read("destination.json")
if not compare(local, remote, key).match:
    raise SystemExit(1)
```

For a CLI integration, `compare --json` reports `match`, `left_rows`, `right_rows` and `differences`, where each difference has `bucket`, `left_rows` and `right_rows`. Exit code 0 is a match or successful write, 1 is a valid mismatch, 2 is a usage, input, authentication or operational failure, and 130 indicates interruption. An error produces no comparison JSON. [Protocol](protocol.md) · [Runnable example](../examples/demo.py)
