# Contributing

Use CPython 3.11 or newer with SQLite 3.37 or newer. Clone the repository and run the tests and demo from its root.

```sh
python -W error::ResourceWarning -m unittest discover -v
python examples/demo.py
```

A virtual environment is optional for source development. To test installation, follow the [build instructions](docs/build.md). For performance changes, include raw measurements and reproduce the corresponding workload before and after. [Benchmark methodology](docs/benchmarks.md)

Changes to v1 bytes require a compatibility discussion and a new protocol version. Add a small synthetic regression input for adapter edge cases. For adapter contributions, define type mapping and transaction or snapshot guarantees first. The Python iterator interface is enough to prototype externally. [API](docs/api.md)

Report bugs with actionable commands and fake example data. Be mindful that even a receipt can expose dataset metadata. Contributions are available under Apache-2.0.
