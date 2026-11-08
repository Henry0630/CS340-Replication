# Week 1 claims review for role D

Reviewer: Haotong Xie (1230022122), role C.

Reviewed version: [d-report at 84f27fd](https://github.com/Henry0630/CS340-Replication/blob/84f27fd943756315a117b80b0cf24260363ee315/docs/claims.md).
The latest team division assigns the canonical claims document to D. This
review supplies corrected wording and evidence without copying or overwriting
D's branch. D should reconcile these items into the canonical document when
reviewing the combined report. All local L2 experiments remain pending.

Evidence: [table mapping](table_mapping.md), [inventory](../results/tables/bug_inventory.csv),
Tables [5](../results/tables/table5.csv), [6](../results/tables/table6.csv),
[7](../results/tables/table7.csv), [9](../results/tables/table9.csv),
[10](../results/tables/table10.csv), and the
[paper](https://songlh.github.io/paper/go-study.pdf).

## C1: taxonomy and data coverage

**Judgment: partially supported for our commit-backed sample.**

Suggested wording: The released workbook contains 171 bug entries, of which
169 have valid commit hashes and corresponding released patches. Our pipeline
includes 83 blocking and 86 non-blocking records, with 105 shared-memory labels
and 65 message-passing labels. The paper reports 85 / 86 / 105 / 66.

Correction: `blocking!90` (boltdb#392) and `blocking!92` (boltdb#240) exist in
the workbook; their commit cells contain issue IDs. They are not absent rows.
They are excluded from the commit-backed inventory. Also, `blocking!35`
(kubernetes#11298) has overlapping shared/message and Wait/ChanWith labels.
Preserve those labels and explain the resulting differences rather than
describing every discrepancy as a missing-row problem.

## C2: Go-specific versus traditional causes

**Judgment: supported for the raw non-traditional labels; broader safety
comparisons require care.**

The draft's 61 percent calculation uses shared-memory counts, not the
non-traditional label. These are different classifications.

Suggested wording: Among the 169 included records, 54 blocking rows have
`non-trandition` (blocking column L) set to 1 and 40 non-blocking rows have
`non-traditional` (non-blocking column H) set to 1. Thus 94/169, or about
55.6 percent, carry a non-traditional label. This supports a majority claim
within this dataset, not a universal failure probability for Go constructs.

Reproduce this supplementary count with the existing standard-library parser:

```sh
python -c "import sys; sys.path.insert(0, 'scripts'); from parse_dataset import read_sheets, parse_bugs, DATASET_PATH; bugs=parse_bugs(read_sheets(DATASET_PATH)); print({kind:sum(b.flag('L' if kind=='blocking' else 'H') for b in bugs if b.behavior==kind) for kind in ('blocking','non-blocking')})"
```

This is a supplementary workbook-label count; the current five CSV tables
do not contain a dedicated traditional/non-traditional column. Its source
coordinates must accompany the report. Shared-memory/message-passing counts
are not interchangeable with this classification.

## C3: what the fix data actually establishes

**Judgment: the draft's claim about shallow, incomplete, or bug-introducing
fixes is not established by the presented tables. Replace or separately source it.**

Suggested replacement claim: Fix strategies vary with bug causes. We reproduce
the strategy counts in Tables 7 and 10, preserving their original category
definitions; Table 10 matches every cell, while Table 7 has documented
differences from missing commit-backed records and overlapping labels.

Counting small changes or added synchronization does not prove that developers
failed to identify a root cause, or that fixes introduced new bugs. The current
work contains no experiment measuring those properties. Local before/after
reproducer controls can test whether a specific fix removes our observed
symptom, but cannot by themselves prove such general claims.

## C4: detector coverage and the sample mismatch

**Judgment: paper reference established; local detector replication inconclusive
until experiments are run.**

Suggested wording: The paper reports 2/21 blocking bugs detected by the built-in
deadlock detector (Table 8) and 10/20 non-blocking bugs detected with `-race`
within 100 runs each (Table 12). The race detector detects exactly half of that
sample, so avoid saying that it missed more than half. We have not measured
our own detector coverage yet.

**Required discrepancy statement: The commit-backed dataset inventory is marked
19 blocking / 23 non-blocking reproduced, while the paper reports 21 / 20.**

Scope explanation: both excluded BoltDB issue-only rows are marked reproduced;
including them gives 21 blocking flags in the full workbook. The non-blocking
workbook has 23 flagged rows, so its disagreement with the paper remains.
These flags describe upstream annotations, not this team's completed runs.

The paper's blocking detector experiment ran each deterministic bug once.
Our three-run stability qualification is an additional team requirement.
The 100-run race protocol is a separate experiment. See the
[reproducer contract](../repro/README.md).

## Extension: loop-variable semantics

**Judgment: planned hypothesis, not a result or a claim made by the 2019 paper.**

The [Go 1.22 release notes](https://go.dev/doc/go1.22) describe per-iteration
variables declared by for loops. The [transition explanation](https://go.dev/blog/loopvar-preview)
also explains language-version selection. Record the module's `go` directive,
actual toolchain, and any experiments/compiler flags; switching the container
tag alone is not proof that the intended language semantics changed.

Suggested wording: We will test whether the new loop-variable semantics remove
selected loop-capture symptoms. Anonymous-function bugs involving other shared
state need not disappear. Keep source, input, dependencies, and other settings
fixed where possible; record base-image and compiler differences instead of
asserting that two unverified image tags differ only in Go.

## Handoff checks

- Keep these suggested judgments distinct from new L2 measurements.
- Correct the weekly log using real commits: the data-pipeline implementation
  in `1b3e968` was committed by C; it should not be credited as A's implementation.
- Link the completed candidate document to its actual C commit after merge.
- Do not describe all of week one as merged while main still lacks the branches.
