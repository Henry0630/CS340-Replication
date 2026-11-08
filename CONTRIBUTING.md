# Contributing

## Commit message format

```
<scope>: <what changed> (<student id> <full name>)
```

- `<scope>` is one of: `meta`, `data`, `env`, `repro`, `report`, `docs`.
- The trailing `(student id full name)` is **mandatory**. The course checks
  `git log --format='%an'` to confirm each member contributed from their own
  GitHub account, and the weekly check expects this string in the subject.

Examples:

```
data: pin upstream dataset and regenerate tables 5/6/7/9/10 (1240006592 辛相天)
env: add Dockerfile and record host facts for L1 (1240012291 张歆海)
repro: select ten candidate bugs with commit hashes (1230022122 谢昊桐)
report: add introduction draft and weekly log (1240015875 郭子嘉)
```

## Branches

One branch per role, cut from `main`:

| Branch | Owner |
|---|---|
| `a-dataset` | A |
| `b-env` | B |
| `c-repro` | C |
| `d-report` | D |

Never commit directly to `main` — `main` only receives merged branches.

## Weekly freeze and merge

- **Sunday 21:30 is the code freeze.** After 21:30 no new commits land on
  the role branches; anything unfinished moves to the next week.
- **Sunday 21:30–22:30 is the merge window.** The role branch owner merges
  their own branch into `main` and resolves conflicts. If the owner is
  unavailable, the merge is deferred to the next member in the rotation.
- **Sunday 22:30–23:59** is buffer for last-minute fixes and for updating
  `docs/weekly-log.md`. `main` must be green (`make tables` exits 0) by
  23:59.
- The weekly check is **23:59 sharp**. Commits pushed after that count
  against the following week and cannot be made up.

## Review rotation

Each branch is reviewed by the **next member in the A → B → C → D → A
rotation**, i.e. A reviews B, B reviews C, C reviews D, D reviews A.

- A review is one commit on the reviewing member's own branch that either
  fixes something on the reviewed branch (merged back) or leaves a comment
  on the reviewed branch's PR.
- The reviewing member is responsible for the merge of the branch they
  reviewed, if the branch owner has not merged by 22:00.
- Reviewer and author must be different people.

## Before you commit

```bash
make tables      # must exit 0 and print no unexpected deltas
```

For changes under `repro/`, also record the Go version and the image digest
in `docs/environment.md` — an unlabelled run log is not a result.

## Do not

- `git add .` — stage only the files you changed, or the history stops
  being attributable per person.
- Rewrite or squash other members' commits.
- Amend a pushed commit; add a new one.
