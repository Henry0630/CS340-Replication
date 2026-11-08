#!/usr/bin/env python3
"""Fetch or verify the pinned upstream workbook using only the standard library.

Run without arguments to download a missing workbook. Use --check for an
offline integrity check; neither mode silently replaces an existing file.
"""

import argparse
import hashlib
import os
from pathlib import Path
import sys
import tempfile
from urllib.error import URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = ROOT / "data" / "bug_table.xlsx"
UPSTREAM_COMMIT = "f2655063a2278cff64a51121b73801eda05fdcfa"
EXPECTED_SHA256 = "a0e5f0103600b3c394b86cb975f403789366f0190312019fae648de0cd8e3235"
DATASET_URL = (
    "https://raw.githubusercontent.com/system-pclub/go-concurrency-bugs/"
    + UPSTREAM_COMMIT + "/bug%20table.xlsx"
)


def verify_dataset(path):
    """Reject missing, incomplete, or changed data before it enters the pipeline."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            digest.update(chunk)
    actual = digest.hexdigest()
    if actual != EXPECTED_SHA256:
        raise ValueError(
            "Dataset SHA-256 mismatch: expected {}, got {}. "
            "The existing file was not replaced.".format(EXPECTED_SHA256, actual)
        )
    return actual


def fetch_dataset(path=DATASET_PATH, check_only=False):
    """Verify an existing file or atomically install a verified download."""
    path = Path(path)
    if path.exists():
        verify_dataset(path)
        return "verified"
    if check_only:
        raise FileNotFoundError(
            "Dataset is missing: {}. Run scripts/fetch_dataset.py first.".format(path)
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        # Keep the temporary file on the destination filesystem for atomic rename.
        with tempfile.NamedTemporaryFile(
            dir=str(path.parent), prefix=".bug_table-", suffix=".tmp", delete=False
        ) as output:
            temporary = Path(output.name)
            request = Request(DATASET_URL, headers={"User-Agent": "CS340-Replication/1.0"})
            with urlopen(request, timeout=30) as response:
                while True:
                    chunk = response.read(65536)
                    if not chunk:
                        break
                    output.write(chunk)
        verify_dataset(temporary)
        os.replace(str(temporary), str(path))
        return "downloaded and verified"
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify locally without downloading")
    parser.add_argument("--output", type=Path, default=DATASET_PATH, help="workbook destination")
    args = parser.parse_args(argv)
    try:
        status = fetch_dataset(args.output, check_only=args.check)
    except ValueError as error:
        print("error: {}".format(error), file=sys.stderr)
        return 1
    except URLError as error:
        code = getattr(error, "code", None) or getattr(error.reason, "errno", "unknown")
        print("error: Download failed (code {}). Check network access to raw.githubusercontent.com.".format(code), file=sys.stderr)
        return 1
    except OSError as error:
        print("error: Cannot access the dataset (code {}). Check the path and permissions; "
              "run scripts/fetch_dataset.py without --check if the file is missing.".format(error.errno), file=sys.stderr)
        return 1
    print("Dataset {}: {}".format(status, args.output))
    print("Upstream commit: {}".format(UPSTREAM_COMMIT))
    print("SHA-256: {}".format(EXPECTED_SHA256))
    return 0


if __name__ == "__main__":
    sys.exit(main())
