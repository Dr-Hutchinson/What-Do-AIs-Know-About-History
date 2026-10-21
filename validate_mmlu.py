"""Compare local history data with an independently downloaded canonical archive."""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import tarfile

from history import DATA, dataset_version, questions


def validate(archive):
    manifest = json.loads((DATA / "manifest.json").read_text())
    archive_hash = hashlib.sha256(archive.read_bytes()).hexdigest()
    if archive_hash != manifest["archive_sha256"]:
        raise ValueError("Archive differs from recorded source; review upstream changes before comparison")
    total = 0
    with tarfile.open(archive) as handle:
        for name, entry in manifest["files"].items():
            members = [m for m in handle.getmembers() if m.isfile() and m.name.endswith("/" + name)]
            if len(members) != 1:
                raise ValueError(f"Expected exactly one upstream file: {name}")
            raw = handle.extractfile(members[0]).read()
            if raw != (DATA / name).read_bytes():
                raise ValueError(f"Local file differs from upstream: {name}")
            rows = list(csv.reader(io.StringIO(raw.decode("utf-8"))))
            subject, split = name.removesuffix(".csv").rsplit("_", 1)
            loaded = questions(subject, split)
            if len(rows) != entry["rows"] or len(loaded) != len(rows):
                raise ValueError(f"Row-count mismatch: {name}")
            for number, (row, question) in enumerate(zip(rows, loaded), 1):
                if ([question["question"], *question["options"], question["answer"]] != row
                        or question["id"] != f"{subject}:{split}:{number:03}"):
                    raise ValueError(f"Loader alignment mismatch: {name}:{number}")
            total += len(rows)
            print(f"MATCH {name}: {len(rows)} rows; bytes, fields, order, IDs")
    print(f"Validated {total} rows. Dataset version: {dataset_version()}")
    print("Source fidelity does not establish historical correctness of the source items.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    validate(parser.parse_args().archive)
