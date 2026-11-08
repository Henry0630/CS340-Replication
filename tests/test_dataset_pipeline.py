"""Regression checks for data integrity, counting rules, and command-line use.

Run `python scripts/fetch_dataset.py` once, then
`python -m unittest discover -s tests -v`. Tests never require network access.
"""

import contextlib
import copy
import csv
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import URLError
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import fetch_dataset as fetch
import parse_dataset as parse


class DatasetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fetch.verify_dataset(fetch.DATASET_PATH)
        cls.payload = fetch.DATASET_PATH.read_bytes()
        cls.sheets = parse.read_sheets(fetch.DATASET_PATH)
        cls.bugs = parse.parse_bugs(cls.sheets)

    def test_verified_download_and_offline_reuse(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "data" / "bug_table.xlsx"
            with patch.object(fetch, "urlopen", return_value=io.BytesIO(self.payload)) as download:
                self.assertEqual(fetch.fetch_dataset(target), "downloaded and verified")
                download.assert_called_once()
            with patch.object(fetch, "urlopen", side_effect=AssertionError("Network was used")):
                self.assertEqual(fetch.fetch_dataset(target), "verified")
                self.assertEqual(fetch.fetch_dataset(target, check_only=True), "verified")
            self.assertEqual(target.read_bytes(), self.payload)
            self.assertEqual(list(target.parent.iterdir()), [target])

    def test_check_missing_does_not_download_or_create_directories(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "missing" / "bug_table.xlsx"
            with patch.object(fetch, "urlopen", side_effect=AssertionError("Network was used")):
                with self.assertRaises(FileNotFoundError):
                    fetch.fetch_dataset(target, check_only=True)
            self.assertFalse(target.parent.exists())

    def test_existing_corruption_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "bug_table.xlsx"
            target.write_bytes(b"corrupt existing file")
            with patch.object(fetch, "urlopen", side_effect=AssertionError("Network was used")):
                with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                    fetch.fetch_dataset(target)
            self.assertEqual(target.read_bytes(), b"corrupt existing file")

    def test_failed_downloads_leave_no_partial_workbook(self):
        for failure in ("network", "checksum"):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as folder:
                target = Path(folder) / "bug_table.xlsx"
                options = ({"side_effect": URLError("unavailable")} if failure == "network"
                           else {"return_value": io.BytesIO(b"incomplete workbook")})
                with patch.object(fetch, "urlopen", **options):
                    with self.assertRaises((URLError, ValueError)):
                        fetch.fetch_dataset(target)
                self.assertEqual(list(Path(folder).iterdir()), [])

    def test_inventory_counts_blank_flags_and_candidate_pool(self):
        rows = [parse.inventory_row(b) for b in self.bugs]
        self.assertEqual(len(rows), 169)
        self.assertEqual(sum(r["behavior"] == "blocking" for r in rows), 83)
        self.assertEqual(sum(r["behavior"] == "non-blocking" for r in rows), 86)
        self.assertEqual(sum(r["reproduced_flag"] == "" for r in rows), 89)
        self.assertEqual(sum(r["reproduced_flag"] == "0" for r in rows), 38)
        self.assertEqual(sum(r["reproduced_flag"] == "1" for r in rows), 42)
        candidates = [r for r in rows if r["behavior"] == "blocking"
                      and r["reproduced_flag"] == "1" and r["patch_size_lines"] <= 10]
        self.assertEqual(len(candidates), 14)
        self.assertEqual({r["app"] for r in candidates}, {"Docker", "etcd", "gRPC"})
        self.assertEqual(len({r["bug_key"] for r in rows}), 169)
        self.assertTrue(all(len(r["dataset_commit"]) == 40 for r in rows))
        self.assertFalse(any(r["bug_id"] in ("boltdb#392", "boltdb#240") for r in rows))
        # The same issue can have multiple patches; it must not be deduplicated.
        self.assertEqual(sum(r["bug_id"] == "Moby#21311" for r in rows), 2)

    def test_multi_label_record_is_retained_and_explains_wait_difference(self):
        bug = next(b for b in self.bugs if b.cells.get("C") == "kubernetes#11298")
        self.assertEqual(bug.source_row, 35)
        self.assertEqual((bug.shared(), bug.message(), bug.cause("Wait"), bug.cause("ChanWith")), (1, 1, 1, 1))
        tables = parse.build_tables(self.bugs)
        self.assertEqual(parse.with_total(tables[5][3])[-1], [83, 86, 105, 65])
        self.assertEqual(parse.with_total(tables[6][3])[-1], [27, 5, 4, 29, 15, 4])
        self.assertEqual(tables[7][3][1], [0, 1, 0, 2, 1])
        self.assertEqual(parse.with_total(tables[7][3])[-1], [31, 14, 9, 21, 9])

    def test_nonblocking_tables_match_independently_transcribed_paper_cells(self):
        tables = parse.build_tables(self.bugs)
        self.assertEqual(tables[9][3], [
            [9, 6, 0, 1, 6, 1], [8, 3, 1, 0, 5, 0], [9, 0, 2, 2, 3, 0],
            [10, 1, 3, 2, 0, 0], [8, 1, 0, 1, 2, 0], [2, 0, 0, 0, 0, 0],
        ])
        self.assertEqual(tables[10][3], [
            [27, 4, 5, 10, 0], [3, 2, 1, 0, 0], [5, 2, 0, 4, 0],
            [1, 2, 1, 0, 2], [6, 7, 3, 0, 0], [0, 0, 0, 0, 1],
        ])

    def test_paper_reference_does_not_control_computed_results(self):
        expected = parse.build_tables(self.bugs)
        with patch.dict(parse.PAPER, {5: [[0, 0, 0, 0]] * 6}):
            self.assertEqual(parse.build_tables(self.bugs), expected)

    def test_header_drift_invalid_flags_and_duplicate_commits_fail(self):
        for failure in ("header", "flag", "duplicate", "commit"):
            with self.subTest(failure=failure):
                sheets = copy.deepcopy(self.sheets)
                if failure == "header":
                    sheets["blocking"][0][1]["BD"] = "unexpected field"
                elif failure == "flag":
                    sheets["blocking"][2][1]["D"] = "2"
                elif failure == "duplicate":
                    sheets["blocking"].append(sheets["blocking"][2])
                else:
                    sheets["blocking"][2][1]["B"] = "not-a-commit"
                with self.assertRaises(ValueError):
                    parse.parse_bugs(sheets)

    def test_corrupt_input_fails_before_output_is_created(self):
        with tempfile.TemporaryDirectory() as folder:
            source, output = Path(folder) / "bad.xlsx", Path(folder) / "out"
            source.write_bytes(b"bad workbook")
            with contextlib.redirect_stderr(io.StringIO()) as errors:
                code = parse.main(["--input", str(source), "--output-dir", str(output)])
            self.assertEqual(code, 1)
            self.assertIn("SHA-256 mismatch", errors.getvalue())
            self.assertFalse(output.exists())

    def test_commands_work_outside_repository_and_generate_identical_csvs(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "tables"
            check = subprocess.run([sys.executable, str(ROOT / "scripts/fetch_dataset.py"), "--check"],
                                   cwd=folder, capture_output=True, text=True)
            self.assertEqual(check.returncode, 0, check.stderr)
            command = [sys.executable, str(ROOT / "scripts/parse_dataset.py"), "--output-dir", str(output)]
            first = subprocess.run(command, cwd=folder, capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            before = {f.name: f.read_bytes() for f in output.glob("*.csv")}
            second = subprocess.run(command, cwd=folder, capture_output=True, text=True)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(before, {f.name: f.read_bytes() for f in output.glob("*.csv")})
            self.assertEqual(set(before), {"table5.csv", "table6.csv", "table7.csv", "table9.csv",
                                           "table10.csv", "bug_inventory.csv"})
            self.assertTrue(all(b"\r" not in content for content in before.values()))
            self.assertTrue(all(content.isascii() for content in before.values()))
            inventory = list(csv.DictReader(io.StringIO(before["bug_inventory.csv"].decode("utf-8"))))
            self.assertEqual(len(inventory), 169)
            self.assertIn("kubernetes#11298", first.stdout)
            self.assertIn("boltdb#392", first.stdout)

    def test_xlsx_relationships_sparse_columns_and_rich_strings(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "sample.xlsx"
            with ZipFile(source, "w") as archive:
                archive.writestr("xl/workbook.xml", '''<workbook
                    xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
                    xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
                    <sheets><sheet name="blocking" r:id="rel42"/></sheets></workbook>''')
                archive.writestr("xl/_rels/workbook.xml.rels", '''<Relationships>
                    <Relationship Id="rel42" Target="/xl/worksheets/custom.xml"/>
                    </Relationships>''')
                archive.writestr("xl/sharedStrings.xml", '''<sst
                    xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
                    <si><r><t>commit </t></r><r><t>hash</t></r></si></sst>''')
                archive.writestr("xl/worksheets/custom.xml", '''<worksheet
                    xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
                    <sheetData><row r="1"><c r="B1" t="s"><v>0</v></c>
                    <c r="BD1" t="inlineStr"><is><t>patch size</t></is></c></row>
                    <row r="3"><c r="D3"><v>0</v></c><c r="BD3"><v>10</v></c></row>
                    </sheetData></worksheet>''')
            rows = dict(parse.read_sheets(source)["blocking"])
            self.assertEqual(rows[1], {"B": "commit hash", "BD": "patch size"})
            self.assertEqual(rows[3], {"D": "0", "BD": "10"})
            self.assertNotIn("C", rows[3])


if __name__ == "__main__":
    unittest.main()
