#!/usr/bin/env bash
# Reproducer runner for the extracted grpc-go #793 model.
#
# Contract: repro/README.md. Exit 0 = every requested trial was recorded and
# classified; 2 = invalid arguments; 3 = setup/build failure; 4 = runner or
# oracle failure, or a failed fixed control.
set -u

CANDIDATE_ID="grpc-793"
REPOSITORY="https://github.com/grpc/grpc-go"
DATASET_COMMIT="5a547ed72c09faf4050739d54caea1d51f4d276d"
CHECKOUT_COMMIT="7c6103d142da5fd11a36964c3a42cf698056b00b"
FIXED_COMMIT="5a547ed72c09faf4050739d54caea1d51f4d276d"
WORKLOAD_KIND="extracted_model"
SCHEMA_VERSION="1"
REQUIRES_LINUX="no"

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd) || {
    echo "reproduce.sh: cannot resolve the script directory" >&2
    exit 3
}
HARNESS_DIR="$SCRIPT_DIR/harness"

usage() {
    cat <<'EOF'
usage: bash repro/grpc-793/reproduce.sh --variant buggy|fixed --mode symptom|deadlock \
         --runs N --timeout SECONDS --output DIR

Runs the extracted grpc-go #793 harness (repeated GracefulStop) N times and
writes one JSON object per trial to DIR/runs.jsonl, plus stdout, stderr,
stack, and build evidence in DIR.

exit codes: 0 all requested trials recorded; 2 invalid arguments;
            3 setup/build failure; 4 runner/oracle failure or failed fixed control.
EOF
}

die_usage() {
    printf 'reproduce.sh: %s\n' "$*" >&2
    usage >&2
    exit 2
}

die_setup() {
    printf 'reproduce.sh: setup/build failure: %s\n' "$*" >&2
    exit 3
}

VARIANT=""
MODE=""
RUNS=""
TIMEOUT=""
OUTPUT=""

while [ "$#" -gt 0 ]; do
    case "$1" in
        --variant)
            [ "$#" -ge 2 ] || die_usage "--variant needs a value"
            VARIANT=$2
            shift 2
            ;;
        --mode)
            [ "$#" -ge 2 ] || die_usage "--mode needs a value"
            MODE=$2
            shift 2
            ;;
        --runs)
            [ "$#" -ge 2 ] || die_usage "--runs needs a value"
            RUNS=$2
            shift 2
            ;;
        --timeout)
            [ "$#" -ge 2 ] || die_usage "--timeout needs a value"
            TIMEOUT=$2
            shift 2
            ;;
        --output)
            [ "$#" -ge 2 ] || die_usage "--output needs a value"
            OUTPUT=$2
            shift 2
            ;;
        --help|-h)
            usage
            exit 0
            ;;
        *)
            die_usage "unknown argument: $1"
            ;;
    esac
done

[ -n "$VARIANT" ] && [ -n "$MODE" ] && [ -n "$RUNS" ] && [ -n "$TIMEOUT" ] && [ -n "$OUTPUT" ] ||
    die_usage "all of --variant, --mode, --runs, --timeout and --output are required"
case "$VARIANT" in
    buggy|fixed) ;;
    *) die_usage "--variant must be buggy or fixed" ;;
esac
case "$MODE" in
    symptom|deadlock) ;;
    race) die_usage "--mode race applies to the non-blocking candidates; this is a blocking candidate" ;;
    *) die_usage "--mode must be symptom or deadlock" ;;
esac
case "$RUNS" in
    ''|*[!0-9]*) die_usage "--runs must be a positive integer" ;;
esac
[ "$RUNS" -gt 0 ] || die_usage "--runs must be a positive integer"
case "$TIMEOUT" in
    ''|*[!0-9]*) die_usage "--timeout must be a positive integer number of seconds" ;;
esac
[ "$TIMEOUT" -gt 0 ] || die_usage "--timeout must be a positive integer number of seconds"

case "$OUTPUT" in
    /*) OUT_DIR=$OUTPUT ;;
    *) OUT_DIR=$(pwd)/$OUTPUT ;;
esac
OUT_DIR=${OUT_DIR%/}
[ -n "$OUT_DIR" ] || die_usage "--output must not resolve to the filesystem root"
if [ -e "$OUT_DIR" ] && [ ! -d "$OUT_DIR" ]; then
    die_usage "--output exists and is not a directory: $OUT_DIR"
fi
if [ -d "$OUT_DIR" ] && [ -n "$(ls -A "$OUT_DIR" 2>/dev/null)" ]; then
    die_usage "refusing to reuse a nonempty output directory: $OUT_DIR"
fi

if [ "$REQUIRES_LINUX" = "yes" ] && [ "$(uname -s 2>/dev/null)" != "Linux" ]; then
    die_setup "this candidate requires Linux (child workload uses /bin/sh and dd)"
fi

command -v go >/dev/null 2>&1 || die_setup "go not found on PATH (need Go 1.22)"
command -v timeout >/dev/null 2>&1 || die_setup "GNU timeout not found on PATH (coreutils)"
command -v python3 >/dev/null 2>&1 || die_setup "python3 not found on PATH"

export GOMAXPROCS=${GOMAXPROCS:-4}
export CGO_ENABLED=${CGO_ENABLED:-1}
export GOTOOLCHAIN=${GOTOOLCHAIN:-local}

mkdir -p "$OUT_DIR" || die_setup "cannot create output directory: $OUT_DIR"

GO_VERSION=$(go version 2>/dev/null || echo unknown)
GOOS=$(go env GOOS 2>/dev/null || echo unknown)
GOARCH=$(go env GOARCH 2>/dev/null || echo unknown)
HARNESS_COMMIT=$(git -C "$SCRIPT_DIR/../.." rev-parse HEAD 2>/dev/null || echo unknown)
RUN_ID=$(basename -- "$OUT_DIR")

BUILD_LOG="$OUT_DIR/build.log"
BINARY="$OUT_DIR/harness-$VARIANT"
printf 'go: %s\nGOOS=%s GOARCH=%s\nGOMAXPROCS=%s CGO_ENABLED=%s GOTOOLCHAIN=%s\n' \
    "$GO_VERSION" "$GOOS" "$GOARCH" "$GOMAXPROCS" "$CGO_ENABLED" "$GOTOOLCHAIN" >"$BUILD_LOG"
(
    cd "$HARNESS_DIR" || exit 1
    go build -trimpath -buildvcs=false -o "$BINARY" "./$VARIANT"
) >>"$BUILD_LOG" 2>&1
BUILD_RC=$?
if [ "$BUILD_RC" -ne 0 ]; then
    printf 'reproduce.sh: build failed for variant %s; see %s\n' "$VARIANT" "$BUILD_LOG" >&2
    exit 3
fi
printf 'reproduce.sh: built %s variant at %s\n' "$VARIANT" "$BINARY"

trial=1
recorded=0
control_failed=0
while [ "$trial" -le "$RUNS" ]; do
    stem=$(printf 'run-%03d' "$trial")
    stdout_path="$OUT_DIR/$stem.stdout"
    stderr_path="$OUT_DIR/$stem.stderr"
    stacks_path="$OUT_DIR/$stem.stacks"
    started_utc=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
    start_ns=$(date +%s%N)

    timeout -s QUIT --kill-after=2s "${TIMEOUT}s" "$BINARY" >"$stdout_path" 2>"$stderr_path"
    child_rc=$?
    end_ns=$(date +%s%N)
    duration=$(awk -v s="$start_ns" -v e="$end_ns" 'BEGIN { printf "%.3f", (e - s) / 1000000000 }')

    awk '/^(error|SIGQUIT|fatal error|goroutine )/ { found = 1 } found' "$stderr_path" >"$stacks_path"

    status="completed"
    if [ "$child_rc" -eq 124 ] || [ "$child_rc" -eq 137 ]; then
        status="timeout"
    elif grep -q 'all goroutines are asleep - deadlock!' "$stderr_path"; then
        status="deadlock_reported"
    elif [ "$child_rc" -ne 0 ]; then
        status="unexpected_failure"
    elif ! grep -q '^ORACLE:' "$stdout_path"; then
        status="inconclusive"
    fi

    trigger_observed=null
    detector_detected=null
    oracle_evidence=""
    if [ "$VARIANT" = "buggy" ]; then
        case "$status" in
            timeout)
                trigger_observed=true
                oracle_evidence="workload did not finish within ${TIMEOUT}s (progress markers retained; no ORACLE line)"
                ;;
            deadlock_reported)
                trigger_observed=true
                oracle_evidence="Go runtime reported all goroutines asleep (deadlock); no ORACLE line"
                ;;
            completed|inconclusive)
                trigger_observed=false
                oracle_evidence="workload returned without the documented symptom"
                ;;
            *)
                trigger_observed=false
                oracle_evidence="unexpected failure before the documented symptom"
                ;;
        esac
        if [ "$MODE" = "deadlock" ]; then
            if [ "$status" = "deadlock_reported" ]; then
                detector_detected=true
            else
                detector_detected=false
            fi
        fi
    else
        trigger_observed=false
        if [ "$MODE" = "deadlock" ]; then
            detector_detected=false
        fi
        if [ "$status" != "completed" ]; then
            control_failed=1
            oracle_evidence="fixed control did not complete: status=$status; see stderr"
        else
            oracle_evidence="fixed control completed and printed the ORACLE marker"
        fi
    fi

    SCHEMA_VERSION="$SCHEMA_VERSION" CANDIDATE_ID="$CANDIDATE_ID" RUN_ID="$RUN_ID" \
    TRIAL="$trial" VARIANT="$VARIANT" MODE="$MODE" REPOSITORY="$REPOSITORY" \
    DATASET_COMMIT="$DATASET_COMMIT" CHECKOUT_COMMIT="$CHECKOUT_COMMIT" \
    FIXED_COMMIT="$FIXED_COMMIT" WORKLOAD_KIND="$WORKLOAD_KIND" \
    HARNESS_COMMIT="$HARNESS_COMMIT" GO_VERSION="$GO_VERSION" GOOS="$GOOS" \
    GOARCH="$GOARCH" GOMAXPROCS="$GOMAXPROCS" CGO_ENABLED="$CGO_ENABLED" \
    GOTOOLCHAIN="$GOTOOLCHAIN" STARTED="$started_utc" DURATION="$duration" \
    TIMEOUT="$TIMEOUT" CHILD_RC="$child_rc" STATUS="$status" \
    TRIGGER="$trigger_observed" DETECTOR="$detector_detected" \
    EVIDENCE="$oracle_evidence" STDOUT_REL="$stem.stdout" \
    STDERR_REL="$stem.stderr" STACKS_REL="$stem.stacks" OUT_DIR="$OUT_DIR" \
    python3 - <<'PY' || { echo "reproduce.sh: failed to record trial $trial" >&2; exit 4; }
import json
import os


def env(name):
    return os.environ[name]


def maybe_bool(name):
    value = os.environ[name]
    if value == "null":
        return None
    return value == "true"


record = {
    "schema_version": int(env("SCHEMA_VERSION")),
    "candidate_id": env("CANDIDATE_ID"),
    "run_id": env("RUN_ID"),
    "trial": int(env("TRIAL")),
    "variant": env("VARIANT"),
    "mode": env("MODE"),
    "repository": env("REPOSITORY"),
    "dataset_commit": env("DATASET_COMMIT"),
    "checkout_commit": env("CHECKOUT_COMMIT"),
    "workload_kind": env("WORKLOAD_KIND"),
    "harness_commit": env("HARNESS_COMMIT"),
    "compatibility_patches": [
        "harness: extracted model, see notes.md",
        "harness/go.mod: module-mode wrapper for the extracted package",
    ],
    "environment": {
        "go_version": env("GO_VERSION"),
        "goos": env("GOOS"),
        "goarch": env("GOARCH"),
        "gomaxprocs": int(env("GOMAXPROCS")),
        "cgo_enabled": env("CGO_ENABLED"),
        "gotoolchain": env("GOTOOLCHAIN"),
        "container_image": None,
        "container_digest": None,
    },
    "command": [
        "timeout", "-s", "QUIT", "--kill-after=2s", env("TIMEOUT") + "s",
        os.path.join(env("OUT_DIR"), "harness-" + env("VARIANT")),
    ],
    "started_at_utc": env("STARTED"),
    "duration_seconds": float(env("DURATION")),
    "timeout_seconds": int(env("TIMEOUT")),
    "exit_code": int(env("CHILD_RC")),
    "timed_out": env("CHILD_RC") in ("124", "137"),
    "status": env("STATUS"),
    "trigger_observed": maybe_bool("TRIGGER"),
    "detector_detected": maybe_bool("DETECTOR"),
    "oracle_evidence": env("EVIDENCE"),
    "artifacts": {
        "stdout": env("STDOUT_REL"),
        "stderr": env("STDERR_REL"),
        "stacks": env("STACKS_REL"),
    },
}
with open(os.path.join(env("OUT_DIR"), "runs.jsonl"), "a", encoding="utf-8") as handle:
    handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
PY

    recorded=$((recorded + 1))
    printf 'reproduce.sh: trial %d/%d status=%s exit=%d duration=%ss\n' \
        "$trial" "$RUNS" "$status" "$child_rc" "$duration"
    trial=$((trial + 1))
done

if [ "$recorded" -ne "$RUNS" ]; then
    printf 'reproduce.sh: runner failure: recorded %d of %d trials\n' "$recorded" "$RUNS" >&2
    exit 4
fi
if [ "$VARIANT" = "fixed" ] && [ "$control_failed" -ne 0 ]; then
    printf 'reproduce.sh: fixed control failed; see %s\n' "$OUT_DIR" >&2
    exit 4
fi
printf 'reproduce.sh: finished %d trial(s); evidence in %s\n' "$RUNS" "$OUT_DIR"
exit 0
