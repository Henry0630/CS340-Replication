# S7 — Critical analysis (page 7)

- **Speaker:** 张歆海 (1240012291), 50 s, 3:30–4:20
- **Title on slide:** `Critical analysis: four differing cells, two data causes`
- **Sources (footer):** `tables_check.md` · `docs/claims.md` (C1–C2) · `docs/environment.md` · `results/ci/legacy-20261121T0655Z.md`

## Content on the slide

| Item | Paper | Ours | Cause |
|---|---|---|---|
| Blocking bugs | 85 | **83** | 2 BoltDB patches absent from the release |
| Message passing | 66 | **65** | same two rows |
| Shared memory | 105 | 105 | `+1` double label cancels `−1` missing row |
| Non-blocking | 86 | 86 | — |

- `kubernetes#11298`: labelled **both** shared *and* message, *both* wait *and* channel-with-lock → the paper assigns a single cause.
- Paper §5.3 itself names the two absent bugs: `BoltDB#392`, `BoltDB#240`.

Reproducibility strip (four blocks):

| Block | Value |
|---|---|
| Go image | `golang@sha256:0c02666907…` → go1.22.4 |
| Extension image | `golang@sha256:c6a5b9308b…` → go1.21.13 |
| Legacy toolchain | go1.12.17 · `pre-modules: yes` · `LEGACY BUILD OK` |
| Clean machine | GitHub Actions `ubuntu-22.04`, artifacts in `results/ci/` |

## Speaker notes (50 s)

> Four of our cells differ from the paper, and the interesting part is that they
> have only two causes — both visible in the released workbook.
>
> First: the release ships 83 blocking patches, not 85. The two that are missing
> are BoltDB bugs, and the paper's own §5.3 names BoltDB#392 and #240 as the only
> blocking bugs its built-in detector catches — so we can point at exactly what
> is absent, instead of guessing.
>
> Second: one Kubernetes record, #11298, is labelled twice — both shared and
> message passing, both wait and channel-with-lock. The paper assigns a single
> cause. That single row is why our shared-memory total matches exactly at 105
> while message passing is 65, not 66: one `+1` and one `−1` cancel out.
>
> So the deltas are a property of the released data, not of our counting — our
> script prints those flags on every run.
>
> On reproducibility: both images are pinned by digest, `GOMAXPROCS` and cgo are
> fixed, and the 2015–18 trees are built by a pinned Go 1.12 legacy layer —
> BoltDB v1.3.1 compiles unmodified. The CI job is the clean machine.

## Hard numbers to keep at hand

`83 / 85` · `65 / 66` · `105 / 105` · `86 / 86` · `+1 / −1` · `944 / 934 MB` · `19–34 s`

## Q&A points owned by this page

- "If two rows are missing, why does shared memory still match at 105?" → the
  `kubernetes#11298` double label adds one to shared and one to message, so the
  shared total absorbs the missing BoltDB Mutex row.
- "Can anyone rebuild this?" → digests + `make verify` + `results/ci/` artifacts.
