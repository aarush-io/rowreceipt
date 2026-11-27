"""Build the reproducible zipapp and source archive from the project tree."""

import argparse
import hashlib
import sys
from pathlib import Path
from zipfile import ZIP_STORED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from rowreceipt import __version__  # noqa: E402

SOURCE_DIRS = (".github", "benchmarks", "docs", "examples", "rowreceipt", "scripts", "tests")
SOURCE_FILES = (
    ".gitignore", "CHANGELOG.md", "CODE_OF_CONDUCT.md", "CONTRIBUTING.md", "LICENSE",
    "README.md", "SECURITY.md", "pyproject.toml",
)


def archive(path, entries):
    with ZipFile(path, "w") as output:
        for name, data in sorted(entries):
            entry = ZipInfo(name, date_time=(2026, 11, 27, 0, 0, 0))
            entry.compress_type = ZIP_STORED
            entry.create_system = 3
            entry.external_attr = 0o100644 << 16
            output.writestr(entry, data)


def source_entries():
    for name in SOURCE_FILES:
        yield name, (ROOT / name).read_bytes()
    for folder in SOURCE_DIRS:
        for path in (ROOT / folder).rglob("*"):
            relative = path.relative_to(ROOT)
            if path.is_file() and "__pycache__" not in relative.parts and path.suffix != ".pyc":
                # Git's native checkout may use CRLF on Windows.
                yield relative.as_posix(), path.read_bytes().replace(b"\r\n", b"\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    name = f"rowreceipt-{__version__}"
    source = [(path, data.replace(b"\r\n", b"\n")) for path, data in source_entries()]
    app = [(path, data) for path, data in source if path.startswith("rowreceipt/") or path == "LICENSE"]
    app.append(("__main__.py", b"from rowreceipt.cli import main\nraise SystemExit(main())\n"))
    archive(args.out / f"{name}.pyz", app)
    archive(args.out / f"{name}-source.zip", [(f"{name}/{path}", data) for path, data in source])
    artifacts = sorted(args.out.glob(f"{name}*"))
    checksums = [
        f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n"
        for path in artifacts if path.is_file() and path.suffix in {".pyz", ".zip", ".whl"}
    ]
    (args.out / "SHA256SUMS").write_bytes("".join(checksums).encode("ascii"))


if __name__ == "__main__":
    main()
