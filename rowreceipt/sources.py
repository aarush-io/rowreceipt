"""Read ordinary SQLite tables and typed UTF-8 CSV exports."""

import csv
import os
import re
import sqlite3
from collections.abc import Iterator
from contextlib import closing
from pathlib import Path

from ._io import ReceiptError, regular_file
from .contract import Contract, physical_columns

MAX_ROW_BYTES = 8 * 1024 * 1024
_MAX_CSV_RECORD = 2 * 1024 * 1024
_MAX_CSV_FIELD = 128 * 1024
_INTEGER = re.compile(r"[+-]?[0-9]{1,19}")
_REAL = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?")
_HEX = re.compile(r"[0-9a-fA-F]*")


def _quote_identifier(name):
    return '"' + name.replace('"', '""') + '"'


def sqlite_rows(
    path: str | Path, table: str, contract: Contract, mapping: dict[str, str] | None = None
) -> Iterator[tuple]:
    """Yield mapped fields from a single read-only SQLite transaction."""
    columns = physical_columns(contract, mapping)
    if not isinstance(table, str) or not table or "\x00" in table:
        raise ReceiptError("invalid SQLite table name")
    if sqlite3.sqlite_version_info < (3, 37):
        raise ReceiptError("SQLite input requires SQLite 3.37 or later")
    source = regular_file(path)
    try:
        with closing(sqlite3.connect(source.as_uri() + "?mode=ro", uri=True, timeout=5)) as db:
            db.execute("PRAGMA trusted_schema=OFF")
            db.execute("PRAGMA query_only=ON")
            if hasattr(db, "setconfig") and hasattr(sqlite3, "SQLITE_DBCONFIG_DEFENSIVE"):
                db.setconfig(sqlite3.SQLITE_DBCONFIG_DEFENSIVE, True)
            db.setlimit(sqlite3.SQLITE_LIMIT_LENGTH, MAX_ROW_BYTES)
            db.execute("BEGIN")
            if db.execute(
                "SELECT 1 FROM pragma_table_list WHERE schema='main' AND name=? AND type='table'",
                (table,),
            ).fetchone() is None:
                raise ReceiptError("source SQLite table is missing or is not an ordinary table")
            known = {
                item[0] for item in db.execute(
                    "SELECT name FROM pragma_table_xinfo(?, 'main') WHERE hidden=0", (table,)
                )
            }
            if not set(columns) <= known:
                raise ReceiptError("mapped SQLite column is missing or is not an ordinary column")
            projection = ", ".join(map(_quote_identifier, columns))
            yield from db.execute(f"SELECT {projection} FROM main.{_quote_identifier(table)}")
    except sqlite3.Error as exc:
        code = getattr(exc, "sqlite_errorname", None)
        raise ReceiptError(f"SQLite source read failed ({code or 'SQLite error'})") from exc


class _CsvLines:
    """Bound an entire logical record, including multiline quoted text."""

    def __init__(self, stream):
        self.stream = stream
        self.remaining = _MAX_CSV_RECORD

    def __iter__(self):
        return self

    def __next__(self):
        line = self.stream.readline(self.remaining + 1)
        if not line:
            raise StopIteration
        self.remaining -= len(line)
        if self.remaining < 0:
            raise ReceiptError("CSV record exceeds the character limit")
        return line


def _csv_value(value, field, row_number):
    if value == r"\N":
        return None
    if field.kind == "text":
        if not value.startswith("\\"):
            return value
        if value.startswith("\\\\"):
            return value[1:]
    elif field.kind == "integer" and _INTEGER.fullmatch(value):
        return int(value)
    elif field.kind == "real" and _REAL.fullmatch(value):
        return float(value)
    elif field.kind == "bytes" and len(value) % 2 == 0 and _HEX.fullmatch(value):
        return bytes.fromhex(value)
    raise ReceiptError(f"CSV record {row_number}, field {field.name}: invalid {field.kind}")


def _csv_signature(stream):
    info = os.fstat(stream.fileno())
    return info.st_size, info.st_mtime_ns, info.st_ctime_ns


def csv_rows(
    path: str | Path, contract: Contract, mapping: dict[str, str] | None = None
) -> Iterator[tuple]:
    """Yield mapped, typed tuples from an immutable UTF-8 CSV export."""
    columns = physical_columns(contract, mapping)
    with regular_file(path).open("r", encoding="utf-8-sig", newline="") as stream:
        before = _csv_signature(stream)
        lines = _CsvLines(stream)
        reader = csv.reader(lines, strict=True)
        try:
            header = next(reader, [])
            if (
                not header or any(not name or "\x00" in name or len(name) > _MAX_CSV_FIELD for name in header)
                or len(set(header)) != len(header)
            ):
                raise ReceiptError("CSV needs a non-empty header with unique column names")
            indices = {name: index for index, name in enumerate(header)}
            if not set(columns) <= indices.keys():
                raise ReceiptError("mapped column is missing from the CSV header")
            selected = [indices[name] for name in columns]
            lines.remaining = _MAX_CSV_RECORD
            for number, row in enumerate(reader, start=2):
                lines.remaining = _MAX_CSV_RECORD
                if len(row) != len(header):
                    raise ReceiptError(f"CSV record {number} has a different width from its header")
                if any(len(value) > _MAX_CSV_FIELD for value in row):
                    raise ReceiptError(f"CSV record {number} has a field exceeding the character limit")
                yield tuple(
                    _csv_value(row[index], field, number)
                    for index, field in zip(selected, contract.fields)
                )
        except (csv.Error, UnicodeError) as exc:
            raise ReceiptError(f"invalid CSV near physical line {reader.line_num + 1}") from exc
        if before != _csv_signature(stream):
            raise ReceiptError("CSV changed during capture")
