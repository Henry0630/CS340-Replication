# grpc-793 application-level notes

## Provenance

- Dataset row: blocking sheet row 79, `grpc#793`; inventory record
  `blocking:gRPC:5a547ed72c09faf4050739d54caea1d51f4d276d`:
  `reproduced_flag=1`, `patch_size_lines=1`, shared-memory label, cause
  `Mutex`, fix `Change`.
- Fixing commit (dataset commit):
  `5a547ed72c09faf4050739d54caea1d51f4d276d` ("Merge pull request #795 from
  tamird/graceful-deadlock").
- Pre-fix checkout: `7c6103d142da5fd11a36964c3a42cf698056b00b`.
- Source: `server.go`, `func (s *Server) GracefulStop()`.
- Upstream regression test added by the fix:
  `TestServerGracefulStopIdempotent`, which calls `GracefulStop` three times.

## What the workload does

`harness/main.go` imports the complete `google.golang.org/grpc` package, creates
a real server with `grpc.NewServer()`, and calls `GracefulStop()` twice:

```go
s := grpc.NewServer()
s.GracefulStop()
s.GracefulStop()
```

The pre-fix `GracefulStop` early-return branch takes `s.mu` a second time, so the
second call self-deadlocks in `(*Server).GracefulStop`. The fixing commit
changes that line to `s.mu.Unlock()`. The server has no listeners and no
connections; the bug is in the idempotency path and does not depend on active
RPCs. The fixed variant prints `ORACLE: grpc-793 fixed: second GracefulStop
returned`.

## Build path and compatibility layer

- Image: `docker/legacy` (B's environment work), Go 1.12.17 in GOPATH mode,
  `GO111MODULE=off`, `CGO_ENABLED=1`, base image
  `debian@sha256:734a72b3d6142a71993b4bc580ca01d8ca687f77a2c422d96a961d3376b179bc`.
- The 2016 grpc-go tree has no `go.mod` and no `vendor/` directory, so the
  dependency layer is reconstructed in a fresh GOPATH by `build.sh` from
  `deps.lock`: `golang.org/x/net` and `github.com/golang/protobuf` are pinned to
  commits from the same period. Every fetch is by commit SHA and checked with
  `git rev-parse HEAD`; no upstream source file is edited and no patch is
  applied.
- The Go toolchain is older than the original developers used (the bug is from
  2016) but is the newest pre-modules toolchain the pinned image supports; the
  exact compiler is recorded with every trial in `runs.jsonl`.

## Local pre-validation (non-canonical)

A first end-to-end run was executed on the working machine, which has no Docker:
Windows/amd64, Go 1.12.17, `CGO_ENABLED=0`, GOPATH mode. It is recorded here as
a pre-validation only; it is **not** the pinned-image result.

| Variant | Trials | Observed |
|---|---:|---|
| buggy | 3/3 | `deadlock_reported` (Go runtime reported `all goroutines are asleep - deadlock!`; exit 2) |
| fixed | 3/3 | `completed` with the `ORACLE:` marker |
| buggy detector trial | 1/1 | `deadlock_reported` (detector fired) |

The pinned-image run is wired in `.github/workflows/repro.yml` (job
`grpc-793-app`) but had not run when this commit was prepared: this session has
no credentials to push the branch. `repro/week3-results.md` records the
non-canonical results separately and lists the canonical run as pending.

## Relation to the extracted model

`../README.md` and `../notes.md` describe the week-two extracted model of the
same bug (Go 1.22, no upstream tree). Under the week-two toolchain that model
timed out without a runtime deadlock report; under Go 1.12.17 (this workload's
toolchain) the model reports the same global deadlock as the complete
application. The detector outcome therefore depends on the toolchain, not on
whether the code is extracted; this workload does not estimate the paper's
Table 8 coverage.

## Limitations

- One bug only. This is an application-level observation for grpc-793, not an
  estimate of application-level detector coverage for the paper's 21 blocking
  bugs.
- The local pre-validation host is not the pinned image; its results are
  labeled non-canonical everywhere they appear.
- `CGO_ENABLED=1` in the image, `0` on the pre-validation host; the bug is pure
  Go synchronization and does not involve cgo, but the setting is recorded in
  every JSONL row.
