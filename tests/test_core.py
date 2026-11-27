import dataclasses
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from rowreceipt import Contract, Receipt, ReceiptError, capture, compare

KEY = b"\x01" * 32


def contract_spec():
    return {
        "format": "rowreceipt-contract/1",
        "dataset": "inventory",
        "fields": [
            {"name": "id", "type": "integer"},
            {"name": "group", "type": "text"},
            {"name": "name", "type": "text", "nullable": True},
            {"name": "cost", "type": "real"},
            {"name": "bits", "type": "bytes"},
        ],
        "key": ["id", "group"],
        "buckets": 64,
    }


class ContractTests(unittest.TestCase):
    def test_contract_round_trip(self):
        contract = Contract.from_dict(contract_spec())
        self.assertEqual(contract, Contract.from_dict(contract.as_dict()))
        self.assertEqual(contract.digest(), Contract.from_dict(dict(reversed(list(contract_spec().items())))).digest())

    def test_reject_invalid_contracts(self):
        alterations = [
            {"buckets": True}, {"buckets": 63}, {"buckets": 8192}, {"key": None},
            {"key": ["name"]}, {"key": ["id", "id"]}, {"key": [{}]}, {"dataset": "not a name"},
            {"fields": [{"name": "id", "type": []}]}, {"extra": "field"}, {"fields": []},
        ]
        for alteration in alterations:
            with self.subTest(alteration=alteration), self.assertRaises(ReceiptError):
                Contract.from_dict({**contract_spec(), **alteration})

    def test_duplicate_json_keys_and_oversize_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "contract.json"
            path.write_text('{"format":0,"format":1}', encoding="utf-8")
            with self.assertRaisesRegex(ReceiptError, "duplicate"):
                Contract.read(path)
            path.write_bytes(b" " * 65_537)
            with self.assertRaisesRegex(ReceiptError, "size"):
                Contract.read(path)


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.contract = Contract.from_dict(contract_spec())
        self.rows = [
            (1, "A", "snow: ☃\x00", -0.0, b"\x00\xff"),
            (1, "B", None, 2.5, b""),
            (2, "B", "", 9007199254740992, b"\xff"),
        ]

    def test_order_and_negative_zero_do_not_change_receipt(self):
        left = capture(iter(self.rows), self.contract, KEY)
        right = capture(reversed([(1, "A", "snow: ☃\x00", 0.0, b"\x00\xff"), *self.rows[1:]]), self.contract, KEY)
        self.assertEqual(left.to_bytes(), right.to_bytes())
        self.assertEqual(compare(left, right, KEY).left_rows, 3)
        self.assertTrue(compare(left, right, KEY).match)

    def test_same_count_changed_value_in_exactly_one_bucket(self):
        left = capture(self.rows, self.contract, KEY)
        changed = [self.rows[0], self.rows[1], (2, "B", None, 9007199254740992, b"\xff")]
        result = compare(left, capture(changed, self.contract, KEY), KEY)
        self.assertFalse(result.match)
        self.assertEqual(result.left_rows, result.right_rows)
        self.assertEqual(len(result.differences), 1)
        self.assertEqual(result.differences[0].left_rows, result.differences[0].right_rows)

    def test_empty_and_deleted_rows(self):
        empty = capture([], self.contract, KEY)
        self.assertTrue(compare(empty, empty, KEY).match)
        result = compare(capture(self.rows, self.contract, KEY), empty, KEY)
        self.assertEqual(result.right_rows, 0)
        self.assertEqual(sum(item.left_rows for item in result.differences), 3)

    def test_duplicate_keys_fail_and_clean_scratch(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ReceiptError, "duplicate logical key"):
                capture([self.rows[0], self.rows[0]], self.contract, KEY, scratch_dir=temporary)
            self.assertEqual(list(Path(temporary).iterdir()), [])

    def test_iterator_failure_cleans_scratch(self):
        def broken():
            yield self.rows[0]
            raise ReceiptError("input failed")

        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ReceiptError, "input failed"):
                capture(broken(), self.contract, KEY, scratch_dir=temporary)
            self.assertEqual(list(Path(temporary).iterdir()), [])

    def test_wrong_type_and_nonfinite_values_fail_closed(self):
        for row in [
            (True, "A", None, 0, b""), (None, "A", None, 0, b""),
            (1, "A", None, 9007199254740993, b""), (1, "A", None, float("inf"), b""),
            (1, "A", None, float("nan"), b""), (1, "A", "\ud800", 0.0, b""),
            (1, "A", None, 0, "not bytes"), (1 << 63, "A", None, 0, b""),
            (1, "A", None, 0, b"x" * (8 * 1024 * 1024)),
            (1, "A"), "invalid row",
        ]:
            with self.subTest(row_type=type(row)), self.assertRaises(ReceiptError):
                capture([row], self.contract, KEY)

    def test_receipt_size_content_and_roundtrip(self):
        receipt = capture(self.rows, self.contract, KEY)
        raw = receipt.to_bytes()
        self.assertLess(len(raw), 8192)
        for private in (b"inventory", b"snow:", b"\x01" * 3):
            self.assertNotIn(private, raw)
        self.assertEqual(receipt, Receipt.from_dict(json.loads(raw)))

    def test_wrong_key_tampering_and_incompatible_contract(self):
        receipt = capture(self.rows, self.contract, KEY)
        other = capture(self.rows, Contract.from_dict({**contract_spec(), "buckets": 32}), KEY)
        with self.assertRaisesRegex(ReceiptError, "different contracts"):
            compare(receipt, other, KEY)
        for tampered, secret in [
            (receipt, bytes(32)),
            (dataclasses.replace(receipt, mac="e" * 64), KEY),
            (dataclasses.replace(receipt, buckets=((7, "e" * 64), *receipt.buckets[1:])), KEY),
        ]:
            with self.assertRaisesRegex(ReceiptError, "authentication failed"):
                compare(receipt, tampered, secret)

    def test_reject_invalid_receipts(self):
        receipt = json.loads(capture([], self.contract, KEY).to_bytes())
        for replacements in [
            {"format": "rowreceipt/2"}, {"mac": "A" * 64}, {"key_id": 0},
            {"buckets": []}, {"buckets": [[False, "0" * 64]] * 16},
            {"buckets": [[-1, "0" * 64]] * 16}, {"buckets": [[(1 << 63) - 1, "0" * 64]] * 16},
        ]:
            with self.subTest(fields=list(replacements)), self.assertRaises(ReceiptError):
                Receipt.from_dict({**receipt, **replacements})

    def test_protocol_vector(self):
        vector = json.loads(Path(__file__).with_name("vector.json").read_text(encoding="utf-8"))
        receipt = capture(
            map(tuple, vector["input"]),
            Contract.from_dict(vector["contract"]), bytes.fromhex(vector["key_hex"]),
        )
        self.assertEqual(receipt.contract, vector["contract_sha256"])
        self.assertEqual(receipt.mac, vector["receipt_mac"])
        self.assertEqual(hashlib.sha256(receipt.to_bytes()).hexdigest(), vector["receipt_sha256"])
