# grpc-793 notes — extracted model

## Provenance

- Dataset row: blocking sheet row 79, `grpc#793`; inventory record
  `blocking:gRPC:5a547ed72c09faf4050739d54caea1d51f4d276d`:
  `reproduced_flag=1`, `patch_size_lines=1`, shared-memory label, cause
  `Mutex`, fix `Change`.
- Fixing commit (dataset commit):
  `5a547ed72c09faf4050739d54caea1d51f4d276d` ("Merge pull request #795 from
  tamird/graceful-deadlock").
- Pre-fix checkout: `7c6103d142da5fd11a36964c3a42cf698056b00b` (first parent).
- Source: `server.go`, `func (s *Server) GracefulStop()`.
- Upstream regression test added by the fix: `TestServerGracefulStopIdempotent`
  calls `GracefulStop` three times.

## What was extracted

The model copies the `GracefulStop` body from the pre-fix file verbatim. The
only changes needed to compile it without the rest of grpc-go:

| Upstream expression | Model substitution |
|---|---|
| `c.(transport.ServerTransport).Drain()` | `c.(serverTransport).Drain()`, where `serverTransport` is a local one-method interface (`Drain()`) |
| `s.events trace.EventLog` | local `eventLog` interface (`Finish()`); always nil in the harness |
| `NewServer()` initialising `lis`, `conns`, `cv` | the same fields are initialised directly in `harness/*/main.go` |

The buggy and fixed variants differ only in the upstream-fix line
(`s.mu.Lock()` versus `s.mu.Unlock()` in the early-return branch). The upstream
diff is kept in [patches/upstream-fix.diff](patches/upstream-fix.diff).

## Deviations from the paper's experiment

- `workload_kind` is `extracted_model`, not `original_application`. Fewer
  goroutines exist than in a real grpc server, which can change whether the
  runtime deadlock detector classifies the hang as a global deadlock. Per
  `repro/README.md` this result must be reported separately from
  application-level detector coverage.
- The upstream regression test starts a real server and runs RPCs. This model
  creates a server with no listeners and no connections. The deadlock is in
  the idempotency path and does not depend on active RPCs.
- The 10 s timeout is a bound, not the expected latency: the buggy variant
  deadlocks immediately.

## Why not build the pinned upstream revision

The pinned revision predates Go modules (2016) and uses a historical
`golang.org/x/net` / protobuf dependency set. Reconstructing that graph with
Go 1.22 would add an unrecorded, review-heavy compatibility layer. The
contract in `repro/README.md` allows `extracted_model` provided it is stated
separately, so the dependency-free extraction is used. An application-level
run would keep the upstream checkout in `dataset-upstream/` and record its own
compatibility patches.

## Reproducer protocol

`reproduce.sh` implements the contract in `repro/README.md`: fresh output
directory, external `timeout -s QUIT --kill-after=2s` watchdog, progress
markers on stdout, one JSON object per trial, and a fixed control. The
three-run stability qualification (3/3) runs in CI
(`.github/workflows/repro.yml`).
