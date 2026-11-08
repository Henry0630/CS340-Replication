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
