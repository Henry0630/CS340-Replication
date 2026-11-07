# CS340 — Replication of *Understanding Real-World Concurrency Bugs in Go* (ASPLOS'19)

Course project for **CS340 Operating Systems**, MUST, AY 2026–2027.
Group 5 (4 members). Target paper:

> Tengfei Tu, Xiaoyu Liu, Linhai Song, Yiying Zhang.
> *Understanding Real-World Concurrency Bugs in Go.* ASPLOS'19.
> <https://songlh.github.io/paper/go-study.pdf>

The paper is an **empirical study**, not a performance paper: it labels 171 real
concurrency bugs from six production Go programs along two axes (behaviour:
blocking / non-blocking; cause: shared memory / message passing), studies how
they were fixed, and then re-runs 41 of them against Go's built-in deadlock and
data-race detectors.

Our reproduction therefore has two layers:

| Layer | What we do | Maps to paper |
|---|---|---|
| **L1 — re-derive the statistics** | Parse the released dataset and recompute every table ourselves, then compare against the published numbers | Tables 5, 6, 7, 9, 10, 11 |
| **L2 — re-run the bugs** | Rebuild a subset of the buggy programs at their buggy commit, trigger the bug, and re-measure detector coverage | Tables 8, 12 (§5.3, §6.3) |

The extension (§ below) changes **one factor**: the Go language version, to test
whether Go 1.22's per-iteration loop-variable semantics eliminates the
"anonymous function" bug class the paper reports.

## Repository layout

```
data/            bug_table.xlsx (upstream dataset, pinned commit below)
docs/            claims, table mapping, environment, plan, team division
scripts/         parse_dataset.py, fetch_dataset.py, md2html.py
results/tables/  CSV output of the re-derived tables (committed)
results/raw/     raw run logs (not committed; see .gitignore)
repro/           one directory per reproduced bug (week 2+)
report/          main.tex + refs.bib

Shareable docs: `docs/team_division.md` is the 分工方案; regenerate the PDF with
`python scripts/md2html.py docs/team_division.md` then
`msedge --headless=new --print-to-pdf=... docs/team_division.html`.
```

## Setup

Requirements: `python3` (stdlib only — no pandas/openpyxl needed), `git`,
`curl`. For L2 (reproducing bugs and running the detectors) you need **Docker
with Linux containers**; the image, the pinned versions and the exact steps are
in `docs/env-setup.md`. Status: the image has **not been built yet on any
machine** — do not quote environment numbers in the report before
`docs/env-setup.md` §6 returns them.

```bash
make setup     # fetch the dataset snapshot if data/bug_table.xlsx is missing
make tables    # recompute every table and print paper-vs-ours comparison
```

No `make` on Windows (git-bash has none): run `python scripts/fetch_dataset.py`
and `python scripts/parse_dataset.py` instead — same thing.

`make tables` prints the deltas against the paper and writes one CSV per table
to `results/tables/`. Expected runtime: **< 2 seconds** on any machine.

Expected output (first lines):

```
rows parsed: blocking=83 non-blocking=86 total=169
== Table 5  Taxonomy
  app               Blocking  NonBlocking SharedMemory MessagePassing
  Total                   83           86          105           65
  paper                   85           86          105           66
  delta                   -2            0            0           -1
```

Tables 9 and 10 match the paper exactly; the deviations in Tables 5/6/7 come
from two BoltDB blocking bugs that are missing from the released snapshot — see
`docs/claims.md` (claim C2) for the analysis.

## Build / run commands

```bash
make setup      # download data/bug_table.xlsx (pinned upstream commit)
make tables     # L1: recompute Tables 5, 6, 7, 9, 10
make clean      # remove results/raw and __pycache__
```

## Credits and starting point

* Upstream dataset: <https://github.com/system-pclub/go-concurrency-bugs>
  pinned at commit `f2655063a2278cff64a51121b73801eda05fdcfa` (the last upstream
  commit, 2019-05-18). `scripts/fetch_dataset.py` records this pin.
* The upstream repository states no explicit licence; the dataset is used here
  for academic replication only and is redistributed unmodified, with credit.
* `scripts/parse_dataset.py` and everything under `docs/`, `results/`, `repro/`
  is our own code.
* Files we did not modify: all upstream data. Files we wrote: see `git log`
  for this repository.

## Team

| Member | Student ID | Role |
|---|---|---|
| _TBD_ | _TBD_ | A — data pipeline & statistics |
| 张歆海 | 1240012291 | B — build & run environment (Docker, Go toolchain) |
| _TBD_ | _TBD_ | C — bug reproduction & detector experiments |
| _TBD_ | _TBD_ | D — analysis, report & presentation |

## AI usage

See the AI usage statement in the final report; tool usage per member is tracked
there, as required by the course.
