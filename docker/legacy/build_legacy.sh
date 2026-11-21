#!/usr/bin/env bash
# Reconstruct a GOPATH workspace for pre-modules upstream revisions and build them.
#
# Input: a manifest (default /cfg/manifest), one entry per line:
#     <import-path> <git-ref> [# comment]
# e.g.
#     github.com/boltdb/bolt v1.3.1
#
# For each entry the repository is cloned into $GOPATH/src/<import-path> at the
# pinned ref, the resolved commit is printed (so the report can cite an exact
# SHA even when the manifest names a tag), and `go build ./...` runs with
# GO111MODULE=off. Nothing is edited: if a revision does not build, the script
# fails loudly instead of patching sources.
#
# Exit codes: 0 = every entry built, 1 = a build failed, 2 = bad usage/manifest.
set -uo pipefail

MANIFEST="${1:-/cfg/manifest}"
[ -f "$MANIFEST" ] || { echo "manifest not found: $MANIFEST"; exit 2; }
command -v go >/dev/null || { echo "go not in PATH"; exit 2; }

work="${GOPATH:-/work/gopath}/src"
mkdir -p "$work"
status=0
built=0

echo "# Legacy (pre-modules) build report"
echo
echo "- go: \`$(go version)\`"
echo "- GO111MODULE: \`${GO111MODULE:-unset}\`"
echo "- GOPATH: \`${GOPATH}\`"
echo "- CGO_ENABLED: \`${CGO_ENABLED:-unset}\`"
echo "- gcc: \`$(gcc --version | head -1)\`"
echo

while read -r import_path ref rest; do
  case "${import_path:-}" in
    ""|\#*) continue ;;
  esac
  [ -n "${ref:-}" ] || { echo "- $import_path: **missing ref**, skipped"; status=1; continue; }

  dest="$work/$import_path"
  echo "## $import_path @ $ref"

  if [ -d "$dest/.git" ]; then
    git -C "$dest" fetch --tags --quiet origin || true
  else
    mkdir -p "$(dirname "$dest")"
    rm -rf "$dest"
    # The import path usually already starts with the host (github.com/owner/repo).
    case "$import_path" in
      *.*/*) url="https://${import_path}.git" ;;
      *)     url="https://github.com/${import_path}.git" ;;
    esac
    git clone --quiet "$url" "$dest" || {
      echo "- clone \`$url\`: **FAILED**"; status=1; continue; }
  fi

  git -C "$dest" checkout --quiet "$ref" 2>/dev/null || {
    echo "- checkout \`$ref\`: **FAILED**"; status=1; continue; }

  sha="$(git -C "$dest" rev-parse HEAD)"
  date="$(git -C "$dest" show -s --format=%ad --date=short HEAD)"
  has_mod=no
  [ -f "$dest/go.mod" ] && has_mod=yes
  echo "- resolved commit: \`$sha\` ($date)"
  echo "- pre-modules: $([ "$has_mod" = no ] && echo yes || echo 'no go.mod found — not legacy')"
  echo "- head subject: $(git -C "$dest" show -s --format=%s HEAD)"

  if ( cd "$dest" && go build ./... ); then
    echo "- build: **OK**"
    built=$((built + 1))
  else
    echo "- build: **FAILED**"
    status=1
  fi
  echo
done < "$MANIFEST"

echo "---"
if [ "$status" -eq 0 ]; then
  echo "LEGACY BUILD OK ($built entries)"
else
  echo "LEGACY BUILD FAILED"
fi
exit "$status"
