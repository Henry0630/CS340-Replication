# Team division

Group 5 — 4 members. Every member owns one vertical slice; the report is
assembled from the slices, but the person who produced a number owns the
sentence that cites it in the report.

## Roles

| Role | Member | Student ID | Email | Scope |
|---|---|---|---|---|
| A — data pipeline & statistics | 辛相天 | 1240006592 | 1240006592@student.must.edu.mo | Parse the pinned upstream dataset, recompute Tables 5/6/7/9/10, and record every deviation from the paper in `docs/deviations.md`. |
| B — build & run environment | 张歆海 | 1240012291 | 1240012291@student.must.edu.mo | Dockerfile, Go toolchain pinning, `docs/environment.md`, `docs/env-setup.md`, `make env` / `make docker-build`. |
| C — bug reproduction & detector experiments | 谢昊桐 | 1230022122 | 1230022122@student.must.edu.mo | Rebuild the 15–20 selected bugs at their buggy commits under `repro/`, trigger them, and re-measure detector coverage (paper 5.3, 6.3). |
| D — analysis, report & presentation | 郭子嘉 | 1240015875 | 1240015875@student.must.edu.mo | `docs/claims.md`, `report/main.tex` + `report/refs.bib`, `docs/weekly-log.md`, `CONTRIBUTING.md`, final tagging and presentation. |

## Week 1 (11/7 – 11/8 23:59)

The weekly check is **Sunday 23:59**. Anything pushed after that counts
against the following week and cannot be made up, so every member needs at
least one meaningful commit on `main` before the deadline.

| Role | Week-1 deliverable |
|---|---|
| A | `scripts/fetch_dataset.py` + `scripts/parse_dataset.py`; `make setup`, `make check`, `make tables` run green; Tables 5/6/7/9/10 regenerated into `results/tables/`. |
| B | `scripts/check_env.py` + `docs/environment.md` (L1 rows filled from `make env`); Dockerfile drafted. |
| C | Ten candidate bugs selected and justified in `docs/candidates.md` (project, commit hash, bug class, expected trigger). |
| D | Repository, branches and collaborators set up; `docs/team_division.md` with real names; `CONTRIBUTING.md`; `report/main.tex` Introduction draft; `docs/weekly-log.md` created. |

## Week 2 (11/14 – 11/15 23:59)

The freeze, merge window and buffer keep the same times: code freeze **21:30**,
merge window **21:30–22:30**, buffer **22:30–23:59**, check **23:59 sharp**.
Week 2 is the week where claims must survive contact with the data, so the
deliverables are written to be *defensible*, not merely complete.

| Role | Week-2 deliverable | State |
|---|---|---|
| A | The deviations register and the paper-vs-ours comparison, reconciled with the actual parser output rather than with the paper's rendered tables. | In progress — `tables_check.md` drafted; reconciliation with D. |
| B | The experiment image built and **verified** on a machine with Docker: kernel, `go version`, `gcc --version`, base-image digest, image size, and both build timings written into the L2 rows of `docs/environment.md`. The digest must replace the floating tag in the `Dockerfile`. | **Not started.** The L2 rows of `docs/environment.md` are still `pending`; no L2 number may enter the report until they are filled. |
| C | At least one working reproducer under `repro/<candidate-id>/` with a build log, three runs, and a recorded detector outcome; then the remaining shortlist and the race-detector protocol. The candidate list and the reproducer contract already exist. | Contract and ten candidates done; **no build, run or detector result yet**. |
| D | `docs/claims.md` reconciled with C's review; `docs/discrepancy_analysis.md` written; `report/main.tex` filled for setup, results, discrepancies, extension and conclusion; `docs/weekly-log.md` corrected to match the real commit subjects. | This commit. |

### Hard rules for week 2

- **No L2 number enters the report before B's environment record is final.**
  Until the digest and kernel are known, the report quotes the paper's
  detector numbers *as the paper's* and says plainly that our own coverage is
  unmeasured.
- **A reviewer's suggestion is not evidence.** C's review of the claims file
  is reconciled with the data before it is adopted; where the review and the
  data can be checked directly, the data decides.
- **The contribution statement must match `git log`.** The week-1 data
  pipeline was implemented by C at the team's request, while A's statistical
  scope stays with A. The weekly log records who wrote the code.
- **The report may only contain numbers that exist in `docs/claims.md`**, and
  every one of them must point at `results/tables/*.csv` or `repro/*/logs`.

## Branches

One branch per role, all branched off `main`:

| Branch | Owner |
|---|---|
| `a-dataset` | A |
| `b-env` | B |
| `c-repro` | C |
| `d-report` | D |

`main` is the default branch and always contains the merged state of the
four branches. Merges happen on Sunday after the 21:30 code freeze.

## Cross-role dependencies

- A's dataset must be pinned before B can rebuild the buggy programs.
- C's run logs are the only source of the L2 numbers; B's environment
  record must be final before C's numbers are quoted anywhere.
- D's `docs/claims.md` is the contract between the numbers and the report:
  every claim states the paper value, our value, and where the deviation
  is explained.
