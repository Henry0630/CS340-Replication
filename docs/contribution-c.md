# Role C contribution record

Member: Haotong Xie. Student ID: 1230022122. GitHub: Nobody325sun.

This note is evidence for D's canonical weekly log and contribution statement.
It records completed work and remaining experiment scope without changing
other members' histories or claiming their work.

| Work | Evidence | Report use |
|---|---|---|
| Implement the missing pinned-data fetcher and offline parser; add regression tests, original workbook, five computed tables, and a 169-record inventory | [Commit 1b3e968](https://github.com/Henry0630/CS340-Replication/commit/1b3e9684120b4253aeb1336747ff20417cff4b7e) | Setup, Workloads, Results |
| Select ten candidates across three repositories; inspect fixing commits and the pre-fix source; define triggers, controls, risk, and effort | [Candidate document](candidates.md), introduced with this note | Workloads, Reproduction Setup |
| Define the reproducibility interface and separate trigger evidence from detector reports | [Reproducer specification](../repro/README.md), introduced with this note | Setup, Methodology |
| Review C1-C4 against actual data and the paper; distinguish additional team checks from paper protocol | [Claims review](claims-review.md), introduced with this note | Claims, Deviations, Limitations |

The data-pipeline work is a cross-role prerequisite implemented at the user's
request, even though the original role table assigned the pipeline to A.
It does not transfer ownership of A's subsequent statistical analysis to C.

## Validation performed

- The 12 existing data-pipeline tests pass; the workbook hash is verified.
- Candidate IDs, commit hashes, source rows, patch-size limits, and reproduction
  flags are checked against the committed CSV.
- Fixing commits and first parents were retrieved from upstream GitHub; the
  relevant pre-fix source files were read for all ten candidates.
- The new documents use English text and resolve their local links.
- No Go/Docker build, real bug reproduction, or detector run is claimed.

## AI assistance

Codex assisted with the data scripts, tests, source inspection, candidate
selection, experiment specification, and document drafting under the member's
direction. This disclosure should be incorporated into the final report's AI
usage statement. AI assistance is not evidence that an experiment was executed.

## Remaining team workflow

D owns `docs/weekly-log.md` and the canonical claims text on `d-report`.
Reconcile their descriptions with these actual contributions and commit
subjects during review. B reviews C according to the review rotation. A PR
and the required reviewer decision precede merging into main. Runtime work
continues in week two after the experiment environment has been verified.
