import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.test_core import contract_spec


class CliTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.key = self.directory / "key"
        self.contract = self.directory / "contract.json"
        self.contract.write_text(json.dumps(contract_spec()), encoding="utf-8")
        result = self.cli("keygen", "--out", self.key)
        self.assertEqual(result.returncode, 0, result.stderr)

    def cli(self, *args):
        return subprocess.run(
            [sys.executable, "-m", "rowreceipt", *map(str, args)],
            text=True, capture_output=True, check=False,
        )

    def snapshot(self, source, out):
        return self.cli("capture", "--csv", source, "--contract", self.contract, "--key", self.key, "--out", out)

    def test_end_to_end_exit_codes_and_no_clobber(self):
        source = self.directory / "data.csv"
        original = self.directory / "a.json"
        updated = self.directory / "b.json"
        source.write_text("id,group,name,cost,bits\n1,A,original,0,\n", encoding="utf-8")
        self.assertEqual(self.snapshot(source, original).returncode, 0)
        source.write_text("id,group,name,cost,bits\n1,A,updated,0,\n", encoding="utf-8")
        self.assertEqual(self.snapshot(source, updated).returncode, 0)
        result = self.cli("compare", original, original, "--key", self.key)
        self.assertEqual(result.returncode, 0)
        self.assertIn("Match: 1 rows", result.stdout)
        result = self.cli("compare", original, updated, "--key", self.key, "--json")
        self.assertEqual(result.returncode, 1)
        report = json.loads(result.stdout)
        self.assertFalse(report["match"])
        self.assertEqual(report["left_rows"], 1)
        encoded = updated.read_bytes()
        self.assertEqual(self.snapshot(source, updated).returncode, 2)
        self.assertEqual(updated.read_bytes(), encoded)
        updated.write_text('{"format":"rowreceipt/2"}', encoding="utf-8")
        invalid = self.cli("compare", original, updated, "--key", self.key, "--json")
        self.assertEqual(invalid.returncode, 2)
        self.assertEqual(invalid.stdout, "")
        self.assertNotIn("Traceback", invalid.stderr)

    def test_key_file_private_and_exclusive(self):
        first = self.key.read_bytes()
        self.assertEqual(len(first), 32)
        if os.name == "posix":
            self.assertEqual(stat.S_IMODE(self.key.stat().st_mode), 0o600)
        self.assertEqual(self.cli("keygen", "--out", self.key).returncode, 2)
        self.assertEqual(self.key.read_bytes(), first)

    def test_failed_capture_never_publishes(self):
        source = self.directory / "bad.csv"
        source.write_text("id,group,name,cost,bits\n1,A,secret_one,0,\n1,A,secret_two,0,\n", encoding="utf-8")
        output = self.directory / "out.json"
        failure = self.snapshot(source, output)
        self.assertEqual(failure.returncode, 2)
        self.assertIn("duplicate logical key", failure.stderr)
        self.assertNotIn("secret", failure.stderr)
        self.assertFalse(output.exists())

    def test_concurrent_writers_publish_at_most_one(self):
        path = self.directory / "contested.key"
        command = [sys.executable, "-m", "rowreceipt", "keygen", "--out", str(path)]
        with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as first:
            with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as second:
                first.communicate(timeout=10)
                second.communicate(timeout=10)
        self.assertEqual(sorted([first.returncode, second.returncode]), [0, 2])
        self.assertEqual(len(path.read_bytes()), 32)
        self.assertFalse(list(self.directory.glob(".rowreceipt-*")))
