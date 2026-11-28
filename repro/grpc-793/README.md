# grpc-793 — repeated `GracefulStop()` deadlocks

Dataset row: blocking sheet row 79 (`grpc#793`), fixing commit
`5a547ed72c09faf4050739d54caea1d51f4d276d`, pre-fix checkout
`7c6103d142da5fd11a36964c3a42cf698056b00b`, patch size 1 line, cause `Mutex`,
fix `Change`. Upstream issue: [grpc/grpc-go#793](https://github.com/grpc/grpc-go/issues/793),
fixed by PR #795 ("Fix deadlock when GracefulStop()ing multiple times").

## The bug

`(*Server).GracefulStop` returns early once the server is draining
(`s.drain == true || s.conns == nil`). The pre-fix early return takes `s.mu` a
second time instead of releasing it, so the second call self-deadlocks:

```go
s.mu.Lock()
if s.drain == true || s.conns == nil {
    s.mu.Lock() // pre-fix: deadlocks here
    return
}
```

The upstream fix changes that line to `s.mu.Unlock()` and adds
`TestServerGracefulStopIdempotent`, which calls `GracefulStop` three times.

## Harness

The pinned 2016 revision predates Go modules; rebuilding it with Go 1.22 would
require an unrecorded historical dependency layer. The harness is therefore an
**extracted model** (`workload_kind: extracted_model`): `GracefulStop` is
copied from `server.go` at the pre-fix commit, with the
`transport.ServerTransport` assertion replaced by a local one-method interface.
Buggy and fixed variants differ only in the upstream-fix line. Details and
deviations are in [notes.md](notes.md).

## Requirements

- Linux (CI: `ubuntu-latest`), Go 1.22, GNU coreutils (`timeout`), python3, git.
- No Docker is required. The verified-image path from `docs/env-setup.md` does
  not apply to this extracted model, and runs are reported as extracted-model
  runs, not application detector coverage.

## Commands

```sh
bash repro/grpc-793/reproduce.sh --help
bash repro/grpc-793/reproduce.sh --variant buggy --mode symptom --runs 3 --timeout 10 --output results/raw/grpc-793/local-buggy
bash repro/grpc-793/reproduce.sh --variant fixed --mode symptom --runs 3 --timeout 10 --output results/raw/grpc-793/local-fixed
bash repro/grpc-793/reproduce.sh --variant buggy --mode deadlock --runs 1 --timeout 10 --output results/raw/grpc-793/local-deadlock
```

## Expected observations

- `buggy`: every run stops on the second `GracefulStop`. In the pinned Docker
  CI run, the 10 s external watchdog expired in all three symptom trials; the
  Go runtime did not emit a global deadlock report. The runner records
  `timeout`, `trigger_observed: true`, and saves the SIGQUIT stack in
  `run-00N.stacks`.
- `fixed`: every run returns from all three calls and prints the `ORACLE:` line;
  the runner records `completed` and the fixed control passes.
- Runner exit code is 0 when the buggy symptom appears in all trials or the
  fixed control completes; 1 means the symptom is absent and 2 means failure.

Output goes to `<output>/build.log`, `run-00N.stdout`, `run-00N.stderr`,
`run-00N.stacks`, and `runs.jsonl`, as required by `repro/README.md`.

## Evidence and limitations

The trigger is deterministic and in-process. [notes.md](notes.md) records the
model extraction, the substitutions, and why the result is not application
detector coverage.

## Week-three application workload

[`app/`](app/) is the complete-upstream-application variant of this candidate
(`workload_kind: original_application`): it builds the real grpc-go tree at
`7c6103d142da5fd11a36964c3a42cf698056b00b` inside the pinned legacy image
(`docker/legacy`, Go 1.12.17), calls `GracefulStop()` twice, and has its own
`reproduce.sh`, `metadata.json`, `deps.lock`, and notes. The side-by-side
comparison with this extracted model, including the toolchain/environment
differences, is in [`../../week3-results.md`](../../week3-results.md).
