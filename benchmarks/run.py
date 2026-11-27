"""Benchmark RowReceipt and optional native SQLite tools on the same data."""

import argparse
import csv
import json
import os
import platform
import sqlite3
import subprocess
import sys
import tempfile
import time
from contextlib import closing
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "examples" / "inventory.contract.json"


def sample(argv, expected=0, scratch=None):
    peak_scratch = 0
    with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
        started = time.perf_counter()
        with subprocess.Popen(argv, cwd=ROOT, stdout=stdout, stderr=stderr) as process:
            while True:
                pid, status, usage = os.wait4(process.pid, os.WNOHANG)
                if pid:
                    process.returncode = os.waitstatus_to_exitcode(status)
                    break
                if scratch is not None:
                    for item in scratch.glob("*/fingerprints.sqlite"):
                        try:
                            peak_scratch = max(peak_scratch, item.stat().st_size)
                        except FileNotFoundError:
                            pass
                time.sleep(0.002)
            elapsed = time.perf_counter() - started
        stdout.seek(0)
        output = stdout.read()
        if process.returncode != expected:
            stderr.seek(0)
            raise RuntimeError(f"{argv}: exit {process.returncode}: {stderr.read()!r}")
    return {
        "wall_s": elapsed,
        "user_s": usage.ru_utime,
        "system_s": usage.ru_stime,
        "peak_rss_kib": usage.ru_maxrss,
        "peak_scratch_bytes_sampled": peak_scratch,
        "stdout_bytes": len(output),
    }, output


def rows(count, altered):
    for index in range(1, count + 1):
        yield index, f"product-{index:08d}", index % 37 + int(altered and index == count // 2)


def setup(root, count):
    left, right, exported = (root / name for name in ("left.db", "right.db", "right.csv"))
    for path, altered in ((left, False), (right, True)):
        with closing(sqlite3.connect(path)) as db, db:
            db.execute("CREATE TABLE inventory(sku INTEGER PRIMARY KEY, name TEXT, stock INTEGER)")
            db.executemany("INSERT INTO inventory VALUES (?, ?, ?)", rows(count, altered))
    with exported.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(("sku", "name", "stock"))
        writer.writerows(rows(count, True))
    return left, right, exported


def workload(args, root, count):
    left, right, exported = setup(root, count)
    work = root / "scratch"
    work.mkdir()
    key = root / "secret"
    key.write_bytes(os.urandom(32))
    cli = [sys.executable, "-m", "rowreceipt"] if args.app is None else [sys.executable, str(args.app)]
    settings = ["--contract", str(CONTRACT), "--key", str(key), "--scratch-dir", str(work)]
    results = []

    def run(name, argv, expected=0, scratch=None):
        times, output = sample(argv, expected, scratch)
        results.append({"operation": name, "repeat": repeat, **times})
        return output

    for repeat in range(1, args.repeats + 1):
        source, destination, csv_copy = (root / f"{name}-{repeat}.json" for name in ("src", "dst", "csv"))
        run("rowreceipt_startup", [*cli, "--version"])
        for name, path, output in (
            ("rowreceipt_sqlite_left", left, source), ("rowreceipt_sqlite_right", right, destination),
            ("rowreceipt_csv_right", exported, csv_copy),
        ):
            adapter = ["--csv", str(path)] if path == exported else ["--sqlite", str(path), "--table", "inventory"]
            run(name, [*cli, "capture", *settings, *adapter, "--out", str(output)], scratch=work)
            results[-1]["receipt_bytes"] = output.stat().st_size
        common = [*cli, "compare", str(source), "--key", str(key), "--json"]
        for name, receipt in (("rowreceipt_compare_sqlite", destination), ("rowreceipt_compare_csv", csv_copy)):
            report = json.loads(run(name, [*common, str(receipt)], expected=1))
            if len(report["differences"]) != 1 or report["left_rows"] != count or report["right_rows"] != count:
                raise RuntimeError("expected exactly one changed bucket and equal row counts")
        if destination.read_bytes() != csv_copy.read_bytes():
            raise RuntimeError("the destination SQLite and CSV receipts should be identical")
        if args.sqldiff:
            output = run("sqldiff", [
                str(args.sqldiff), "--primarykey", "--table", "inventory", str(left), str(right),
            ])
            if not output.startswith(b"UPDATE inventory SET stock=") or len(output.splitlines()) != 1:
                raise RuntimeError(f"expected one update from sqldiff, got {output!r}")
        if args.dbhash:
            a = run("dbhash_left", [str(args.dbhash), "--without-schema", "--like", "inventory", str(left)]).split()[0]
            b = run("dbhash_right", [str(args.dbhash), "--without-schema", "--like", "inventory", str(right)]).split()[0]
            if len(a) != 40 or len(b) != 40 or a == b:
                raise RuntimeError("expected two distinct SHA-1 database hashes")
    data = {path.name: path.stat().st_size for path in (left, right, exported)}
    return {"rows_per_side": count, "input_bytes": data, "samples": results}


def main():
    if not sys.platform.startswith("linux"):
        raise SystemExit("The CPU/RSS benchmark runner currently requires Linux.")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=int, nargs="+", default=[1000, 100000])
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--sqldiff", type=lambda p: Path(p).resolve())
    parser.add_argument("--dbhash", type=lambda p: Path(p).resolve())
    parser.add_argument("--app", type=lambda p: Path(p).resolve())
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if args.repeats < 1 or any(count < 2 for count in args.rows):
        parser.error("need a positive repeat count and at least two rows per workload")
    cpu = next(
        (line.partition(":")[2].strip() for line in Path("/proc/cpuinfo").read_text().splitlines()
         if line.startswith("model name")), "unknown",
    )
    paths = {name: str(path) for name, path in vars(args).items() if name in {"sqldiff", "dbhash", "app"} and path}
    report = {"platform": platform.platform(), "cpu": cpu, "python": platform.python_version(),
              "python_sqlite": sqlite3.sqlite_version, "tools": paths, "workloads": []}
    for count in args.rows:
        with tempfile.TemporaryDirectory(prefix="rowreceipt-bench-") as directory:
            report["workloads"].append(workload(args, Path(directory), count))
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
