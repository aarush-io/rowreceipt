"""Use RowReceipt with records from a host application."""

from pathlib import Path

from rowreceipt import Contract, capture, compare, read_key


def match_exports(left_rows, right_rows, key_path: Path):
    contract = Contract.read(Path(__file__).with_name("inventory.contract.json"))
    key = read_key(key_path)
    before = capture(left_rows, contract, key)
    after = capture(right_rows, contract, key)
    return compare(before, after, key)
