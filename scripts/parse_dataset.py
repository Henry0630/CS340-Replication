#!/usr/bin/env python3
"""Recompute Tables 5/6/7/9/10 and a traceable bug inventory, offline.

Only Python's standard library is required. The pinned workbook is verified
before parsing. Raw labels are retained, including known overlapping labels;
published numbers are used for comparison only, never to adjust our results.
"""

import argparse
from collections import Counter
import csv
from dataclasses import dataclass
import os
from pathlib import Path
import posixpath
import re
import sys
import tempfile
import xml.etree.ElementTree as ET
from zipfile import BadZipFile, ZipFile

from fetch_dataset import DATASET_PATH, ROOT, UPSTREAM_COMMIT, verify_dataset


NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
APPS = ("Docker", "Kubernetes", "etcd", "CockroachDB", "gRPC", "BoltDB")
APP_NAMES = {name.lower(): name for name in APPS}
REPOSITORIES = dict(zip(APPS, (
    "moby/moby", "kubernetes/kubernetes", "etcd-io/etcd",
    "cockroachdb/cockroach", "grpc/grpc-go", "boltdb/bolt",
)))
PATCH_DIRS = dict(zip(APPS, ("docker", "kubernetes", "etcd", "cockroachdb", "grpc-go", "boltdb")))

# Column letters are deliberate: the two worksheets have different layouts.
# Header checks below prevent silent column drift. See docs/table_mapping.md.
CAUSES = {
    "blocking": {
        "Mutex": ("N",), "RWMutex": ("Q",), "Wait": ("O", "P"),
        "Chan": ("R",), "ChanWith": ("S",), "MessagingLib": ("T",),
    },
    "non-blocking": {
        "Traditional": ("J",), "Anonymous": ("L",), "WaitGroup": ("K",),
        "SharedLib": ("M",), "Chan": ("N",), "MessagingLib": ("O",),
    },
}
FIXES = {
    "blocking": {"Add": "Y", "Move": "Z", "Change": "AA", "Remove": "AB", "Misc": "AC"},
    "non-blocking": {"Add": "V", "Move": "W", "InstructionBypass": "X", "DataPrivate": "Y", "Misc": "Z"},
}
HEADERS = {
    "blocking": {
        "N": "lock related", "O": "wait related", "P": "WaitGroup", "Q": "rwlock",
        "R": "channel related", "S": "mixing lock/wait & channel", "T": "messaging lib",
        "V": "shared", "W": "message", "Y": "Syn Add", "Z": "Syn Move",
        "AA": "Syn Change", "AB": "Syn Remove", "AC": "Misc", "BD": "patch size",
    },
    "non-blocking": {
        "J": "traditional bug", "K": "misusing waitgroup", "L": "anonymous funcion",
        "M": "race@lib", "N": "misusing channel", "O": "misusing messaging lib",
        "Q": "shared", "R": "message", "V": "Add-t", "W": "Move-t",
        "X": "eliminate or bypass Insruction", "Y": "data private", "Z": "Misc.", "BC": "patch-size",
    },
}
COMMON_HEADERS = {"B": "commit hash", "C": "BugID", "D": "Reproduced?", "E": "application"}
MISSING_COMMITS = {("blocking", "boltdb#392"), ("blocking", "boltdb#240")}

# Transcribed reference counts from https://songlh.github.io/paper/go-study.pdf.
# Each matrix follows the row and column orders used in build_tables().
PAPER = {
    5: [[21, 23, 28, 16], [17, 17, 20, 14], [21, 16, 18, 19],
        [12, 16, 23, 5], [11, 12, 12, 11], [3, 2, 4, 1]],
    6: [[9, 0, 3, 5, 2, 2], [6, 2, 0, 3, 6, 0], [5, 0, 0, 10, 5, 1],
        [4, 3, 0, 5, 0, 0], [2, 0, 0, 6, 2, 1], [2, 0, 0, 0, 1, 0]],
    7: [[9, 7, 2, 8, 2], [0, 1, 0, 1, 1], [0, 2, 0, 3, 0],
        [15, 1, 5, 4, 4], [6, 3, 2, 4, 1], [1, 0, 0, 1, 2]],
    9: [[9, 6, 0, 1, 6, 1], [8, 3, 1, 0, 5, 0], [9, 0, 2, 2, 3, 0],
        [10, 1, 3, 2, 0, 0], [8, 1, 0, 1, 2, 0], [2, 0, 0, 0, 0, 0]],
    10: [[27, 4, 5, 10, 0], [3, 2, 1, 0, 0], [5, 2, 0, 4, 0],
         [1, 2, 1, 0, 2], [6, 7, 3, 0, 0], [0, 0, 0, 0, 1]],
}
TITLES = {5: "Taxonomy", 6: "Blocking bug causes", 7: "Blocking bug fixes",
          9: "Non-blocking bug causes", 10: "Non-blocking bug fixes"}


def read_sheets(path):
    """Read XLSX relationships, shared strings, and sparse cell coordinates."""
    sheets = {}
    with ZipFile(path) as archive:
        strings = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            strings = ["".join(t.text or "" for t in item.findall(".//s:t", NS))
                       for item in root.findall("s:si", NS)]
        relationships = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        targets = {item.attrib["Id"]: item.attrib["Target"] for item in relationships
                   if item.get("TargetMode") != "External"}
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        for sheet in workbook.findall("s:sheets/s:sheet", NS):
            name = sheet.attrib["name"]
            if name not in CAUSES:
                continue
            target = targets[sheet.attrib["{" + REL_NS + "}id"]]
            member = (target.lstrip("/") if target.startswith("/")
                      else posixpath.normpath(posixpath.join("xl", target)))
            rows = []
            root = ET.fromstring(archive.read(member))
            for row in root.findall("s:sheetData/s:row", NS):
                cells = {}
                for cell in row.findall("s:c", NS):
                    coordinate = re.fullmatch(r"([A-Z]+)[1-9][0-9]*", cell.attrib["r"])
                    if coordinate is None:
                        raise ValueError("Invalid cell coordinate: " + cell.attrib["r"])
                    value = cell.findtext("s:v", default="", namespaces=NS)
                    if cell.get("t") == "s":
                        value = strings[int(value)]
                    elif cell.get("t") == "inlineStr":
                        value = "".join(t.text or "" for t in cell.findall(".//s:t", NS))
                    elif cell.get("t") == "e":
                        raise ValueError("Excel error at {}!{}: {}".format(name, cell.attrib["r"], value))
                    if cell.find("s:f", NS) is not None and not value:
                        raise ValueError("Formula has no cached value: {}!{}".format(name, cell.attrib["r"]))
                    cells[coordinate.group(1)] = value.strip()
                rows.append((int(row.attrib["r"]), cells))
            sheets[name] = rows
    return sheets


@dataclass
class Bug:
    behavior: str
    source_row: int
    cells: dict
    app: str

    def flag(self, column):
        """Blank category cells mean no label; the original cells remain intact."""
        value = self.cells.get(column, "")
        if value not in ("", "0", "1"):
            raise ValueError("Invalid binary label at {}!{}{}: {!r}".format(
                self.behavior, column, self.source_row, value))
        return int(value or "0")

    def cause(self, label):
        # Wait is explicitly O + P, not just the WaitGroup column.
        return sum(self.flag(col) for col in CAUSES[self.behavior][label])

    def shared(self):
        return self.flag("V" if self.behavior == "blocking" else "Q")

    def message(self):
        return self.flag("W" if self.behavior == "blocking" else "R")


def parse_bugs(sheets):
    """Validate the schema and keep one record per worksheet/commit pair."""
    bugs, seen = [], set()
    for behavior in CAUSES:
        if behavior not in sheets:
            raise ValueError("Missing worksheet: " + behavior)
        headers = dict(sheets[behavior]).get(1, {})
        expected = dict(COMMON_HEADERS, **HEADERS[behavior])
        for column, label in expected.items():
            if headers.get(column) != label:
                raise ValueError("Unexpected header at {}!{}1: expected {!r}, got {!r}".format(
                    behavior, column, label, headers.get(column)))
        for row_number, cells in sheets[behavior]:
            commit = cells.get("B", "")
            # Formatting, headers, and summary/formula rows are not bug records.
            if not re.fullmatch(r"[0-9a-fA-F]{40}", commit):
                # These two upstream rows contain issue IDs instead of commits.
                # The repository requires a 169-record commit-backed inventory.
                if ((behavior, commit) in MISSING_COMMITS
                        and cells.get("E", "").lower() == "boltdb"
                        and cells.get("C") == commit):
                    continue
                if cells.get("A", "").isdigit():
                    raise ValueError("Missing or invalid commit at {}!B{}".format(behavior, row_number))
                continue
            key = (behavior, commit.lower())
            if key in seen:
                raise ValueError("Duplicate worksheet/commit record: {} {}".format(*key))
            seen.add(key)
            app = APP_NAMES.get(cells.get("E", "").lower())
            if app is None:
                raise ValueError("Unknown application at {}!E{}".format(behavior, row_number))
            bug = Bug(behavior, row_number, cells, app)
            bug.flag("D")
            bug.shared()
            bug.message()
            for label in CAUSES[behavior]:
                bug.cause(label)
            for column in FIXES[behavior].values():
                bug.flag(column)
            patch = cells.get("BD" if behavior == "blocking" else "BC", "")
            if not patch.isdigit():
                raise ValueError("Invalid patch size at {} row {}".format(behavior, row_number))
            bugs.append(bug)
    counts = Counter(bug.behavior for bug in bugs)
    if counts != {"blocking": 83, "non-blocking": 86}:
        raise ValueError("Unexpected pinned dataset row counts: {}".format(dict(counts)))
    return bugs


def with_total(matrix):
    """Totals sum category counts; multi-labeled records can count twice."""
    return matrix + [[sum(column) for column in zip(*matrix)]]


def build_tables(bugs):
    """Aggregate raw labels without consulting the paper reference counts."""
    tables = {}
    taxonomy = [[sum(b.app == app and b.behavior == "blocking" for b in bugs),
                 sum(b.app == app and b.behavior == "non-blocking" for b in bugs),
                 sum(b.shared() for b in bugs if b.app == app),
                 sum(b.message() for b in bugs if b.app == app)] for app in APPS]
    tables[5] = ("app", list(APPS), ["Blocking", "NonBlocking", "SharedMemory", "MessagePassing"], taxonomy)
    for number, behavior in ((6, "blocking"), (9, "non-blocking")):
        columns = list(CAUSES[behavior])
        matrix = [[sum(b.cause(c) for b in bugs if b.behavior == behavior and b.app == app)
                   for c in columns] for app in APPS]
        tables[number] = ("app", list(APPS), columns, matrix)
    cause_order = {
        "blocking": ["Mutex", "Wait", "RWMutex", "Chan", "ChanWith", "MessagingLib"],
        "non-blocking": ["Traditional", "WaitGroup", "Anonymous", "SharedLib", "Chan", "MessagingLib"],
    }
    for number, behavior in ((7, "blocking"), (10, "non-blocking")):
        rows = cause_order[behavior]
        columns = list(FIXES[behavior])
        matrix = [[sum(b.cause(cause) * b.flag(FIXES[behavior][fix])
                       for b in bugs if b.behavior == behavior) for fix in columns] for cause in rows]
        tables[number] = ("cause", rows, columns, matrix)
    return tables


def inventory_row(bug):
    """Keep dataset commits distinct from unverified buggy revisions."""
    cells = bug.cells
    commit = cells["B"].lower()
    patch_directory = "blocking-bugs" if bug.behavior == "blocking" else "non-blocking-bugs"
    return {
        "bug_key": "{}:{}:{}".format(bug.behavior, bug.app, commit),
        "app": bug.app, "repository": REPOSITORIES[bug.app], "behavior": bug.behavior,
        "dataset_commit": commit, "bug_id": cells.get("C", ""),
        "reproduced_flag": cells.get("D", ""),
        "patch_size_lines": int(cells["BD" if bug.behavior == "blocking" else "BC"]),
        "shared_memory_flag": cells.get("V" if bug.behavior == "blocking" else "Q", ""),
        "message_passing_flag": cells.get("W" if bug.behavior == "blocking" else "R", ""),
        "cause_labels": ";".join(c for c in CAUSES[bug.behavior] if bug.cause(c)),
        "fix_labels": ";".join(f for f, col in FIXES[bug.behavior].items() if bug.flag(col)),
        "wait_related_flag": cells.get("O", "") if bug.behavior == "blocking" else "",
        "waitgroup_flag": cells.get("P", "") if bug.behavior == "blocking" else "",
        "source_sheet": bug.behavior, "source_row": bug.source_row,
        "upstream_commit": UPSTREAM_COMMIT,
        "patch_url": "https://github.com/system-pclub/go-concurrency-bugs/blob/{}/{}/{}/{}.txt".format(
            UPSTREAM_COMMIT, patch_directory, PATCH_DIRS[bug.app], commit),
    }


def write_csv(path, fieldnames, rows):
    """Use UTF-8 and LF for deterministic CSVs on Windows and Linux."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="",
                                         dir=str(path.parent), suffix=".tmp", delete=False) as stream:
            temporary = Path(stream.name)
            writer = csv.writer(stream, lineterminator="\n")
            writer.writerow(fieldnames)
            writer.writerows(rows)
        os.replace(str(temporary), str(path))
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def print_table(number, table):
    key, labels, columns, matrix = table
    values, reference = with_total(matrix), with_total(PAPER[number])
    print("\n== Table {}  {}".format(number, TITLES[number]))
    print("  {:<16} {}".format(key, " ".join("{:>14}".format(c) for c in columns)))
    for label, row in zip(labels + ["Total"], values):
        print("  {:<16} {}".format(label, " ".join("{:>14}".format(v) for v in row)))
    print("  {:<16} {}".format("paper", " ".join("{:>14}".format(v) for v in reference[-1])))
    print("  {:<16} {}".format("delta", " ".join("{:>14}".format(a - b) for a, b in zip(values[-1], reference[-1]))))
    differences = []
    for label, ours, paper in zip(labels + ["Total"], values, reference):
        for column, actual, expected in zip(columns, ours, paper):
            if actual != expected:
                differences.append("{}/{}: paper={} ours={} delta={:+d}".format(
                    label, column, expected, actual, actual - expected))
    if differences:
        print("  Differences (raw labels retained):")
        for difference in differences:
            print("    " + difference)
    else:
        print("  All {} cells match the paper (including totals).".format(len(values) * len(columns)))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DATASET_PATH, help="pinned workbook to read")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results" / "tables", help="CSV destination")
    args = parser.parse_args(argv)
    try:
        verify_dataset(args.input)
        bugs = parse_bugs(read_sheets(args.input))
        tables = build_tables(bugs)
        print("rows parsed: blocking=83 non-blocking=86 total={}".format(len(bugs)))
        for number in (5, 6, 7, 9, 10):
            key, labels, columns, matrix = tables[number]
            rows = [[label] + values for label, values in zip(labels + ["Total"], with_total(matrix))]
            write_csv(args.output_dir / "table{}.csv".format(number), [key] + columns, rows)
            print_table(number, tables[number])
        inventory = [inventory_row(bug) for bug in bugs]
        fields = list(inventory[0])
        write_csv(args.output_dir / "bug_inventory.csv", fields,
                  [[row[field] for field in fields] for row in inventory])
        print("\n== Label sanity checks")
        print("Excluded issue-only rows: blocking!90 boltdb#392; blocking!92 boltdb#240. "
              "Neither has a commit hash in column B; the source workbook is unchanged.")
        warnings = 0
        for bug in bugs:
            cause_count = sum(bug.cause(c) for c in CAUSES[bug.behavior])
            fix_count = sum(bug.flag(c) for c in FIXES[bug.behavior].values())
            if bug.shared() + bug.message() != 1 or cause_count != 1 or fix_count != 1:
                warnings += 1
                print("WARNING: {}!row {} {}: shared={} message={} causes={} fixes={}; labels preserved.".format(
                    bug.behavior, bug.source_row, bug.cells.get("C") or bug.cells["B"],
                    bug.shared(), bug.message(), cause_count, fix_count))
        print("{} label warning(s); differences are not data corrections.".format(warnings))
        print("Reproduced flags in commit-backed inventory: blocking={} non-blocking={} (paper: 21 / 20).".format(
            *(sum(b.behavior == behavior and b.cells.get("D") == "1" for b in bugs) for behavior in CAUSES)))
        print("Wrote 5 tables and {} inventory rows to {}".format(len(inventory), args.output_dir))
        return 0
    except OSError as error:
        print("error: Cannot read the input or write the output (code {}). Check paths and permissions; "
              "run scripts/fetch_dataset.py first if the dataset is missing.".format(error.errno), file=sys.stderr)
        return 1
    except (ValueError, BadZipFile, ET.ParseError, KeyError, IndexError) as error:
        print("error: {}".format(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
