# docker-256 — `CmdStream` deadlocks when a command writes a lot to stderr

Dataset row: blocking sheet row 18 (`moby#256`), fixing commit
`58befe3081726ef74ea09198cd9488fb42c51f51`, pre-fix checkout
`1d6929c8bc6cbc5ad63dce083869460b6bb377ad`, patch size 8 lines, cause
`MessagingLib`, fix `Add`. Upstream fix: moby/moby commit
["Fix a deadlock in CmdStream"](https://github.com/moby/moby/commit/58befe3081726ef74ea09198cd9488fb42c51f51).

## The bug

`CmdStream` starts the child, then copies stdout into an `io.Pipe` in a
goroutine. Only after stdout reaches EOF does that goroutine read stderr and
call `cmd.Wait()`. If the child writes enough stderr to fill the pipe buffer, the
child blocks on stderr, the helper goroutine blocks reading stdout, and the
caller blocks reading the pipe: a three-way deadlock.

The upstream fix adds a second goroutine that drains stderr concurrently and
hands it to the stdout goroutine, and adds `TestCmdStreamLargeStderr` using
`dd if=/dev/zero bs=1k count=1000 of=/dev/stderr; echo hello`.

## Harness

The 2013 Docker tree predates Go modules and cannot be rebuilt dependency-free
with Go 1.22. The harness is an **extracted model** (`workload_kind:
extracted_model`): `CmdStream` is reconstructed from the upstream fix diff
(the diff is the source of truth in [patches/upstream-fix.diff](patches/upstream-fix.diff)),
and the buggy/fixed variants differ exactly in the upstream fix. Details in
[notes.md](notes.md).

The model requires Linux (`/bin/sh`, `dd`, process pipes); it is rejected with
exit 2 on other platforms.

## Requirements

- Linux (CI: `ubuntu-latest`), Go 1.22, GNU coreutils (`timeout`), python3, git.
- No Docker required; runs are reported as extracted-model runs.

## Commands

```sh
bash repro/docker-256/reproduce.sh --help
bash repro/docker-256/reproduce.sh --variant buggy --mode symptom --runs 3 --timeout 10 --output results/raw/docker-256/local-buggy
bash repro/docker-256/reproduce.sh --variant fixed --mode symptom --runs 3 --timeout 10 --output results/raw/docker-256/local-fixed
bash repro/docker-256/reproduce.sh --variant buggy --mode deadlock --runs 1 --timeout 10 --output results/raw/docker-256/local-deadlock
```

## Expected observations

- `buggy`: the child fills the stderr pipe, the helper blocks on stdout, and the
  harness blocks reading stdout. The external watchdog fires: status `timeout`
  (exit 124), `trigger_observed: true`, and `run-00N.stacks` contains the
  SIGQUIT goroutine dump showing the blocked read.
- `fixed`: the child drains stderr, `echo hello` completes stdout, `CmdStream`
  returns EOF, the harness prints `ORACLE:`, and the runner records `completed`.
- Runner exit code is 0 when the buggy symptom appears in all trials or the
  fixed control completes; 1 means the symptom is absent and 2 means failure.

## Evidence and limitations

The deadlock is deterministic under the documented workload. The timeout is the
symptom bound (10 s), not the expected runtime. See [notes.md](notes.md) for the
extraction and observation caveats.
