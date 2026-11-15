# grpc-1424 — `lbWatcher` leaks the initial dial waiter when the balancer closes first

Dataset row: blocking sheet row 88 (`grpc#1424`), fixing commit
`4e56696c6c5a8cd7b711a1eb8936463559361da5`, pre-fix checkout
`39c8c3866d926d95e11c03508bf83d00f2963f91`, patch size 5 lines, cause `Chan`,
fix `Add`. Upstream fix: grpc/grpc-go commit
["Fix a goroutine leak in DialContext"](https://github.com/grpc/grpc-go/commit/4e56696c6c5a8cd7b711a1eb8936463559361da5).

## The bug

`DialContext`'s initial connection waits on `doneChan`, which `lbWatcher`
closes only when the first balancer address arrives. If the balancer's `Notify`
channel closes before any address (the resolver failed, or the balancer was
closed during dial), the for-range ends and no one ever closes `doneChan`: the
initial dial wait blocks forever and the dialer goroutine leaks.

The upstream fix adds `defer close(doneChan)` at the top of `lbWatcher`, and
`TestClientLBWatcherWithClosedBalancer` closes a blocking balancer before the
first address and expects the watcher to return.

## Harness

The extracted model keeps the pre-fix `lbWatcher` body and substitutes the
grpc transport types (`ClientConn`, `addrConn`, `balancer`, `Address`) with
local stand-ins. A `blockingBalancer` never sends an address and is closed
immediately, so the watcher's range ends while the main goroutine is still
waiting on `doneChan`. The fixed variant differs only in the deferred close.
See [notes.md](notes.md) and [patches/upstream-fix.diff](patches/upstream-fix.diff).

## Requirements

Linux, Go 1.22, GNU coreutils (`timeout`), python3, git. No Docker required;
runs are reported as extracted-model runs.

## Commands

```sh
bash repro/grpc-1424/reproduce.sh --help
bash repro/grpc-1424/reproduce.sh --variant buggy --mode deadlock --runs 3 --timeout 10 --output results/raw/grpc-1424/local-buggy
bash repro/grpc-1424/reproduce.sh --variant fixed --mode deadlock --runs 3 --timeout 10 --output results/raw/grpc-1424/local-fixed
bash repro/grpc-1424/reproduce.sh --variant buggy --mode symptom --runs 3 --timeout 10 --output results/raw/grpc-1424/local-symptom-buggy
```

## Expected observations

- `buggy`: `lbWatcher` returns without notifying the waiter; the remaining
  goroutine blocks on `doneChan`, the runtime reports
  `all goroutines are asleep - deadlock!`, and the runner records
  `deadlock_reported` (exit code 2 from the child; the runner still exits 0).
- `fixed`: the deferred close wakes the waiter, `ORACLE:` is printed, and the
  runner records `completed`.
- If the runtime does not classify the hang as a global deadlock on some Go
  version, the external 10 s watchdog fires and the status is `timeout`, also
  `trigger_observed: true`. The fixed control must still complete.

## Evidence and limitations

This is a goroutine-leak bug whose visible symptom in this extracted harness is
a blocked waiter; the runtime global-deadlock report is evidence of the missing
notification, not of a production deadlock (see [notes.md](notes.md)). The fixed
control distinguishes the bug from a harness hang.
