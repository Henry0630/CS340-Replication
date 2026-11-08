# Weekly log

One row per commit that matters. This file is the evidence behind the
contribution statement in the report: the assistant/TA reads `git log` and
this table together, so every line here must correspond to a real commit.

| Week | Date | Member | Commit summary | Report section it feeds |
|---|---|---|---|---|
| 1 | 2026-11-08 | 辛相天 (A) | Pin upstream dataset, add `fetch_dataset.py` / `parse_dataset.py`, regenerate Tables 5/6/7/9/10 | Reproduction Setup, Results |
| 1 | 2026-11-08 | 张歆海 (B) | `check_env.py`, `docs/environment.md` L1 rows, Dockerfile draft | Reproduction Setup |
| 1 | 2026-11-08 | 谢昊桐 (C) | Ten candidate bugs with commit hashes and expected triggers (`docs/candidates.md`) | Reproduction Setup |
| 1 | 2026-11-08 | 郭子嘉 (D) | Repo/branches/collaborators, `docs/team_division.md`, `CONTRIBUTING.md`, Introduction draft, this file | Introduction and Claims |

## How to use this file

- Add one row **in the same commit** that does the work, or immediately
  after it — never batch rows at the end of the week.
- The *Commit summary* column must match the actual commit subject.
- The *Report section* column is the section of `report/main.tex` that the
  commit produced material for. If a commit feeds nothing in the report
  (e.g. a typo fix), write "—" rather than inventing a section.
- Update the table when the week rolls over; the header row stays.
