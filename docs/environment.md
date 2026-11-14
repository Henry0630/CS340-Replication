# Environment

Everything that affects the numbers is pinned here and reproduced by
`Dockerfile` + `.github/workflows/env.yml`. `python scripts/check_env.py` prints
the same facts for whatever machine you are sitting at.

The image is **built and measured on a clean GitHub Actions runner**, not on a
student laptop: the B machine has no Docker (decision log below), and a CI run is
a better "clean machine" than any laptop — anyone, including the TA, can press
"Re-run" and get the same block. The raw measurement is committed under
`results/ci/`.

## L1 — dataset statistics (works anywhere)

| Item | Value |
|---|---|
| Python | 3.11.15 (standard library only; 3.8+ works) |
| Dataset | `bug table.xlsx`, upstream commit `f2655063a2278cff64a51121b73801eda05fdcfa` |
| Dataset sha256 | `a0e5f0103600b3c394b86cb975f403789366f0190312019fae648de0cd8e3235` |
| Host used for L1 | Windows 11 build 10.0.26300, Intel Core 5 220H (16 logical cores), 15.6 GB RAM |
| Runtime of `make tables` | < 2 s |

L1 has no dependency on the Go toolchain, so its results must be identical on
every member's machine. If they differ, the counting logic is wrong.

## L2 — reproduction and detector experiments (measured)

Measured 2026-11-14 by `docker/verify.sh` in CI; raw block:
`results/ci/env-L2-20261114T1116Z.md`. Re-run: Actions → *environment* →
"Re-run all jobs".

| Item | Value |
|---|---|
| Measurement host | GitHub Actions `ubuntu-22.04` runner, 4 vCPU, Docker 28.0.4 (`overlay2`) |
| Host OS / kernel | Ubuntu 22.04.5 LTS / `Linux 6.8.0-1070-azure x86_64` |
| Container OS | Debian GNU/Linux 12 (bookworm) |
| Go, main reproduction | `go1.22.4 linux/amd64` |
| Go, Extension control | `go1.21.13 linux/amd64` |
| Compiler | `gcc (Debian 12.2.0-14) 12.2.0` |
| Base image, main | `golang@sha256:0c02666907338370a3272af1b4642a184968911d2317f0bd010dcef89a081d6f` (tag `golang:1.22.4-bookworm`) |
| Base image, control | `golang@sha256:c6a5b9308b3f3095e8fde83c8bf4d68bd101fce606c1a0a1394522542509dda9` (tag `golang:1.21.13-bookworm`) |
| Image size | 944 MB (go1.22) / 934 MB (go1.21) |
| Image build time | 34 s cold, 19 s warm (go1.22); 32 s cold, 17 s warm (go1.21) |
| `GOMAXPROCS` | 4, set in the image |
| `CGO_ENABLED` | 1 (required by the race detector) |
| `GOTOOLCHAIN` | `local` — Go cannot silently swap toolchains |
| Detector flags | `-race`; the built-in deadlock detector is always on |
| Race detector verified | PASS — the build-time smoke test reports `DATA RACE` |
| Runs per bug | ≥ 3 for statistics; 100 for the Table 12 protocol |
| Wall time per reproducer | _to fill in week 3, per bug, in the README_ |

### Three ways to reproduce this table

1. **CI (default, no local install):** push a change to `Dockerfile` / `docker/`,
   or run the workflow manually. The job builds both images, runs the smoke test,
   and commits the measured block to `results/ci/`.
2. **GitHub Codespaces:** open the repo → *Code* → *Codespaces* → create; the
   devcontainer installs Docker-in-Docker, then run `bash docker/verify.sh`.
3. **Your own machine with Docker:** `make verify` (= `bash docker/verify.sh
   --out results/local/env-L2-<host>.md`). Commit the file under `results/local/`;
   kernel and build times will differ from the CI row, Go/gcc/image digest must
   not.

## Environment decision log

**Decision (2026-11-07, host B / 张歆海):** no environment is installed on the B
machine (no Go, no Docker, no WSL2). L2 is built and measured through the CI
workflow above, and interactive work uses Codespaces or a teammate's machine.

| Candidate | Decision |
|---|---|
| GitHub Actions runner (Linux) | **used** — clean machine, free, auditable log |
| GitHub Codespaces (devcontainer) | available as the interactive route |
| WSL2 + Ubuntu + native Go | not installed on host B |
| Docker Desktop on host B | not installed on host B |
| Windows-native Go only | rejected for L2 (wrong OS semantics), fine for reading code |

## Deviations to record as we go

The report needs a table with **item / paper's setting / our setting / reason**.

| Item | Paper | Ours | Reason |
|---|---|---|---|
| Experiment host | Authors' machines, Go 1.11-era | GitHub Actions `ubuntu-22.04`, kernel 6.8 | The B machine has no Docker; the paper's metrics are counts, so the host does not change them |
| Go version | Bugs from 2015–2018 code | go1.22.4 (builds may need `-mod=mod` / API fixes) | Modern toolchain; every workaround per bug goes in `repro/<bug>/notes.md` |
| Scale | 41 bugs re-run | target 15–20 | Time; stated as a reduced scale |
| Dataset size | 85 blocking bugs | 83 blocking patches shipped upstream | Two BoltDB blocking bugs are missing from the release (see `docs/claims.md` C2) |
