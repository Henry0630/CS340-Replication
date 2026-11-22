# grpc-793 application-level workload

Dataset row: blocking sheet row 79 (`grpc#793`), fixing commit
`5a547ed72c09faf4050739d54caea1d51f4d276d`, pre-fix checkout
`7c6103d142da5fd11a36964c3a42cf698056b00b`, patch size 1 line, cause `Mutex`,
fix `Change`. Upstream issue: [grpc/grpc-go#793](https://github.com/grpc/grpc-go/issues/793),
fixed by PR #795 ("Fix deadlock when GracefulStop()ing multiple times").

This is a **complete upstream application** workload (`workload_kind:
original_application`): the harness is compiled against the real grpc-go tree
at the pinned revision, not against a copied `GracefulStop` body.

## The bug

The pre-fix `(*Server).GracefulStop` early return takes `s.mu` a second time
instead of releasing it, so the second call self-deadlocks:

```go
s.mu.Lock()
if s.drain == true || s.conns == nil {
    s.mu.Lock() // pre-fix: deadlocks here
    return
}
```

The upstream fix changes that line to `s.mu.Unlock()`.

## Harness

`harness/main.go` creates a real server with `grpc.NewServer()`, calls
`GracefulStop()` twice, and prints `ORACLE: grpc-793 fixed: second GracefulStop
returned` only if both calls return. See [notes.md](notes.md) for provenance and
the compatibility layer.

## Requirements

- Linux with Docker, or the pinned image built locally:
  `docker build -f docker/legacy/Dockerfile -t cs340-legacy:go1.12 .`
- Inside the image: Go 1.12.17, `GO111MODULE=off`, `CGO_ENABLED=1`, git, gcc.
- Network access for the pinned dependency fetch in `build.sh`.

## Commands

From the repository root on a Docker host:

```sh
docker build -f docker/legacy/Dockerfile -t cs340-legacy:go1.12 .

bash repro/grpc-793/app/reproduce.sh --help
bash repro/grpc-793/app/reproduce.sh --variant buggy --mode symptom --runs 3 --timeout 10 \
  --output results/raw/grpc-793/app-buggy
bash repro/grpc-793/app/reproduce.sh --variant fixed --mode symptom --runs 3 --timeout 10 \
  --output results/raw/grpc-793/app-fixed
bash repro/grpc-793/app/reproduce.sh --variant buggy --mode deadlock --runs 1 --timeout 10 \
  --output results/raw/grpc-793/app-detector
```

The runner re-executes itself inside `cs340-legacy:go1.12`; set
`CS340_IN_CONTAINER=1` when invoking it inside the image (the CI job does this
by calling the script from the host).

## Expected observations

- `buggy`: the second `GracefulStop` blocks. The Go runtime may report a global
  deadlock (`deadlock_reported`, exit 2) or the external 10 s watchdog may fire
  (`timeout`, exit 124); both count as the documented symptom. The SIGQUIT stack
  is saved in `run-00N.stacks`.
- `fixed`: all three calls return; the runner records `completed` and the fixed
  control passes.
- Detector trial: records whether Go's built-in deadlock detector fired; the
  runner returns 0 whether or not it fired.

Output goes to `<output>/build.log`, `run-00N.stdout`, `run-00N.stderr`,
`run-00N.stacks`, `binary-path`, and `runs.jsonl`, as required by
[`repro/README.md`](../README.md).

## Evidence and limitations

The runner exit codes and JSONL fields follow the repository contract
(`repro/README.md`). Because this workload builds the whole application, its
detector observation is reported separately from the extracted model in
[`repro/week3-results.md`](../week3-results.md). One bug does not estimate the
paper's Table 8 coverage.
