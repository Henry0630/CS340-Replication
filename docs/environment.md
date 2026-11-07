# Environment

Everything that affects the numbers must be pinned here and reproduced by the
`Dockerfile` (week 2). Until the container exists and has been built, this file
is the single source of truth for "what we ran on".

Regenerate the machine facts with `python scripts/check_env.py` (it prints a
markdown block; paste it below instead of typing values by hand).

## L1 — dataset statistics (works anywhere)

| Item | Value |
|---|---|
| Python | 3.11.15 (standard library only; 3.8+ works) |
| Dataset | `bug table.xlsx`, upstream commit `f2655063a2278cff64a51121b73801eda05fdcfa` |
| Dataset sha256 | `a0e5f0103600b3c394b86cb975f403789366f0190312019fae648de0cd8e3235` |
| Host used (host B) | Windows 11 build 10.0.26300, Intel Core 5 220H (16 logical cores), 15.6 GB RAM |
| Runtime of `make tables` | < 2 s |

L1 has no dependency on the Go toolchain, so its results must be identical on
every member's machine. If they differ, the counting logic is wrong.

## L2 — bug reproduction and detector experiments (week 2+)

The experiments must run on **Linux**: the paper measured Go programs on Linux,
and hang/timeout, signal delivery and the race detector's behaviour are
OS-specific. Target environment (container on top of a Linux host):

| Item | Value |
|---|---|
| Host OS / kernel | _to fill: `uname -a` inside the container/VM_ |
| Go version | `golang:1.22.4-bookworm` → `go1.22.4 linux/amd64` (language version 1.22) |
| Extension comparison | `golang:1.21.13-bookworm` — same image, only the Go version differs |
| Compiler | gcc from `build-essential` in the image (record `gcc --version`) |
| Image digest | _to fill after the first build_ (`docker image inspect`) |
| CPU / cores / RAM | inherited from host: Intel Core 5 220H, 16 logical cores, 15.6 GB |
| `GOMAXPROCS` | 4, fixed in the Dockerfile |
| `CGO_ENABLED` | 1 (the race detector needs cgo) |
| Detector flags | `-race` for data races; the built-in deadlock detector is always on |
| Runs per bug | ≥ 3 for statistics; 100 for the race-detector experiment (Table 12 protocol) |
| Run duration | _to fill: seconds per reproducer, so the README can state expected runtimes_ |

## Environment decision log

**Decision (2026-11-07, host B / 张歆海):** no environment is installed on the
B machine (no Go, no Docker, no WSL2, and the group decided not to install
them). L2 experiments run on a teammate's machine that has Docker; the
`Dockerfile` in this repository is the single pin, and the hand-off procedure is
`docs/env-setup.md`.

Consequence to keep honest in the report: the image is **unverified until
someone runs it** — mark the L2 rows in this file `pending` until the hand-off
checklist returns the values below. Do not write environment numbers into the
report before they come from a real build.

| Candidate | Decision |
|---|---|
| WSL2 + Ubuntu + native Go | not installed on host B (decided 2026-11-07) |
| Docker Desktop (WSL2 backend) | not installed on host B; used instead on a teammate's machine |
| Windows-native Go only | rejected for L2 (wrong OS semantics), acceptable for reading code |
| Remote Linux VM | not needed |

Verification status: **not yet verified on any machine** — pending the hand-off.

## Deviations to record as we go

The report needs a table with **item / paper's setting / our setting / reason**.
Known deviations to enter immediately:

1. Go version: the paper studied bugs from 2015–2018 code; we build with a
   modern toolchain → old code may not compile (API drift). Pin each upstream
   repository at its buggy commit and record every workaround.
2. Scale: we reproduce a subset (target 15–20 bugs), not all 41.
3. Hardware: our laptop/VM vs. the authors' machines — matters little here
   because the paper's metrics are counts, not throughputs; state it anyway.
4. Two BoltDB blocking bugs are absent from the released dataset; if they are
   not recovered, we report 83 blocking bugs instead of 85.
