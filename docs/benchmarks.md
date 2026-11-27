# Performance and reliability

The Linux workload generates two SQLite files with identical tables and one CSV representation of the right table. One non-key value differs between the left and right sides. The workload verifies that RowReceipt sees exactly one changed bucket, that SQLite and CSV produce byte-identical right-side receipts, that sqldiff emits one UPDATE and that dbhash distinguishes the logical content. Database and export generation time is outside measurement.

Run from the repository root on Linux.

```sh
python benchmarks/run.py --rows 1000 100000 1000000 --repeats 5 \
  --sqldiff /path/to/sqldiff --dbhash /path/to/dbhash --out results.json
```

The optional baseline tools are SQLite 3.54.1. Use the official Linux x64 download to obtain sqldiff. Build dbhash from the version-matched source tree and amalgamation. The published SHA3-256 values for the tools, source, and amalgamation respectively were `555635de98534d87a67ee2e6e1b0d79f494b1b33b223477d3e7a8ea0c66e416f`, `877c6f4996ce7adb368686bce21638de9e3d91534832ad3d9d119037d1bc22ad` and `92281c86e2957f9b9305890f9ac04204caa7b677cc868dc326d942689df28e30`. [SQLite downloads](https://www.sqlite.org/download.html) · [dbhash docs](https://www.sqlite.org/dbhash.html) · [sqldiff docs](https://www.sqlite.org/sqldiff.html)

```sh
cc -O2 -I /path/to/amalgamation /path/to/source/tool/dbhash.c /path/to/amalgamation/sqlite3.c -o dbhash -ldl -pthread
```

The runner measures wall time at process completion and collects process CPU time and peak RSS through Linux wait4. It samples the temporary index every 2 ms. Sampling and scheduling introduce noise, especially for process launches and short runs. RSS can include the footprint inherited at fork before exec. The system file cache is left intact and inputs are reused across runs. The current benchmarks are a warm-cache, single-machine reference.

RowReceipt and dbhash are timed per independent capture. RowReceipt incurs an additional receipt comparison, whereas dbhash users can compare its hexadecimal digests. sqldiff runs once with simultaneous access to both SQLite files and can emit the exact update. RowReceipt reads both SQLite and CSV without staging conversion and publishes bucket-level evidence only. File sizes below represent the exchange payload before encryption or transport metadata. The runner has no network transfer, battery instrumentation or fault-injection workload for power loss.

[Raw Linux measurements](../benchmarks/linux-x86_64.json)

## Results

Median of five runs on a Linux x86-64 AMD EPYC 9V74 host with CPython 3.12.14 and SQLite 3.53.1 for RowReceipt. Baselines use SQLite 3.54.1. Capture time is per source.

| Operation | 1,000 rows | 100,000 rows | 1,000,000 rows |
|---|---:|---:|---:|
| RowReceipt CLI startup | 42 ms | 44 ms | 42 ms |
| RowReceipt SQLite capture | 55 ms | 629 ms | 8.35 s |
| RowReceipt CSV capture | 55 ms | 822 ms | 10.51 s |
| RowReceipt offline compare | 44 ms | 44 ms | 46 ms |
| dbhash single SQLite source | 2.3 ms | 19 ms | 162 ms |
| sqldiff two SQLite sources | 4.5 ms | 101 ms | 1.02 s |
| Receipt bytes per source | 4,870 | 5,001 | 5,065 |

At one million rows, the SQLite capture processed about 120,000 rows per second with 49.1 MiB median peak RSS, about 81.4 MB of sampled scratch, and 7.29 s user plus 1.06 s kernel CPU time. The source database occupied 27,189,248 bytes. CSV capture reached 51.3 MiB median peak RSS. The scratch index is discarded without a durability requirement. In smaller runs the cache can keep most pages in memory, leaving a much smaller on-disk index.

Profiling 100,000 rows identified row fingerprint generation and B-tree insertion as the main costs. Reusing initialized HMAC state avoids repeatedly setting up the same key, and a larger SQLite cache reduces scratch writes on the million-row workload. Together these reduced median SQLite capture from 10.65 s to 8.35 s on this machine, while median peak RSS rose from 24.1 MiB to 49.1 MiB. The reference vector and equality tests passed with both builds. [Raw measurements before tuning](../benchmarks/linux-x86_64-before.json)

Native utilities win wall-clock time for the workflows they support. Use dbhash for a compact exact comparison of compatible SQLite sources and sqldiff for a concrete row-level patch with both sources present. RowReceipt adds authenticated, cross-format, bucket-level comparison while keeping the exchange payload under 8 KiB per side. The results here describe this controlled workload only.
