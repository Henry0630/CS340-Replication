# Dataset parsing and table mapping

## Source and commands

The upstream workbook is [bug table.xlsx](https://github.com/system-pclub/go-concurrency-bugs/blob/f2655063a2278cff64a51121b73801eda05fdcfa/bug%20table.xlsx),
pinned to commit `f2655063a2278cff64a51121b73801eda05fdcfa`.
Its SHA-256 is `a0e5f0103600b3c394b86cb975f403789366f0190312019fae648de0cd8e3235`.
The local copy is `data/bug_table.xlsx` and is stored without modification.

Run from the repository root with Python 3.8 or later; no third-party packages,
Go installation, or Docker container are required:

```sh
python scripts/fetch_dataset.py
python scripts/fetch_dataset.py --check
python scripts/parse_dataset.py
python -m unittest discover -s tests -v
```

The first three commands are also exposed as `make setup`, `make check`, and
`make tables`. Default paths are relative to the scripts' repository, not the
current working directory. Optional `--output` on the fetcher and `--input` /
`--output-dir` on the parser allow explicit paths.

The fetcher verifies an existing file without network access. It never silently
replaces a mismatched existing file. A new download is installed only after its
checksum passes. `--check` never downloads. The parser verifies the same checksum
and runs offline. Errors return exit code 1; expected paper/data differences are
reported with a successful exit code because they are research findings.

## Record selection and provenance

The workbook includes 171 bug entries, but only 169 contain 40-character commit
hashes. Following the repository's stated baseline, the pipeline includes those
83 blocking and 86 non-blocking records. It excludes these issue-only entries:

| Sheet | Row | Column B value | Reason |
|---|---:|---|---|
| blocking | 90 | boltdb#392 | Issue ID in place of a commit hash; no matching released patch |
| blocking | 92 | boltdb#240 | Issue ID in place of a commit hash; no matching released patch |

These entries remain in the original workbook and are reported by the parser.
Headers, blank separators, cached summary formulas, and application subtotals
are not bug records. Unknown malformed commit records cause an error.

`bug_inventory.csv` keeps the source worksheet and Excel row number, project,
repository, dataset commit, BugID, labels, upstream pin, and a pinned patch URL.
Its stable key is behavior + application + commit, not BugID: an issue can have
more than one patch. Project capitalization is normalized to the paper's names.

`dataset_commit` identifies the upstream dataset's commit, generally a fixing
commit. It is not a verified buggy revision. Role C must inspect the patch and
repository history before choosing the revision to reproduce.

## Worksheet fields

| Inventory field | blocking column | non-blocking column |
|---|---|---|
| dataset_commit | B | B |
| bug_id | C | C |
| reproduced_flag | D | D |
| app | E | E |
| shared_memory_flag | V | Q |
| message_passing_flag | W | R |
| patch_size_lines | BD | BC |

Blank, zero, and one reproduction flags stay distinct. Blank category labels
contribute zero when aggregating. Patch size is the authors' recorded value,
not a new count of all added/deleted diff lines (which may include tests).
Neither missing BugIDs nor reproduction flags are guessed.

## Table definitions

Reference values are transcribed from Tables 5, 6, 7, 9, and 10 of the
[paper](https://songlh.github.io/paper/go-study.pdf). Reference matrices are used
only to print comparisons; generated CSVs contain independently computed counts.
Every table includes a `Total` row and is compared cell by cell, including totals.

| CSV | Row grouping | Columns and calculation |
|---|---|---|
| table5.csv | Application | Blocking/non-blocking record counts; sums of shared/message flags |
| table6.csv | Application, blocking only | Mutex=N; RWMutex=Q; Wait=O+P; Chan=R; ChanWith=S; MessagingLib=T |
| table7.csv | Blocking cause | Add=Y; Move=Z; Change=AA; Remove=AB; Misc=AC |
| table9.csv | Application, non-blocking only | Traditional=J; Anonymous=L; WaitGroup=K; SharedLib=M; Chan=N; MessagingLib=O |
| table10.csv | Non-blocking cause | Add=V; Move=W; InstructionBypass=X; DataPrivate=Y; Misc=Z |

Table 7 uses the same cause mapping as Table 6. Table 10 uses the same cause
mapping as Table 9. Each cause/fix cell sums `cause_label * fix_label` across
records. `Total` sums the displayed category rows, so a multi-labeled record can
contribute more than once. Totals are category counts, not deduplicated bug counts.
The Table 6 Wait category is explicitly `wait related` (O) plus `WaitGroup` (P).

## Observed deviations and checks

- Table 5 totals: 83 blocking, 86 non-blocking, 105 shared-memory labels, and
  65 message-passing labels, versus 85 / 86 / 105 / 66 in the paper.
- The missing commit-backed BoltDB records reduce the blocking count by two.
  `blocking!35`, `kubernetes#11298`, has both shared/message labels and both
  Wait/ChanWith causes. All these original labels are retained and warned about.
- Consequently, Table 6 has Wait=4 versus 3 in the paper, Mutex=27 versus 28,
  and ChanWith=15 versus 16. Table 7 has Wait/Remove=2 versus 1,
  ChanWith/Remove=3 versus 4, and Mutex/Misc=1 versus 2. Its Remove total is 21
  category assignments even though only 20 included blocking records have that
  fix label; the overlapping cause labels explain the difference.
- All 42 cells in Table 9 and all 35 cells in Table 10 match the paper,
  including their total rows.
- Included records have 19 blocking and 23 non-blocking reproduction flags of
  one, versus 21 / 20 reproduced experiments in the paper. The two excluded
  issue-only blocking rows are also marked one; including them makes the
  workbook's blocking flag count 21. The non-blocking discrepancy remains.
- Screening included blocking records for `reproduced_flag=1` and
  `patch_size_lines<=10` yields 14 entries: Docker=3, etcd=6, gRPC=5.
  Their symptoms and suitability for timeout-based detection still require
  manual inspection; the script does not claim they have been reproduced here.

The parser checks header positions, binary labels, duplicate worksheet/commit
keys, patch sizes, and expected row counts. Tests also cover corrupt or missing
files, failed downloads, blank flags, overlapping labels, sparse XML cells,
shared/inline strings, stable CSV bytes, and execution outside the repository.
