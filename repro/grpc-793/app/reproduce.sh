#!/usr/bin/env bash
# Application-level reproducer for grpc/grpc-go#793 (repeated GracefulStop).
#
# Workload: the complete upstream grpc-go tree at
#   7c6103d142da5fd11a36964c3a42cf698056b00b (buggy, pre-fix)
#   5a547ed72c09faf4050739d54caea1d51f4d276d (fixed control)
# built in GOPATH mode with Go 1.12.17 inside docker/legacy.
#
# On a Docker host this script re-executes itself inside cs340-legacy:go1.12.
# Set CS340_IN_CONTAINER=1 when it already runs inside the image.
#
# Exit codes: 0 = documented symptom reproduced in every buggy trial (or every
# fixed-control trial passed); 1 = the buggy symptom was absent; 2 = invalid
# input, setup/build failure, runner failure, or a failed fixed control.
set -u

CANDIDATE_ID=grpc-793
REPOSITORY=https://github.com/grpc/grpc-go
DATASET_COMMIT=5a547ed72c09faf4050739d54caea1d51f4d276d
BUGGY_COMMIT=7c6103d142da5fd11a36964c3a42cf698056b00b
FIXED_COMMIT=5a547ed72c09faf4050739d54caea1d51f4d276d
WORKLOAD_KIND=original_application
SCHEMA_VERSION=1
IMAGE=${CS340_LEGACY_IMAGE:-cs340-legacy:go1.12}
XNET_COMMIT=6a513affb38dc9788b449d59ffed099b8de18fa0
PROTOBUF_COMMIT=c3cefd437628a0b7d31b34fe44b3a7a540e98527

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd) || {
    echo "reproduce.sh: cannot resolve the script directory" >&2
    exit 2
}
REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../../.." && pwd) || {
    echo "reproduce.sh: cannot resolve the repository root" >&2
    exit 2
}

usage() {
    cat <<'EOF'
usage: bash repro/grpc-793/app/reproduce.sh --variant buggy|fixed --mode symptom|deadlock \
         --runs N --timeout SECONDS --output DIR

Builds the complete upstream grpc-go checkout for grpc/grpc-go#793 in the
pinned legacy image (Go 1.12.17, GOPATH mode) and runs a server that calls
GracefulStop twice. Writes one JSON object per trial to DIR/runs.jsonl plus
stdout, stderr, stack, and build evidence in DIR.

exit codes: 0 symptom reproduced (or fixed control passed);
            1 symptom absent;
            2 invalid input, build, or runner failure.
EOF
}

die_usage() {
    printf 'reproduce.sh: %s\n' "$*" >&2
    usage >&2
    exit 2
}

die_setup() {
    printf 'reproduce.sh: setup/build failure: %s\n' "$*" >&2
    exit 2
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
    race) die_usage "--mode race applies to non-blocking candidates; grpc-793 is blocking" ;;
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

# ---------------------------------------------------------------------------
# Host wrapper: re-execute inside the pinned legacy image.
# ---------------------------------------------------------------------------
if [ "${CS340_IN_CONTAINER:-}" != "1" ]; then
    command -v docker >/dev/null 2>&1 ||
        die_setup "docker not found; run this inside $IMAGE, or install docker"
    IMAGE_ID=$(docker image inspect "$IMAGE" --format '{{.Id}}' 2>/dev/null || true)
    [ -n "$IMAGE_ID" ] ||
        die_setup "image $IMAGE not found; build it with: docker build -f docker/legacy/Dockerfile -t $IMAGE ."
    BASE_DIGEST=$(docker image inspect debian:bookworm-slim --format '{{index .RepoDigests 0}}' 2>/dev/null || true)
    exec docker run --rm \
        -e CS340_IN_CONTAINER=1 \
        -e CS340_IMAGE_REF="$IMAGE" \
        -e CS340_IMAGE_ID="$IMAGE_ID" \
        -e CS340_BASE_DIGEST="${BASE_DIGEST:-unknown}" \
        -v "$REPO_ROOT:/repo" -w /repo "$IMAGE" \
        bash "repro/grpc-793/app/reproduce.sh" "$@"
fi

# ---------------------------------------------------------------------------
# Inside the pinned image.
# ---------------------------------------------------------------------------
command -v go >/dev/null 2>&1 || die_setup "go not found on PATH (need Go 1.12.17 from docker/legacy)"
command -v timeout >/dev/null 2>&1 || die_setup "GNU timeout not found on PATH (coreutils)"
command -v gcc >/dev/null 2>&1 || die_setup "gcc not found on PATH (CGO_ENABLED=1)"

GO_VERSION=$(go version 2>/dev/null || echo unknown)
case "$GO_VERSION" in
    *"go1.12.17"*) ;;
    *) die_setup "expected go1.12.17 from the legacy image, got: $GO_VERSION" ;;
esac

export GO111MODULE=off
export CGO_ENABLED=${CGO_ENABLED:-1}
export GOMAXPROCS=${GOMAXPROCS:-4}

GOOS=$(go env GOOS 2>/dev/null || echo unknown)
GOARCH=$(go env GOARCH 2>/dev/null || echo unknown)
GOTOOLCHAIN=${GOTOOLCHAIN:-local}
KERNEL=$(uname -r 2>/dev/null || echo unknown)
GCC=$(gcc --version 2>/dev/null | head -1)
if [ -z "$GCC" ]; then
    GCC=unknown
fi
IMAGE_REF=${CS340_IMAGE_REF:-unknown}
IMAGE_ID=${CS340_IMAGE_ID:-unknown}
BASE_DIGEST=${CS340_BASE_DIGEST:-unknown}
HARNESS_COMMIT=$(git -C "$REPO_ROOT" rev-parse HEAD 2>/dev/null || echo unknown)
RUN_ID=$(basename -- "$OUT_DIR")
CHECKOUT_COMMIT=$BUGGY_COMMIT
if [ "$VARIANT" = "fixed" ]; then
    CHECKOUT_COMMIT=$FIXED_COMMIT
fi

mkdir -p "$OUT_DIR" || die_setup "cannot create output directory: $OUT_DIR"

BUILD_LOG=$OUT_DIR/build.log
{
    printf 'date_utc: %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
    printf 'variant: %s\n' "$VARIANT"
    printf 'go: %s\n' "$GO_VERSION"
    printf 'goos=%s goarch=%s\n' "$GOOS" "$GOARCH"
    printf 'GO111MODULE=%s GOPATH=%s\n' "${GO111MODULE:-unset}" "${GOPATH:-unset}"
    printf 'CGO_ENABLED=%s GOMAXPROCS=%s\n' "$CGO_ENABLED" "$GOMAXPROCS"
    printf 'gcc: %s\n' "$GCC"
    printf 'uname: %s\n' "$(uname -a 2>/dev/null || echo unknown)"
    printf 'image_ref: %s\n' "$IMAGE_REF"
    printf 'image_id: %s\n' "$IMAGE_ID"
    printf 'base_image_digest: %s\n' "$BASE_DIGEST"
    printf 'resolved_upstream: grpc-go %s; golang.org/x/net %s; github.com/golang/protobuf %s\n' \
        "$CHECKOUT_COMMIT" "$XNET_COMMIT" "$PROTOBUF_COMMIT"
} >"$BUILD_LOG"

bash "$SCRIPT_DIR/build.sh" "$VARIANT" "$OUT_DIR" >>"$BUILD_LOG" 2>&1
BUILD_RC=$?
if [ "$BUILD_RC" -ne 0 ]; then
    printf 'reproduce.sh: build failed for variant %s; see %s\n' "$VARIANT" "$BUILD_LOG" >&2
    exit 2
fi
BINARY=$(cat "$OUT_DIR/binary-path" 2>/dev/null || true)
[ -n "$BINARY" ] || die_setup "build produced no binary path"
[ -f "$BINARY" ] || die_setup "built binary not found: $BINARY"

# JSON-safe strings: the local pre-validation host may use backslash paths.
BINARY_JSON=${BINARY//\\//}
KERNEL_JSON=${KERNEL//\\//}
GCC_JSON=${GCC//\\//}
COMPAT_PATCHES='["golang.org/x/net@6a513affb38dc9788b449d59ffed099b8de18fa0","github.com/golang/protobuf@c3cefd437628a0b7d31b34fe44b3a7a540e98527","upstream sources unmodified"]'
COMMAND="[\"timeout\",\"-s\",\"QUIT\",\"--kill-after=2s\",\"${TIMEOUT}s\",\"${BINARY_JSON}\"]"
CONTAINER_DIGEST=null

trial=1
recorded=0
control_failed=0
reproduced=0
while [ "$trial" -le "$RUNS" ]; do
    stem=$(printf 'run-%03d' "$trial")
    stdout_path=$OUT_DIR/$stem.stdout
    stderr_path=$OUT_DIR/$stem.stderr
    stacks_path=$OUT_DIR/$stem.stacks
    started_utc=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
    start_ns=$(date +%s%N)

    timeout -s QUIT --kill-after=2s "${TIMEOUT}s" "$BINARY" >"$stdout_path" 2>"$stderr_path"
    child_rc=$?
    end_ns=$(date +%s%N)
    duration=$(awk -v s="$start_ns" -v e="$end_ns" 'BEGIN { printf "%.3f", (e - s) / 1000000000 }')

    awk '/^(error|SIGQUIT|fatal error|goroutine )/ { found = 1 } found' "$stderr_path" >"$stacks_path"

    status=completed
    if [ "$child_rc" -eq 124 ] || [ "$child_rc" -eq 137 ]; then
        status=timeout
    elif grep -q 'all goroutines are asleep - deadlock!' "$stderr_path"; then
        status=deadlock_reported
    elif [ "$child_rc" -ne 0 ]; then
        status=unexpected_failure
    elif ! grep -q '^ORACLE:' "$stdout_path"; then
        status=inconclusive
    fi

    trigger_observed=null
    detector_detected=null
    oracle_evidence=""
    if [ "$VARIANT" = "buggy" ]; then
        case "$status" in
            timeout)
                trigger_observed=true
                oracle_evidence="workload did not finish within ${TIMEOUT}s (no ORACLE line)"
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
            oracle_evidence="fixed control did not complete: status=${status}; see stderr"
        else
            oracle_evidence="fixed control completed and printed the ORACLE marker"
        fi
    fi

    if [ "$VARIANT" = "buggy" ] && [ "$trigger_observed" = true ]; then
        reproduced=$((reproduced + 1))
    fi

    printf '{"schema_version":%d,"bug":"%s","run":%d,"verdict":"%s","wall_s":%s,"candidate_id":"%s","run_id":"%s","trial":%d,"variant":"%s","mode":"%s","repository":"%s","dataset_commit":"%s","checkout_commit":"%s","workload_kind":"%s","harness_commit":"%s","compatibility_patches":%s,"environment":{"go_version":"%s","goos":"%s","goarch":"%s","gomaxprocs":%d,"cgo_enabled":"%s","gotoolchain":"%s","kernel":"%s","gcc":"%s","container_image":"%s","container_image_id":"%s","container_digest":%s,"base_image_digest":"%s"},"command":%s,"started_at_utc":"%s","duration_seconds":%s,"timeout_seconds":%d,"exit_code":%d,"timed_out":%s,"status":"%s","trigger_observed":%s,"detector_detected":%s,"oracle_evidence":"%s","artifacts":{"stdout":"%s","stderr":"%s","stacks":"%s"}}\n' \
        "$SCHEMA_VERSION" "$CANDIDATE_ID" "$trial" "$status" "$duration" \
        "$CANDIDATE_ID" "$RUN_ID" "$trial" "$VARIANT" "$MODE" \
        "$REPOSITORY" "$DATASET_COMMIT" "$CHECKOUT_COMMIT" "$WORKLOAD_KIND" \
        "$HARNESS_COMMIT" "$COMPAT_PATCHES" \
        "$GO_VERSION" "$GOOS" "$GOARCH" "$GOMAXPROCS" "$CGO_ENABLED" "$GOTOOLCHAIN" \
        "$KERNEL_JSON" "$GCC_JSON" "$IMAGE_REF" "$IMAGE_ID" "$CONTAINER_DIGEST" "$BASE_DIGEST" \
        "$COMMAND" "$started_utc" "$duration" "$TIMEOUT" "$child_rc" \
        "$([ "$status" = "timeout" ] && echo true || echo false)" \
        "$status" "$trigger_observed" "$detector_detected" "$oracle_evidence" \
        "$stem.stdout" "$stem.stderr" "$stem.stacks" >>"$OUT_DIR/runs.jsonl" ||
        { printf 'reproduce.sh: failed to record trial %d\n' "$trial" >&2; exit 2; }

    recorded=$((recorded + 1))
    printf 'reproduce.sh: trial %d/%d status=%s exit=%d duration=%ss\n' \
        "$trial" "$RUNS" "$status" "$child_rc" "$duration"
    trial=$((trial + 1))
done

if [ "$recorded" -ne "$RUNS" ]; then
    printf 'reproduce.sh: runner failure: recorded %d of %d trials\n' "$recorded" "$RUNS" >&2
    exit 2
fi
if [ "$VARIANT" = "fixed" ] && [ "$control_failed" -ne 0 ]; then
    printf 'reproduce.sh: fixed control failed; see %s\n' "$OUT_DIR" >&2
    exit 2
fi
if [ "$VARIANT" = "buggy" ] && [ "$reproduced" -ne "$RUNS" ]; then
    printf 'reproduce.sh: observed the symptom in %d/%d trials\n' "$reproduced" "$RUNS" >&2
    exit 1
fi
printf 'reproduce.sh: finished %d trial(s); evidence in %s\n' "$RUNS" "$OUT_DIR"
exit 0
