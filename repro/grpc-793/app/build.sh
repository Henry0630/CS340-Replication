#!/usr/bin/env bash
# Build the complete upstream grpc-go revisions used by the grpc-793
# application-level workload.
#
# The script runs inside the pinned legacy image (docker/legacy: Go 1.12.17,
# GOPATH mode, GO111MODULE=off) and only checks out pinned commits into a fresh
# GOPATH. No upstream source is edited.
#
# Exit codes: 0 = build OK, 2 = setup or build failure.
set -uo pipefail

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd) || {
    echo "build.sh: cannot resolve script directory" >&2
    exit 2
}

usage() {
    echo "usage: bash repro/grpc-793/app/build.sh <buggy|fixed> <output-dir>" >&2
}

VARIANT=${1:-}
OUT=${2:-}
if [ -z "$VARIANT" ] || [ -z "$OUT" ]; then
    usage
    exit 2
fi

case "$VARIANT" in
    buggy) GRPC_COMMIT=7c6103d142da5fd11a36964c3a42cf698056b00b ;;
    fixed) GRPC_COMMIT=5a547ed72c09faf4050739d54caea1d51f4d276d ;;
    *)
        echo "build.sh: unknown variant: $VARIANT" >&2
        exit 2
        ;;
esac

# Dependency layer pinned by this workload; see deps.lock and notes.md.
XNET_COMMIT=6a513affb38dc9788b449d59ffed099b8de18fa0
PROTOBUF_COMMIT=c3cefd437628a0b7d31b34fe44b3a7a540e98527

GO_VERSION_LINE=$(go version 2>/dev/null || true)
case "$GO_VERSION_LINE" in
    *"go1.12.17"*) ;;
    *)
        echo "build.sh: expected go1.12.17 in PATH, got: ${GO_VERSION_LINE:-<go missing>}" >&2
        exit 2
        ;;
esac

for tool in git gcc; do
    command -v "$tool" >/dev/null 2>&1 || {
        echo "build.sh: $tool not found in PATH" >&2
        exit 2
    }
done

export GO111MODULE=off
export CGO_ENABLED=${CGO_ENABLED:-1}
export GOMAXPROCS=${GOMAXPROCS:-4}

GOPATH_DIR=$OUT/gopath
SRC_DIR=$GOPATH_DIR/src
mkdir -p "$SRC_DIR" || exit 2

# The local pre-validation host uses a Windows Go binary; convert the path.
case "$(uname -s 2>/dev/null)" in
    MINGW*|MSYS*|CYGWIN*) GOPATH_WIN=$(cygpath -w "$GOPATH_DIR") ;;
    *) GOPATH_WIN=$GOPATH_DIR ;;
esac
export GOPATH=$GOPATH_WIN

EFFECTIVE_ENV=$OUT/effective-env.txt
{
    echo "GO111MODULE=$GO111MODULE"
    echo "GOPATH=$GOPATH"
    echo "GOROOT=$(go env GOROOT 2>/dev/null || echo unknown)"
    echo "CGO_ENABLED=$CGO_ENABLED"
    echo "GOMAXPROCS=$GOMAXPROCS"
    echo "go=$GO_VERSION_LINE"
} > "$EFFECTIVE_ENV"
cat "$EFFECTIVE_ENV"

fetch_pinned() { # import-path repository commit
    local import_path=$1 repository=$2 commit=$3
    local dest=$SRC_DIR/$import_path
    mkdir -p "$(dirname -- "$dest")"
    rm -rf "$dest"
    mkdir -p "$dest"
    (
        cd "$dest" || exit 1
        git init -q .
        git remote add origin "$repository"
        git fetch -q --depth=1 origin "$commit"
        git checkout -q FETCH_HEAD
    ) || {
        echo "build.sh: cannot fetch $import_path @ $commit" >&2
        return 1
    }
    local resolved
    resolved=$(git -C "$dest" rev-parse HEAD 2>/dev/null) || return 1
    if [ "$resolved" != "$commit" ]; then
        echo "build.sh: $import_path resolved $resolved, expected $commit" >&2
        return 1
    fi
    rm -rf "$dest/.git"
    echo "resolved $import_path @ $resolved"
}

fetch_pinned google.golang.org/grpc https://github.com/grpc/grpc-go.git "$GRPC_COMMIT" || exit 2
fetch_pinned golang.org/x/net https://github.com/golang/net.git "$XNET_COMMIT" || exit 2
fetch_pinned github.com/golang/protobuf https://github.com/golang/protobuf.git "$PROTOBUF_COMMIT" || exit 2

mkdir -p "$SRC_DIR/cs340/grpc793" || exit 2
cp "$SCRIPT_DIR/harness/main.go" "$SRC_DIR/cs340/grpc793/main.go" || exit 2

BINARY=$OUT/harness-binary
case "$(uname -s 2>/dev/null)" in
    MINGW*|MSYS*|CYGWIN*) BINARY=$OUT/harness-binary.exe ;;
esac

BINARY_ARG=$BINARY
case "$(uname -s 2>/dev/null)" in
    MINGW*|MSYS*|CYGWIN*) BINARY_ARG=$(cygpath -w "$BINARY") ;;
esac

echo "building cs340/grpc793 with $GO_VERSION_LINE"
if ! go build -o "$BINARY_ARG" cs340/grpc793; then
    echo "build.sh: go build failed" >&2
    exit 2
fi

printf '%s\n' "$BINARY" > "$OUT/binary-path" || exit 2
echo "built $BINARY"
