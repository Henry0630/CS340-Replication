# grpc-1424 notes — extracted model

## Provenance

- Dataset row: blocking sheet row 88, `grpc#1424`; inventory record
  `blocking:gRPC:4e56696c6c5a8cd7b711a1eb8936463559361da5`:
  `reproduced_flag=1`, `patch_size_lines=5`, shared-memory label, cause `Chan`,
  fix `Add`.
- Fixing commit (dataset commit):
  `4e56696c6c5a8cd7b711a1eb8936463559361da5` ("Fix a goroutine leak in
  DialContext (#1424)").
- Pre-fix checkout: `39c8c3866d926d95e11c03508bf83d00f2963f91` (first parent).
- Source: `clientconn.go`, `func (cc *ClientConn) lbWatcher(doneChan chan struct{})`.
- Upstream regression test added by the fix:
  `TestClientLBWatcherWithClosedBalancer`.

## What was extracted

The harness copies the `lbWatcher` loop from the pre-fix file and substitutes
the transport types so the package builds without the repository:

| Upstream expression | Model substitution |
|---|---|
| `cc.dopts.balancer.Notify()` / `balancer.Close()` | local `balancer` interface and `blockingBalancer` double |
| `Address` (protobuf-generated) | local struct with `Addr`, `Type`, `Metadata` |
| `addrConn`, `resetAddrConn`, `tearDown` | minimal local stand-ins with the same call shapes |
| `cc.mu`, `cc.conns` | the same fields and locking as the pre-fix code |

The buggy and fixed variants differ only in the upstream-fix deferred block:

```go
defer func() {
    if doneChan != nil {
        close(doneChan)
    }
}()
```

The upstream diff is kept in `patches/upstream-fix.diff`.

## Deviations from the paper's experiment

- `workload_kind` is `extracted_model`, not `original_application`. A real
  `DialContext` run needs the full grpc-go tree and its dependency graph, so the
  exact buggy function is isolated. Per `repro/README.md` this result is
  reported separately from application-level detector coverage.
- The real bug is a goroutine leak, not a deadlock: `DialContext` can still
  return via context cancellation and the waiter stays blocked. The harness
  intentionally blocks the last goroutine, so the Go runtime reports a global
  deadlock; that report is used as evidence that the notification was never
  delivered. The fixed control proves the harness is not simply hanging.
- The harness closes the balancer before the watcher can receive a first
  address, which is the upstream test's scenario. It does not model a DNS
  resolver, an LB policy update, or a reconnect.
- The 10 s external bound is a calibration; the buggy variant normally exits in
  well under a second through the runtime detector.

## Reproducer protocol

`reproduce.sh` implements the contract in `repro/README.md`: fresh output
directory, external watchdog, progress markers on stdout, one JSON object per
trial, and a fixed control. The three-run stability qualification (3/3) runs in
CI (`.github/workflows/repro.yml`).
