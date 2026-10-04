import argparse
import hashlib
import json
import shutil
import tempfile
import urllib.request
import zipfile
from datetime import UTC, datetime
from pathlib import Path

SOURCE_URL = (
    "https://phm-datasets.s3.amazonaws.com/NASA/"
    "6.+Turbofan+Engine+Degradation+Simulation+Data+Set.zip"
)
OUTER_MEMBER = "6. Turbofan Engine Degradation Simulation Data Set/CMAPSSData.zip"
REQUIRED = {"train_FD001.txt", "test_FD001.txt", "RUL_FD001.txt", "readme.txt"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch NASA C-MAPSS FD001 source files.")
    parser.add_argument("--destination", type=Path, default=Path("data/raw/cmapss"))
    args = parser.parse_args()
    destination: Path = args.destination
    destination.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="cmapss-") as temporary:
        archive = Path(temporary) / "source.zip"
        request = urllib.request.Request(SOURCE_URL, headers={"User-Agent": "PS26249/0.1"})
        with urllib.request.urlopen(request, timeout=120) as response, archive.open("wb") as target:
            shutil.copyfileobj(response, target)
        archive_hash = sha256(archive)
        with zipfile.ZipFile(archive) as outer:
            if OUTER_MEMBER not in outer.namelist():
                raise RuntimeError("NASA archive is missing its documented CMAPSSData.zip member.")
            nested_archive = Path(temporary) / "CMAPSSData.zip"
            with outer.open(OUTER_MEMBER) as source, nested_archive.open("wb") as target:
                shutil.copyfileobj(source, target)
        nested_hash = sha256(nested_archive)
        with zipfile.ZipFile(nested_archive) as bundle:
            members = set(bundle.namelist())
            missing = REQUIRED - members
            if missing:
                raise RuntimeError(
                    f"NASA archive is missing required FD001 files: {sorted(missing)}"
                )
            file_hashes: dict[str, str] = {}
            for member in sorted(REQUIRED):
                output = destination / member
                with bundle.open(member) as source, output.open("wb") as target:
                    shutil.copyfileobj(source, target)
                file_hashes[output.name] = sha256(output)

    manifest = {
        "dataset": "NASA C-MAPSS",
        "subset": "FD001",
        "simulated": True,
        "source_url": SOURCE_URL,
        "acquired_at": datetime.now(UTC).isoformat(),
        "archive_sha256": archive_hash,
        "nested_archive_sha256": nested_hash,
        "files": file_hashes,
        "license_note": "NASA portal lists the dataset license as not specified.",
    }
    (destination / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
