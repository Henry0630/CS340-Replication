# syntax=docker/dockerfile:1
#
# Experiment image for the L2 reproduction (rebuild buggy Go programs, run the
# built-in deadlock detector and the `-race` data-race detector).
#
# Why a container: the "Reproducibility and Environment" criterion (25%) needs a
# clean machine to rebuild the experiments from the README alone, with OS,
# kernel, compiler and tool versions pinned. This file is that pin.
#
# Build (Go 1.22 — the version used for the main reproduction):
#   docker build --build-arg GO_IMAGE=golang:1.22.4-bookworm -t cs340-repro:go1.22 .
#
# Build (Go 1.21 — same image, only the language version differs; this pair is
# the one-factor comparison used by the Extension):
#   docker build --build-arg GO_IMAGE=golang:1.21.13-bookworm -t cs340-repro:go1.21 .
#
# Run:
#   docker run --rm cs340-repro:go1.22 sh -c 'uname -a; go version'
#   docker run --rm -v "$PWD/repro/<bug>:/work" -w /work cs340-repro:go1.22 ./reproduce.sh
#
# NOTE (must be done on a machine that has Docker, then committed):
#   docker image inspect cs340-repro:go1.22 --format '{{index .RepoDigests 0}}'
# and pin the base image by that digest below, so the image is byte-reproducible
# even if the tag is re-pointed upstream.

ARG GO_IMAGE=golang:1.22.4-bookworm
FROM ${GO_IMAGE}

ARG DEBIAN_FRONTEND=noninteractive

# The kernel is inherited from the host; record it in the report with
#   docker run --rm cs340-repro:go1.22 uname -a
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      build-essential gcc libc6-dev \
      git curl ca-certificates \
      python3 time procps jq less \
 && rm -rf /var/lib/apt/lists/*

# Determinism knobs.
#   GOMAXPROCS  fixed so goroutine schedules are comparable across runs
#   GOTOOLCHAIN=local prevents Go from silently downloading a different
#               toolchain than the one pinned by the base image
#   CGO_ENABLED=1 the race detector needs cgo
ENV CGO_ENABLED=1 \
    GOMAXPROCS=4 \
    GOTOOLCHAIN=local \
    GOFLAGS=-mod=mod \
    TZ=UTC

WORKDIR /work

# Build-time smoke test: proves the image can compile with cgo and the race
# detector and run a goroutine/channel program. A failing build here means the
# image is unusable, so no experiment runs against it.
COPY docker/smoke /tmp/smoke
RUN cd /tmp/smoke \
 && go build -race -o /tmp/smoke/smoke ./... \
 && /tmp/smoke/smoke \
 && go version \
 && rm -rf /tmp/smoke

CMD ["bash"]
