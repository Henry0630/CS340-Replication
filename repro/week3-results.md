# Week-three results: application-level vs extracted model

Owner: Haotong Xie (1230022122), role C.

Scope: one blocking bug, `grpc-793` (row 79 of the blocking sheet; fixing commit
`5a547ed72c09faf4050739d54caea1d51f4d276d`, pre-fix checkout
`7c6103d142da5fd11a36964c3a42cf698056b00b`). Two workloads are compared:

- **application-level** (`repro/grpc-793/app/`, `workload_kind:
  original_application`): the complete upstream grpc-go tree is built in GOPATH
  mode and the workload calls `GracefulStop()` twice on a real `grpc.NewServer()`.
- **extracted model** (`repro/grpc-793/harness/`, week two): the `GracefulStop`
  body copied out of the same revision.

No number in this document is an estimate: every row below was produced by a
command and checked in `runs.jsonl`.

## Status

The canonical run is the pinned image `cs340-legacy:go1.12` (Go 1.12.17,
Debian bookworm-slim, `CGO_ENABLED=1`), wired in `.github/workflows/repro.yml`
as job `grpc-793-app`. **It has not run in this session**: the branch could not
be pushed from the working machine (no GitHub credentials). What is measured
below is a local pre-validation on the same Go 1.12.17 release, which is useful
for validating the scripts but is **not** the pinned-image result.

## Measured rows

| Workload | Environment | Buggy symptom | Fixed control | Detector trial |
|---|---|---|---|---|
| complete application | local pre-validation: Windows/amd64, Go 1.12.17, `CGO_ENABLED=0`, GOPATH mode | **3/3** `deadlock_reported` (exit 2) | **3/3** `completed` with `ORACLE:` | **1/1** `deadlock_reported` (detector fired) |
| extracted model | same local toolchain: Go 1.12.17, Windows/amd64, `CGO_ENABLED=0` | **3/3** `deadlock_reported` (exit 2) | **3/3** `completed` with `ORACLE:` | **1/1** `deadlock_reported` (detector fired) |
| extracted model (week two) | CI image `cs340-repro:go1.22`, Go 1.22.4, Linux, `CGO_ENABLED=1` | **3/3** `timeout` after 10 s, no runtime report | **3/3** `completed` | **1/1** no runtime deadlock report |
| complete application (canonical) | `cs340-legacy:go1.12`, Go 1.12.17, Linux, `CGO_ENABLED=1` | **pending** — workflow job `grpc-793-app` | **pending** | **pending** |

The third row is the week-two measurement copied from
[`week2-results.md`](week2-results.md); it is the only row produced in the
pinned Go 1.22.4 image.

## Local pre-validation commands

The working machine has no Docker, so the runner was executed in its
in-container mode against Go 1.12.17 for Windows:

```sh
export PATH=/path/to/go1.12.17/go/bin:$PATH
export CS340_IN_CONTAINER=1 CGO_ENABLED=0
bash repro/grpc-793/app/reproduce.sh --variant buggy --mode symptom \
  --runs 3 --timeout 10 --output <scratch>/app-buggy
bash repro/grpc-793/app/reproduce.sh --variant fixed --mode symptom \
  --runs 3 --timeout 10 --output <scratch>/app-fixed
bash repro/grpc-793/app/reproduce.sh --variant buggy --mode deadlock \
  --runs 1 --timeout 10 --output <scratch>/app-detector
```

`build.sh` resolved and verified the pinned commits
(`grpc-go 7c6103d142da5fd11a36964c3a42cf698056b00b`,
`golang.org/x/net 6a513affb38dc9788b449d59ffed099b8de18fa0`,
`github.com/golang/protobuf c3cefd437628a0b7d31b34fe44b3a7a540e98527`) and the
build log records each resolution. The workload reached the second
`GracefulStop` and the runtime printed:

```text
fatal error: all goroutines are asleep - deadlock!
...
google.golang.org/grpc.(*Server).GracefulStop(...)
	.../google.golang.org/grpc/server.go:801
main.main()
	.../cs340/grpc793/main.go:19
```

Wall times: buggy 1.198 s / 0.174 s / 0.164 s; fixed 0.270 s / 0.152 s /
0.149 s; detector 1.049 s. The first buggy trial includes the interpreter's
first runtime start-up, not a different behaviour.

The extracted model was rebuilt under the same Go 1.12.17 toolchain by copying
`repro/grpc-793/harness/{buggy,fixed}/main.go` into a GOPATH and running the
same trials: buggy 3/3 `deadlock_reported`, fixed 3/3 `completed`, detector 1/1
`deadlock_reported`.

## What the comparison shows

1. **The application-level workload works.** The complete 2016 grpc-go revision
   builds with Go 1.12.17 once the pre-modules dependency layer is pinned, and
   the second `GracefulStop` call reproduces the deadlock with a runtime stack
   pointing at `server.go` — the same file the upstream fix changes.
2. **Under the same toolchain, the extracted model did not change the detector
   outcome for this bug.** Both workloads reported the global deadlock in 3/3
   trials. The week-two `timeout` without a report is therefore a toolchain /
   image difference (Go 1.22.4, `CGO_ENABLED=1`, container), not evidence that
   extraction hides the bug.
3. **This is one bug, not coverage.** Nothing here estimates the paper's Table 8
   ratio (2 of 21 blocking bugs detected). The application-level row is a single
   observation; the coverage question stays unmeasured.

## Environment differences to report

| Item | Week-two extracted CI | Week-three local pre-validation | Week-three canonical (pending) |
|---|---|---|---|
| Go | 1.22.4 | 1.12.17 | 1.12.17 |
| OS / kernel | ubuntu-latest (Linux) | Windows/amd64 | Debian bookworm-slim, Linux |
| `CGO_ENABLED` | 1 | 0 | 1 |
| image | `cs340-repro:go1.22` | none (host binary) | `cs340-legacy:go1.12`, base `debian@sha256:734a72b3d6142a71993b4bc580ca01d8ca687f77a2c422d96a961d3376b179bc` |
| source | extracted `GracefulStop` body | complete `grpc-go@7c6103d` | complete `grpc-go@7c6103d` |
| dependency layer | none (stdlib only) | `deps.lock` (x/net + protobuf) | `deps.lock` (x/net + protobuf) |
| container | yes | no | yes |

The local pre-validation differs from the canonical row in OS, cgo, and the
absence of the container; those differences are recorded rather than assumed
away.

## Canonical evidence (to be produced by CI)

When `c-repro` is pushed, the `grpc-793-app` job builds
`docker/legacy/Dockerfile`, runs the three invocations above inside
`cs340-legacy:go1.12`, and uploads `results/raw/grpc-793/app-*` plus
`runs.jsonl`, stdout, stderr, stacks, and `build.log` as the
`week3-grpc-793-application` workflow artifact. That artifact is the canonical
application-level row; the table above will be updated with its numbers in the
same follow-up commit.

## Deviations

- The pre-fix checkout is the first parent of the fixing commit; the fixed
  control is the fixing commit itself. The grpc-go tree is 2016 code and has no
  `go.mod`; the pinned dependency layer is the newly documented layer in
  `repro/grpc-793/app/deps.lock`, not a modification of upstream files.
- The pinned legacy toolchain (Go 1.12.17) is newer than the original
  developers' toolchain (2016), which is recorded with every trial.
- No other blocking bug was attempted this week; the comparison intentionally
  uses one bug end-to-end rather than many bugs superficially.
