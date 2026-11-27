# Build and distribution

Use CPython 3.11 or newer with SQLite 3.37 or newer. The zipapp is executable through Python and needs no package installer or account. The wheel installs a CLI and Python API. Neither artifact contains a copy of CPython.

From the project root, build the zipapp and a source archive offline.

```sh
python scripts/build_release.py --out dist
python dist/rowreceipt-0.1.0.pyz --version
python examples/demo.py --app dist/rowreceipt-0.1.0.pyz
```

To reproduce the release wheel with the declared versions already installed, use a clean CPython 3.12 environment. Otherwise install the pinned build tools from your trusted Python index first.

```sh
python -m pip install setuptools==84.2.1 wheel==0.48.0
export SOURCE_DATE_EPOCH=1795737600
python -m pip wheel --no-build-isolation --no-deps --wheel-dir dist .
python scripts/build_release.py --out dist
(cd dist && sha256sum --check SHA256SUMS)
```

For a byte comparison, repeat into a clean checkout or source archive extraction, using the same Python version and build tools. The zipapp and source archive normalize text line endings and ZIP entry times and modes. The wheel is reproducible in the tested Linux environment with the fixed epoch. For PowerShell, use `$env:SOURCE_DATE_EPOCH = "1795737600"` and `Get-FileHash` for verification.

```sh
python -m pip install --no-index --no-deps dist/rowreceipt-0.1.0-py3-none-any.whl
rowreceipt --version
```

The GitHub release job builds and tests assets when a matching version tag is pushed. It runs a Linux/macOS/Windows matrix before publishing assets. Publishing the wheel to PyPI is a later step requiring project ownership and a trusted publisher configuration. Keeping the installable wheel and zipapp together makes a separate container, OS package or service unnecessary for the initial workflow.

MIT would also keep adoption permissive. Apache-2.0 adds explicit patent terms while permitting commercial embedding. Copyleft would impose reciprocal obligations in some redistribution scenarios and would make some embedded integrations harder to adopt.

RowReceipt is Apache-2.0 to allow permissive integration, redistribution and commercial use with an explicit patent grant. It ships no third-party runtime package. The host Python distribution and its linked SQLite retain their own terms. Setuptools and wheel are build tools and are outside the distributed archives. [CPython license](https://docs.python.org/3/license.html) · [SQLite copyright](https://sqlite.org/copyright.html) · [PyPI trusted publishers](https://docs.pypi.org/trusted-publishers/using-a-publisher/)
