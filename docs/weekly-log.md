# Weekly log

One row per commit that matters. This file is the evidence behind the
contribution statement in the report: the assistant/TA reads `git log` and
this table together, so every line here must correspond to a real commit.

| Week | Date | Member | Commit summary | Report section it feeds |
|---|---|---|---|---|
| 1 | 2026-11-08 | 辛相天 (A) | `dataset: add tables check and deviations draft` | Deviations |
| 1 | 2026-11-08 | 张歆海 (B) | `env: pin experiment image with build-time race smoke test` | Reproduction Setup |
| 1 | 2026-11-08 | 张歆海 (B) | `env: add environment report script and hand-off checklist` | Reproduction Setup |
| 1 | 2026-11-08 | 张歆海 (B) | `docs: add markdown-to-html converter for shareable documents` | — |
| 1 | 2026-11-08 | 张歆海 (B) | `meta: record role B in team table` | Team division |
| 1 | 2026-11-08 | 张歆海 (B) | `meta: force LF line endings for scripts and Dockerfile` | — |
| 1 | 2026-11-08 | 谢昊桐 (C) | `data: add pinned dataset pipeline and verified tables` | Reproduction Setup, Results |
| 1 | 2026-11-08 | 谢昊桐 (C) | `repro: complete week-one candidate selection and protocol` | Reproduction Setup, L2 scope |
| 1 | 2026-11-08 | 郭子嘉 (D) | `meta: fill role table with member names` | Team division |
| 1 | 2026-11-08 | 郭子嘉 (D) | `report: add introduction draft and weekly log` | Introduction |
| 2 | 2026-11-14 | 郭子嘉 (D) | `docs: reconcile claims with review and record deviations` | Claims, Deviations |
| 2 | 2026-11-14 | 郭子嘉 (D) | `report: fill setup, results, discrepancy and extension sections` | Reproduction Setup, Results, Analysis of Discrepancies, Extension |
| 2 | 2026-11-14 | 郭子嘉 (D) | `report: reduce claims to three with verdicts and add figures` | Claims, Results, Analysis of Discrepancies |
| 2 | 2026-11-14 | 郭子嘉 (D) | `meta: document starting code, workloads and build commands` | Reproduction Setup |
| 2 | 2026-11-14 | 郭子嘉 (D) | `report: make paper-vs-ours comparison legible in figures` | Results |
| 2 | 2026-11-14 | 郭子嘉 (D) | `report: number and cross-reference the remaining tables` | Reproduction Setup, Analysis of Discrepancies |
| 2 | 2026-11-14 | 郭子嘉 (D) | `report: drop textcomp dependency that broke compilation` | Analysis of Discrepancies |
| 2 | 2026-11-14 | 郭子嘉 (D) | `report: correct cover-page reference to a file the repo does not contain` | Reproduction Setup |
| 2 | 2026-11-14 | 郭子嘉 (D) | `docs: move the deviation register to a filename the role table leaves free` | Deviations |
| 2 | 2026-11-14 | 郭子嘉 (D) | `report: make the report compile and keep every table inside the text width` | Reproduction Setup, Analysis of Discrepancies |
| 2 | 2026-11-14 | 郭子嘉 (D) | `report: replace the pending environment rows with the measured values` | Reproduction Setup, Claims |
| 2 | 2026-11-14 | 郭子嘉 (D) | `meta: merge B's measured experiment environment into main` | Reproduction Setup |
| 2 | 2026-11-15 | 郭子嘉 (D) | `report: fix the remaining LaTeX errors so the PDF builds cleanly` | Reproduction Setup, Analysis of Discrepancies |
| 2 | 2026-11-15 | 郭子嘉 (D) | `docs: point the role table at the real deviations file and log the merge` | Team division |
| 2 | 2026-11-15 | 郭子嘉 (D) | `docs: align the weekly log with the commit subjects` | Contribution Statement |

## Scope note on the week-1 data pipeline

The pinned-data fetcher and the offline parser were implemented by **C**, in
commit `data: add pinned dataset pipeline and verified tables`, at the request
of the team, because the pipeline was a cross-role prerequisite. The role table
assigns the pipeline to **A**, and A's statistical scope — the deviations
register and the paper-vs-ours comparison — remains A's. The weekly log records
who wrote the code, not who owns the analysis.

## Merge status

This table lists what exists on each branch; it does **not** claim that the
branches have been merged. As of the week-2 commit above, `main` still
carries only the environment work and does not yet contain
`a-dataset`, `c-repro` or `d-report`. Merges happen in the Sunday window
defined in `CONTRIBUTING.md`.

## How to use this file

- Add one row **in the same commit** that does the work, or immediately
  after it — never batch rows at the end of the week.
- The *Commit summary* column must match the actual commit subject.
- The *Report section* column is the section of `report/main.tex` that the
  commit produced material for. If a commit feeds nothing in the report
  (e.g. a typo fix), write "—" rather than inventing a section.
- Update the table when the week rolls over; the header row stays.
