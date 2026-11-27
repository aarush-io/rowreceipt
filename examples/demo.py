"""Create a SQLite dataset and compare it with an independent CSV export."""

import argparse
import csv
import sqlite3
import subprocess
import sys
import tempfile
from contextlib import closing
from pathlib import Path

EXAMPLES = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app", type=Path, help="run a built .pyz instead of an installed module")
    args = parser.parse_args()
    cli = [sys.executable, str(args.app.resolve())] if args.app else [sys.executable, "-m", "rowreceipt"]
    with tempfile.TemporaryDirectory(prefix="rowreceipt-demo-") as temporary:
        work = Path(temporary)
        source = work / "source.sqlite"
        export = work / "export.csv"
        key = work / "secret"
        contract = EXAMPLES / "inventory.contract.json"
        mapping = EXAMPLES / "inventory.csv-map.json"
        left, right, changed = (work / name for name in ("before.json", "after.json", "changed.json"))
        with closing(sqlite3.connect(source)) as db, db:
            db.execute("CREATE TABLE inventory(sku INTEGER PRIMARY KEY, name TEXT, stock INTEGER)")
            db.executemany("INSERT INTO inventory VALUES(?, ?, ?)", [(1, "Cable", 10), (2, "Adapter", 4)])

        def command(*options, expected=0):
            result = subprocess.run([*cli, *map(str, options)], check=False)
            if result.returncode != expected:
                raise SystemExit(f"Expected exit {expected}, got {result.returncode}")

        def write_export(stock):
            with export.open("w", encoding="utf-8", newline="") as stream:
                csv.writer(stream).writerows([
                    ("item_id", "label", "quantity"),
                    (2, "Adapter", 4),
                    (1, "Cable", stock),
                ])

        command("keygen", "--out", key)
        standard = ("--contract", contract, "--key", key)
        command("capture", "--sqlite", source, "--table", "inventory", *standard, "--out", left)
        write_export(10)
        command("capture", "--csv", export, "--map", mapping, *standard, "--out", right)
        write_export(9)
        command("capture", "--csv", export, "--map", mapping, *standard, "--out", changed)
        source.unlink()
        export.unlink()
        command("compare", left, right, "--key", key)
        command("compare", left, changed, "--key", key, expected=1)
        print(f"SQLite and CSV exchanged receipts of {left.stat().st_size} bytes each.")


if __name__ == "__main__":
    main()
