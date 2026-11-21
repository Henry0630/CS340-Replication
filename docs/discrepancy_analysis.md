# Deviations

Every place where our numbers differ from the paper, why, and whether it is an
upstream-data artefact or a reproduction artefact. Written by D (role: analysis,
report & presentation).

Sources:

- `results/tables/*.csv` — the five recomputed tables (`make tables`).
- `results/tables/bug_inventory.csv` — the 169-row record-level inventory.
- `docs/table_mapping.md` (C) — worksheet columns and the parser's checks.
- `tables_check.md` (A, on `a-dataset`) — A's setup-level deviation log and
  the paper-vs-ours comparison. Note that A's file lives at the **repository
  root**, not under `docs/`; this file is the canonical report-facing
  register and does not replace it.
- The paper: <https://songlh.github.io/paper/go-study.pdf>

## D1 — Setup deviations

Owner: A (`tables_check.md`, repository root on `a-dataset`).

| Item | Paper setup | Our setup | Reason |
|---|---|---|---|
| Go version | older toolchain, 2015–2018 code | Go 1.22.4 (`golang:1.22.4-bookworm`) | one unified environment; old code may need API repairs, each recorded per bug |
| Reproduction scale | authors re-ran 41 bugs (21 blocking, 20 non-blocking) | subset, target 15–20 bugs | limited time and manpower; the counting metrics of L1 are insensitive to scale |
| Hardware | authors' machines | Linux container on a teammate's laptop (Intel Core 5 220H, 16 logical cores, 15.6 GB) | the metrics are counts, not throughputs; stated as a limitation |
| Experiment image | n/a | `golang:1.22.4-bookworm` / `golang:1.21.13-bookworm`, both pinned by digest, `GOMAXPROCS=4`, `CGO_ENABLED=1`, `GOTOOLCHAIN=local` | the Dockerfile is the single pin; digests measured 2026-11-14 by `docker/verify.sh` in CI |

**The experiment images are built and measured.** B's environment record
(`docs/environment.md`) holds the kernel, compiler, image digests, image sizes
and build times, measured 2026-11-14 by `docker/verify.sh` in CI; the raw
block is committed under `results/ci/`. What is still outstanding is the
level-2 *runs*: no individual bug has been rebuilt at its pre-fix revision and
triggered yet, so no detector coverage number exists on our side.

## D2 — Data-scope deviations (L1)

Owner: C (parser, inventory), D (analysis).

### D2.1 Two issue-only rows are excluded from our inventory

The workbook holds 171 entries. Two blocking rows carry an issue ID in the
commit column instead of a 40-character commit hash:

| Sheet | Row | Issue ID | Cause | Cause axis |
|---|---:|---|---|---|
| blocking | 90 | boltdb#392 | Mutex | shared memory |
| blocking | 92 | boltdb#240 | Chan w/ | message passing |

They are **present in the released workbook**. They are excluded from *our*
inventory only because we cannot bind them to a commit and therefore cannot
reproduce them. Our scope is 169 bugs: 83 blocking, 86 non-blocking.

Independent corroboration: these two issue IDs are exactly the two bugs the
paper's built-in deadlock detector reports ($5.3), and their causes are exactly
the two cells that paper Table 6 needs to gain (`Mutex` +1, `Chan w/` +1).

### D2.2 One record carries two cause labels

`blocking!35`, `kubernetes#11298`, carries **both** a shared-memory and a
message-passing label, and **both** a `Wait` and a `ChanWith` cause. The
paper assigns it a single cause (message passing / `Chan w/`). We keep both
labels, as the parser's policy requires.

Effect: our Table 6 contains 84 cause assignments for 83 blocking bugs, and
our Table 7 `Remove` total of 21 is 21 assignments from 20 distinct records.

### D2.3 Cell-level result

Ours is the commit-backed scope with both labels retained. The paper column is
the published value.

**Table 5 — taxonomy**

| Application | blocking | non-blocking | shared memory | message passing |
|---|---:|---:|---:|---:|
| | paper / ours | paper / ours | paper / ours | paper / ours |
| Docker | 21 / 21 | 23 / 23 | 28 / 28 | 16 / 16 |
| Kubernetes | 17 / 17 | 17 / 17 | 20 / **21** | 14 / 14 |
| etcd | 21 / 21 | 16 / 16 | 18 / 18 | 19 / 19 |
| CockroachDB | 12 / 12 | 16 / 16 | 23 / 23 | 5 / 5 |
| gRPC | 11 / 11 | 12 / 12 | 12 / 12 | 11 / 11 |
| BoltDB | **3 / 1** | 2 / 2 | **4 / 3** | **1 / 0** |
| **Total** | **85 / 83** | 86 / 86 | 105 / 105 | **66 / 65** |

**Table 6 — blocking bug causes**

| Cause | paper | ours | delta | cause of the delta |
|---|---:|---:|---:|---|
| Mutex | 28 | 27 | −1 | excluded `boltdb#392` (D2.1) |
| RWMutex | 5 | 5 | 0 | — |
| Wait | 3 | 4 | +1 | `kubernetes#11298` second label (D2.2) |
| Chan | 29 | 29 | 0 | — |
| Chan w/ | 16 | 15 | −1 | excluded `boltdb#240` (D2.1) |
| Messaging Libraries | 4 | 4 | 0 | — |

**Table 7 — blocking fix strategies**

| Cause / strategy | paper | ours | delta | cause of the delta |
|---|---:|---:|---:|---|
| Mutex / Misc | 2 | 1 | −1 | excluded `boltdb#392` |
| Wait / Remove | 1 | 2 | +1 | `kubernetes#11298` second label |
| Chan w/ / Remove | 4 | 3 | −1 | excluded `boltdb#240` |
| all other cells | — | — | 0 | — |

**Tables 9 and 10 — non-blocking causes and fix strategies**

All 42 cells of Table 9 and all 35 cells of Table 10 match the paper,
including their total rows. No deviation.

### D2.4 The reconciliation

Every difference above is explained by D2.1 and D2.2 alone. We verified that
under the paper's own assignment convention — include the two issue-only rows,
and give `kubernetes#11298` one cause — our recomputation reproduces
**paper Table 5 cell by cell for all six applications**, **paper Table 6 in
all six cause columns**, and **paper Table 7 in every cell**. The model is
therefore not a correction fitted to the paper; it is the only assignment
consistent with the paper's own tables and with $$5.3.

We still report the commit-backed numbers as our primary result, because they
are the ones backed by a commit we can actually rebuild.

## D3 — Reproduced-flag discrepancy

The commit-backed inventory marks **19 blocking** and **23 non-blocking**
records as reproduced. The paper reports **21 blocking** and **20 non-blocking**
reproduced experiments.

- Blocking: both excluded issue-only rows are also marked reproduced, so the
  full workbook's blocking flag count is 21, matching the paper. The
  difference is entirely a scope effect.
- Non-blocking: the workbook holds 23 flagged rows against the paper's 20. This
  disagreement is **unexplained** and is recorded as such.

These flags are upstream annotations. They are **not** evidence that this team
has reproduced anything. No detector result has yet been produced by this
repository.

## D4 — Detector coverage (L2, partially measured)

The paper's numbers: deadlock detector 2/21 blocking bugs (5.3, Table 8);
race detector 10/20 non-blocking bugs within 100 runs each (6.3, Table 12).
The race detector detects exactly half of that sample.

Our own coverage is measured on three **extracted models** of blocking bugs, run
in the pinned `cs340-repro:go1.22` image (Go 1.22.4) on the CI runner:

| Model | Symptom trials | Fixed controls | Runtime detector report |
|---|---|---|---|
| `grpc-793` | 3/3 | 3/3 completed | none |
| `docker-256` | 3/3 | 3/3 completed | none |
| `grpc-1424` | 3/3 | 3/3 completed | `deadlock_reported` |

The numbers are quoted from `repro/week2-results.md`, with the raw per-trial
logs under `repro/` and the Go version, image digest, `GOMAXPROCS`,
`CGO_ENABLED` and the run count recorded alongside them, as
`docs/environment.md` and `repro/README.md` require.

**Why this does not estimate the paper's Table 8 coverage.** These are
`extracted_model` runs, not whole-application rebuilds: they copy the relevant
upstream synchronisation out of the original program and replace the
surrounding application dependencies, because the pinned upstream revisions
predate Go modules and cannot be built with Go 1.22 without an unrecorded
compatibility layer. In `grpc-1424` the harness blocks its last goroutine to
observe the missing notification, which can make the runtime report a global
deadlock although the original application symptom is a goroutine leak. The
paper's 2/21 blocking and 10/20 race-detector figures therefore remain the
paper's, and the workbook's 19/23 reproduced flags remain upstream
annotations rather than our run counts.

## D5 — Claims we do not make

Recorded so that no reviewer has to infer them:

- The non-traditional share is a **workbook-label count** (blocking column L,
  non-blocking column H), not a column of the five published tables. It is
  94/169 = 55.6 %. It is **not** the same quantity as the shared-memory share,
  and the two are never interchanged.
- We do **not** claim that upstream fixes are shallow, incomplete, or that they
  introduce new bugs. No experiment in this repository measures those
  properties.
- We do **not** claim that the race detector "missed more than half" of the
  non-blocking sample: it detected exactly half (10/20).
- We do **not** claim any Go 1.22 result. The extension is a planned
  experiment with a recorded protocol, not a finding.
