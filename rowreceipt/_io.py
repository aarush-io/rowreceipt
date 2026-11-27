"""Bounded JSON parsing and no-clobber publication."""

import json
import os
import stat
import tempfile
from pathlib import Path


class ReceiptError(ValueError):
    """An invalid input, incompatible receipt, or unavailable resource."""


def regular_file(path):
    resolved = Path(path).resolve(strict=True)
    if not stat.S_ISREG(resolved.stat().st_mode):
        raise ReceiptError("expected a regular input file")
    return resolved


def read_bytes(path, limit):
    with regular_file(path).open("rb") as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise ReceiptError("input file exceeds the size limit")
    return data


def _unique_keys(pairs):
    result = {}
    for name, value in pairs:
        if name in result:
            raise ReceiptError("duplicate JSON object field")
        result[name] = value
    return result


def read_json(path, limit):
    try:
        return json.loads(read_bytes(path, limit).decode("utf-8"), object_pairs_hook=_unique_keys)
    except (UnicodeError, ValueError, RecursionError) as exc:
        if isinstance(exc, ReceiptError):
            raise
        raise ReceiptError("invalid UTF-8 JSON input") from exc


def canonical_json(value):
    return json.dumps(
        value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("ascii")


def write_new(path, data):
    """Publish a complete file without replacing a file or symlink."""
    path = Path(path)
    fd, name = tempfile.mkstemp(prefix=".rowreceipt-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(name, path)
    finally:
        os.unlink(name)
