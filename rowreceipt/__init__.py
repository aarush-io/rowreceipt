"""Compare typed datasets through independently captured receipts."""

from ._io import ReceiptError
from .contract import Contract, Field, read_mapping
from .core import BucketDifference, Comparison, Receipt, capture, compare, read_key
from .sources import csv_rows, sqlite_rows

__version__ = "0.1.0"
__all__ = [
    "BucketDifference", "Comparison", "Contract", "Field", "Receipt", "ReceiptError",
    "capture", "compare", "csv_rows", "read_key", "read_mapping", "sqlite_rows",
]
