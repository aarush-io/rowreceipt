"""Version 1 logical dataset contract."""

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

from ._io import ReceiptError, canonical_json, read_json

CONTRACT_FORMAT = "rowreceipt-contract/1"
_MAX_DOCUMENT = 64 * 1024
_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_.-]{0,63}")
KINDS = frozenset(("integer", "real", "text", "bytes"))


def valid_bucket_count(count):
    return type(count) is int and 16 <= count <= 4096 and count & (count - 1) == 0


@dataclass(frozen=True, slots=True)
class Field:
    name: str
    kind: str
    nullable: bool


@dataclass(frozen=True, slots=True)
class Contract:
    dataset: str
    fields: tuple[Field, ...]
    key: tuple[str, ...]
    buckets: int

    @classmethod
    def from_dict(cls, document: dict) -> "Contract":
        """Validate and normalize a v1 contract."""
        if not isinstance(document, dict) or document.keys() != {
            "format", "dataset", "fields", "key", "buckets"
        } or document["format"] != CONTRACT_FORMAT:
            raise ReceiptError("expected a rowreceipt-contract/1 document")
        dataset = document["dataset"]
        if not isinstance(dataset, str) or not _NAME.fullmatch(dataset):
            raise ReceiptError("invalid logical dataset name")
        buckets = document["buckets"]
        if not valid_bucket_count(buckets):
            raise ReceiptError("buckets must be a power of two from 16 to 4096")
        inputs = document["fields"]
        if not isinstance(inputs, list) or not 1 <= len(inputs) <= 128:
            raise ReceiptError("fields must contain 1 to 128 field definitions")
        fields = {}
        for item in inputs:
            if not isinstance(item, dict) or set(item) not in (
                {"name", "type"}, {"name", "type", "nullable"}
            ):
                raise ReceiptError("invalid field definition")
            name, kind, nullable = item["name"], item["type"], item.get("nullable", False)
            if not isinstance(name, str) or not _NAME.fullmatch(name) or name in fields:
                raise ReceiptError("field names must be unique logical identifiers")
            if not isinstance(kind, str) or kind not in KINDS or type(nullable) is not bool:
                raise ReceiptError("invalid field type or nullability")
            fields[name] = Field(name, kind, nullable)
        key = document["key"]
        if not isinstance(key, list) or not 1 <= len(key) <= len(fields):
            raise ReceiptError("key must list one or more logical fields")
        seen = set()
        for name in key:
            if not isinstance(name, str) or name not in fields or name in seen:
                raise ReceiptError("key fields must be known and unique")
            if fields[name].nullable:
                raise ReceiptError("key fields must be non-nullable")
            seen.add(name)
        return cls(dataset, tuple(fields.values()), tuple(key), buckets)

    @classmethod
    def read(cls, path: str | Path) -> "Contract":
        return cls.from_dict(read_json(path, _MAX_DOCUMENT))

    def as_dict(self) -> dict:
        return {
            "format": CONTRACT_FORMAT,
            "dataset": self.dataset,
            "fields": [
                {"name": item.name, "type": item.kind, "nullable": item.nullable}
                for item in self.fields
            ],
            "key": list(self.key),
            "buckets": self.buckets,
        }

    def digest(self) -> bytes:
        return hashlib.sha256(canonical_json(self.as_dict())).digest()


def read_mapping(path: str | Path) -> dict[str, str]:
    mapping = read_json(path, _MAX_DOCUMENT)
    if not isinstance(mapping, dict):
        raise ReceiptError("column mapping must be a JSON object")
    return mapping


def physical_columns(contract, mapping):
    mapping = {} if mapping is None else mapping
    names = {field.name for field in contract.fields}
    if not isinstance(mapping, dict) or not mapping.keys() <= names:
        raise ReceiptError("column mapping contains an unknown logical field")
    columns = [mapping.get(field.name, field.name) for field in contract.fields]
    if any(not isinstance(name, str) or not name or "\x00" in name for name in columns):
        raise ReceiptError("invalid physical column name")
    if len(set(columns)) != len(columns):
        raise ReceiptError("physical columns must be unique")
    return columns
