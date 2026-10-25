"""Download and preserve the original UCI archive and provenance."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen
from zipfile import ZipFile


def main():
    raw = Path(__file__).resolve().parents[1] / "data" / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    url = "https://archive.ics.uci.edu/static/public/275/bike+sharing+dataset.zip"
    archive = raw / "bike-sharing.zip"
    if not archive.exists():
        with urlopen(url, timeout=60) as response:
            archive.write_bytes(response.read())
    with ZipFile(archive) as source:
        for name in ("hour.csv", "day.csv", "Readme.txt"):
            matches = [item for item in source.namelist() if Path(item).name == name]
            if len(matches) != 1:
                raise ValueError(f"Expected one archive member named {name}")
            (raw / name).write_bytes(source.read(matches[0]))
    provenance = raw / "provenance.json"
    if not provenance.exists():
        provenance.write_text(json.dumps({
            "download_url": url,
            "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
            "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
            "dataset_doi": "10.24432/C5W894",
            "attribution": "Fanaee-T, Hadi. Bike Sharing. UCI Machine Learning Repository.",
            "license": "CC BY 4.0",
        }, indent=2) + "\n", encoding="utf-8")
    print(f"Dataset available at {raw}")


if __name__ == "__main__":
    main()
