"""Command-line interface for RowReceipt."""

import argparse
import json
import os
import secrets
import sys
from contextlib import closing
from dataclasses import asdict
from pathlib import Path

from . import Contract, Receipt, ReceiptError, __version__, capture, compare, csv_rows, read_key
from . import read_mapping, sqlite_rows
from ._io import write_new


def _parser():
    parser = argparse.ArgumentParser(
        prog="rowreceipt", description="Compare dataset copies without transferring rows."
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)
    keygen = commands.add_parser("keygen", help="create a private comparison key")
    keygen.add_argument("--out", required=True, type=Path, help="new binary key file")
    snapshot = commands.add_parser("capture", help="create a receipt from one local dataset")
    source = snapshot.add_mutually_exclusive_group(required=True)
    source.add_argument("--csv", type=Path, help="UTF-8 CSV with a header")
    source.add_argument("--sqlite", type=Path, help="SQLite database")
    snapshot.add_argument("--table", help="ordinary SQLite table to read")
    snapshot.add_argument("--contract", required=True, type=Path, help="logical dataset contract")
    snapshot.add_argument("--map", dest="mapping", type=Path, help="JSON logical-to-physical column mapping")
    snapshot.add_argument("--key", required=True, type=Path, help="binary comparison key")
    snapshot.add_argument("--scratch-dir", type=Path, help="parent directory for the temporary digest index")
    snapshot.add_argument("--out", required=True, type=Path, help="new receipt file")
    comparison = commands.add_parser("compare", help="authenticate and compare two receipts")
    comparison.add_argument("left", type=Path)
    comparison.add_argument("right", type=Path)
    comparison.add_argument("--key", required=True, type=Path, help="binary comparison key")
    comparison.add_argument("--json", action="store_true", help="print machine-readable comparison")
    return parser


def _capture(args):
    if (args.sqlite is None) != (args.table is None):
        raise ReceiptError("--table is required with --sqlite and unavailable with --csv")
    if os.path.lexists(args.out):
        raise ReceiptError("output already exists")
    contract = Contract.read(args.contract)
    key = read_key(args.key)
    mapping = read_mapping(args.mapping) if args.mapping is not None else None
    rows = (
        csv_rows(args.csv, contract, mapping) if args.csv is not None
        else sqlite_rows(args.sqlite, args.table, contract, mapping)
    )
    with closing(rows):
        receipt = capture(rows, contract, key, scratch_dir=args.scratch_dir)
    write_new(args.out, receipt.to_bytes())
    print(f"Captured {receipt.rows} rows in {len(receipt.buckets)} buckets.")
    return 0


def _compare(args):
    result = compare(Receipt.read(args.left), Receipt.read(args.right), read_key(args.key))
    if args.json:
        print(json.dumps({"match": result.match, **asdict(result)}, sort_keys=True))
    elif result.match:
        print(f"Match: {result.left_rows} rows.")
    else:
        print(
            f"Mismatch: {result.left_rows} left rows, {result.right_rows} right rows, "
            f"{len(result.differences)} changed buckets."
        )
        for entry in result.differences:
            print(f"  Bucket {entry.bucket}: {entry.left_rows} left, {entry.right_rows} right")
    return 0 if result.match else 1


def main(argv=None):
    args = _parser().parse_args(argv)
    try:
        if args.command == "keygen":
            write_new(args.out, secrets.token_bytes(32))
            print("Created a 32-byte secret key.")
            return 0
        if args.command == "capture":
            return _capture(args)
        return _compare(args)
    except ReceiptError as exc:
        print(f"rowreceipt: {exc}", file=sys.stderr)
        return 2
    except FileExistsError:
        print("rowreceipt: output already exists", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"rowreceipt: file operation failed ({exc.strerror or type(exc).__name__})", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("rowreceipt: interrupted", file=sys.stderr)
        return 130
