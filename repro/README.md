# Reproducer specification

Owner: Haotong Xie (1230022122), role C.

Week 1 delivers the [candidate selection](../docs/candidates.md) and this
implementation contract. No per-bug executable, build success, experiment log,
or detector result is claimed yet. The commands below define the interface
that each week-two reproducer must implement.

## Directory layout

```text
repro/<candidate-id>/
  README.md          # Provenance, exact trigger, oracle, limits, and commands
  metadata.json      # Repository, full fixing/pre-fix SHAs, inventory row
  reproduce.sh       # Entry point, LF line endings, executable Git mode
  patches/           # Documented harness or compatibility changes, if needed
  harness/           # Minimal driver or package-level regression test
results/raw/<candidate-id>/<run-id>/
  build.log
  run-001.stdout
  run-001.stderr
  run-001.stacks
  runs.jsonl
```

The upstream checkout belongs in the ignored `dataset-upstream/` directory.
Record every compatibility patch; never replace a pinned revision with an
unrecorded newer version. Do not commit binaries, upstream clones, or raw logs.
The existing `.gitignore` permits a small `repro/<candidate-id>/runs.jsonl`
summary if needed later; do not put full stdout/stderr in that tracked summary.

## Prerequisites and provenance

- Run L2 on Linux using B's verified experiment environment. The repository
  currently declares its image unverified; building it and recording its actual
  digest/toolchain/kernel are prerequisites for experiments, not completed work.
- Use the candidate's full pre-fix SHA for the buggy variant and its full fixing
  SHA for the fixed control. Verify checkout identity with `git rev-parse HEAD`.
- Record Go/compiler/OS/kernel versions, container image ID and base digest,
  `GOMAXPROCS=4`, `CGO_ENABLED=1`, and `GOTOOLCHAIN=local` from actual runs.
- Pin dependencies. If historical code needs GOPATH mode, vendoring, or changes
  to compile, document the exact procedure and keep synchronization unchanged.
- Identify the workload as `original_application`, `upstream_package_test`, or
  `extracted_model`. Report extracted-model results separately from application
  detector coverage; changing runnable goroutines can change deadlock detection.

## Command-line contract

Every future `reproduce.sh` must support these invocations from any directory:

```sh
bash repro/<candidate-id>/reproduce.sh --help
bash repro/<candidate-id>/reproduce.sh --variant buggy --mode symptom --runs 3 --timeout 10 --output results/raw/<candidate-id>/<run-id>
bash repro/<candidate-id>/reproduce.sh --variant fixed --mode symptom --runs 3 --timeout 10 --output results/raw/<candidate-id>/<control-id>
bash repro/<candidate-id>/reproduce.sh --variant buggy --mode deadlock --runs 1 --timeout 10 --output results/raw/<candidate-id>/<detector-id>
```

For a later non-blocking candidate, `--mode race --runs 100` compiles with
`-race` and executes the same workload 100 times. This first shortlist contains
blocking bugs only and is not a Table 12 sample. The timeout is seconds per
execution after compilation; 10 seconds is an initial setting to calibrate and
record, not a universal threshold. Use a separate bounded build step.

Required options: `--variant buggy|fixed`, `--mode symptom|deadlock|race`,
`--runs` (positive integer), `--timeout` (positive seconds), and `--output`.
`--help` must work without Go or Docker. Resolve source paths relative to the
script, quote paths, validate options before running commands, and do not use
hard-coded machine paths or `eval` to execute assembled shell strings.

Use a fresh output directory; refuse a nonempty destination. Do not erase an
earlier run. Run the workload under an external watchdog with a kill grace
period (for example, GNU `timeout --kill-after=2s`). Capture the child exit code
before shell error handling can discard it. Stop only processes owned by this
run; do not clean arbitrary Docker containers, directories, or user services.

## Result classification

Record trigger and detector outcomes independently. A timeout is evidence of
noncompletion, not sufficient evidence of the specific bug.

| Observation | Required interpretation |
|---|---|
| Build/dependency failure | `build_failed`; not a triggered bug or a detector miss |
| Expected operation completes | `completed`; evaluate the candidate-specific oracle |
| Time limit reached | `timeout`; inspect progress markers/stacks and fixed control |
| Runtime deadlock report | `deadlock_reported`; verify it matches the target bug |
| Race report | `race_reported`; associate reported locations with the target bug |
| Other crash/panic | `unexpected_failure` unless the documented oracle expects it |
| Insufficient evidence | `inconclusive`; do not silently count it as reproduced |

For channel notifications and goroutine leaks, explicitly observe the operation
that should finish. A Go program may exit despite leaked goroutines. Conversely,
adding a blocked main goroutine can manufacture a global-deadlock condition.
Keep observation out of process where possible and document any observer that
changes the goroutine population. Keep compiler timeouts separate from run
timeouts. A fixed control must complete correctly under the same input; if it
also hangs, investigate the harness/environment before accepting the result.

The runner returns 0 when all requested trials are recorded and classified,
including trials where the target did not reproduce. Exit 2 means invalid
arguments, 3 means setup/build failure, and 4 means a runner/oracle failure or a
failed fixed control. Child exit codes remain in the log; do not equate wrapper
success with successful bug reproduction.

## Log fields

Write one JSON object per trial to `runs.jsonl`. Required fields are:

- `schema_version`, `candidate_id`, `run_id`, `trial`, `variant`, `mode`;
- `repository`, `dataset_commit`, `checkout_commit`, `workload_kind`,
  `harness_commit`, and any applied compatibility-patch identifiers;
- actual environment versions/digests and concurrency settings;
- `command` as an argument array, `started_at_utc`, `duration_seconds`,
  `timeout_seconds`, `exit_code`, and `timed_out`;
- `status`, `trigger_observed`, `detector_detected`, `oracle_evidence`,
  and relative paths to stdout, stderr, and stack evidence.

Unknown outcomes are JSON null, not false or zero. Preserve unsuccessful trials
and the planned denominator. Do not create illustrative files that resemble
measured results. Report successful-run timing as mean and standard deviation
only when enough comparable observations exist; list timeouts/failures apart.

## Experimental protocol and acceptance

The [paper](https://songlh.github.io/paper/go-study.pdf), Section 5.3, used one
detector run per deterministically triggered blocking bug. Our team adds a
three-run stability qualification: require 3/3 symptom matches before the
detector experiment. Record this extra qualification as our procedure.

For Section 6.3 / Table 12, execute each selected non-blocking workload 100
times with `-race`, retain all trials, and count a bug as detected if at least
one matching report occurs. Report per-run hits separately from per-bug coverage.
Do not generalize coverage from the ten blocking candidates to all 41 paper
experiments or fill in missing runs with assumed outcomes.

A week-two reproducer is accepted only after its pinned source builds, its
documented symptom is observed with evidence, the fixed control passes, and
the relevant repeatability/detector protocol is logged. Week-one source
inspection and skeleton plans alone do not satisfy that runtime acceptance.
