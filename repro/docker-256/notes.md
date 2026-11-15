# docker-256 notes — extracted model

## Provenance

- Dataset row: blocking sheet row 18, `moby#256`; inventory record
  `blocking:Docker:58befe3081726ef74ea09198cd9488fb42c51f51`:
  `reproduced_flag=1`, `patch_size_lines=8`, message-passing label, cause
  `MessagingLib`, fix `Add`.
- Fixing commit (dataset commit):
  `58befe3081726ef74ea09198cd9488fb42c51f51` ("Fix a deadlock in CmdStream").
  Its parent, used for the buggy variant, is
  `1d6929c8bc6cbc5ad63dce083869460b6bb377ad`.
- Source: `archive.go`, `func CmdStream(cmd *exec.Cmd) (io.Reader, error)`.
- Upstream regression test added by the fix: `TestCmdStreamLargeStderr`.

## What was extracted

`CmdStream` is reconstructed from the upstream fix diff: the removed lines give
the pre-fix order (copy stdout, then `ReadAll(stderr)`, then `Wait`), and the
added lines give the fixed two-goroutine version. The surrounding Docker types
are not needed: the function only uses `io`, `io/ioutil`, `errors`, and
`os/exec`.

The buggy and fixed harnesses share the same workload and differ exactly in the
upstream fix:

| Pre-fix (buggy) | Post-fix (fixed) |
|---|---|
| one goroutine: `io.Copy(pipeW, stdout)` then `ioutil.ReadAll(stderr)` then `cmd.Wait()` | stderr is drained by a second goroutine and sent over `errChan`; the stdout goroutine waits for it before `cmd.Wait()` |

The upstream diff is kept in `patches/upstream-fix.diff`.

## Deviations from the paper's experiment

- `workload_kind` is `extracted_model`, not `original_application`. The upstream
  2013 Docker daemon cannot be rebuilt at the pinned revision with a
  dependency-free Go 1.22 toolchain, so the exact buggy function is isolated
  instead. This is reported separately from application-level detector
  coverage, as `repro/README.md` requires.
- The workload is the upstream regression input (`dd ... of=/dev/stderr; echo
  hello`). The observable oracle is that the caller reaches stdout EOF; the
  harness blocks before that point in the buggy variant.
- In the buggy variant the hang involves a child process and a goroutine blocked
  in a pipe read, so the Go runtime may not classify it as a global deadlock.
  The runner uses an external `timeout -s QUIT --kill-after=2s` bound and
  treats the timeout as the documented symptom, keeping the stack dump as
  evidence. A timeout alone is not counted as proof of the specific bug; the
  fixed control must also complete.
- The 10 s bound is calibration for this deterministic workload, not a claim
  about all blocking bugs.

## Reproducer protocol

`reproduce.sh` implements the contract in `repro/README.md`: fresh output
directory, external watchdog, progress markers on stdout, one JSON object per
trial, and a fixed control. The three-run stability qualification (3/3) runs in
CI (`.github/workflows/repro.yml`).
