import csv
import os
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from rowreceipt import Contract, ReceiptError, capture, compare, csv_rows, sqlite_rows
from tests.test_core import KEY, contract_spec


class SourceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name)
        self.contract = Contract.from_dict(contract_spec())

    def test_csv_and_live_wal_with_renamed_columns(self):
        db_path = self.path / ("a%# database.db" if os.name == "nt" else "a?%# database.db")
        csv_path = self.path / "a.csv"
        with closing(sqlite3.connect(db_path)) as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("PRAGMA wal_autocheckpoint=0")
            db.execute('CREATE TABLE "on""disk" ("i""d" INTEGER, "group" TEXT, name TEXT, cost REAL, bits BLOB)')
            db.executemany('INSERT INTO "on""disk" VALUES(?,?,?,?,?)', [
                (1, "A", "two\r\nlines ☃", -0.0, b"\x00\xff"),
                (2, "A", None, 7.25, b""),
                (3, "A", r"\N", 4, b"\x00"),
            ])
            db.commit()
            self.assertTrue((self.path / (db_path.name + "-wal")).exists())
            with csv_path.open("w", encoding="utf-8-sig", newline="") as stream:
                csv.writer(stream).writerows([
                    ("state", "label", "amount", "number", "area"),
                    ("00", r"\\N", "4e0", 3, "A"),
                    ("", r"\N", "7.25", 2, "A"),
                    ("00FF", "two\r\nlines ☃", "-0.0", 1, "A"),
                ])
            with closing(sqlite_rows(db_path, 'on"disk', self.contract, {"id": 'i"d'})) as rows:
                left = capture(rows, self.contract, KEY)
            with closing(csv_rows(csv_path, self.contract, {
                "id": "number", "group": "area", "name": "label", "cost": "amount", "bits": "state"
            })) as rows:
                right = capture(rows, self.contract, KEY)
        self.assertTrue(compare(left, right, KEY).match)
        self.assertEqual(left.rows, 3)

    def test_one_sqlite_snapshot_even_when_writer_commits(self):
        db_path = self.path / "wal.db"
        with closing(sqlite3.connect(db_path)) as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute('CREATE TABLE source(id, "group", name, cost, bits)')
            db.executemany("INSERT INTO source VALUES(?, 'g', 'old', 0, x'')", [(1,), (2,)])
            db.commit()
            with closing(sqlite_rows(db_path, "source", self.contract)) as rows:
                self.assertEqual(next(rows)[2], "old")
                db.execute("UPDATE source SET name='new'")
                db.commit()
                self.assertEqual([row[2] for row in rows], ["old"])

    def test_views_and_missing_columns_fail(self):
        path = self.path / "test.db"
        with closing(sqlite3.connect(path)) as db:
            db.executescript("CREATE TABLE plain(id); CREATE VIEW other AS SELECT * FROM plain;")
        with self.assertRaisesRegex(ReceiptError, "ordinary table"):
            list(sqlite_rows(path, "other", self.contract))
        with self.assertRaisesRegex(ReceiptError, "column"):
            list(sqlite_rows(path, "plain", self.contract))
        with self.assertRaises(ReceiptError):
            list(sqlite_rows(path, 'plain"; DELETE FROM plain; --', self.contract))

    def test_csv_failures(self):
        path = self.path / "input.csv"
        for content in [
            "", "id,id\n1,2\n", "id,name\n1,A\n", "id,group,name,cost,bits\n1,A,last\n",
            "id,group,name,cost,bits\n1,A,\"unterminated",
            "id,group,name,cost,bits\n1,A,word,4,0a6\n",
            "id,group,name,cost,bits\n1,A,\\invalid,4,\n",
            "id,group,name,cost,bits\n01junk,A,word,4,\n",
            "id,group,name,cost,bits\n1,A,word,nan,\n",
        ]:
            with self.subTest(content=content):
                path.write_text(content, encoding="utf-8")
                with self.assertRaises(ReceiptError):
                    list(csv_rows(path, self.contract))

    def test_csv_detects_mutation_and_bounded_records(self):
        path = self.path / "input.csv"
        path.write_text("id,group,name,cost,bits\n1,A,word,4,\n", encoding="utf-8")
        with closing(csv_rows(path, self.contract)) as rows:
            next(rows)
            with path.open("a", encoding="utf-8") as stream:
                stream.write("2,A,word,4,\n")
            with self.assertRaisesRegex(ReceiptError, "changed"):
                list(rows)
        path.write_text("id,group,name,cost,bits\n1,A," + "x" * (2 * 1024 * 1024), encoding="utf-8")
        with self.assertRaisesRegex(ReceiptError, "record exceeds"):
            list(csv_rows(path, self.contract))

    def test_mapping_validation(self):
        with self.assertRaisesRegex(ReceiptError, "unknown logical"):
            list(csv_rows(self.path / "missing", self.contract, {"unknown": "column"}))
        with self.assertRaisesRegex(ReceiptError, "unique"):
            list(csv_rows(self.path / "missing", self.contract, {"id": "name"}))
