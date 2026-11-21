# syntax=docker/dockerfile:1
#
# Legacy toolchain image: builds pre-modules (GOPATH-era) upstream revisions —
# the 2015–2018 code the paper studied — without patching them by hand.
#
# Why a second image instead of reusing the Go 1.22 one: those revisions predate
# Go modules and were written for GOPATH + vendored `Godeps`/`vendor/`. Go 1.22
# refuses such trees (and older trees use APIs that changed). So this image pins
# an old toolchain, and `build_legacy.sh` reconstructs the GOPATH layout from a
# manifest instead of asking anyone to run `go get` by hand.
#
# Build:
#   docker build -f docker/legacy/Dockerfile -t cs340-legacy:go1.12 .
#
# Run (inside the repo):
#   docker run --rm -v "$PWD/docker/legacy:/cfg:ro" cs340-legacy:go1.12 \
#     /usr/local/bin/build_legacy.sh /cfg/manifest
#
# The toolchain tarball is pinned by sha256 (from https://go.dev/dl/?mode=json),
# so a silently retagged download cannot change the compiler under us.

FROM debian:bookworm-slim

ARG GO_VERSION=1.12.17
ARG GO_SHA256=a53dd476129d496047487bfd53d021dd17e0c96895865a0e7d0469ce3db8c8d2
ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      ca-certificates curl git tar \
      build-essential gcc libc6-dev make pkg-config \
 && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL "https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz" -o /tmp/go.tgz \
 && echo "${GO_SHA256}  /tmp/go.tgz" | sha256sum -c - \
 && tar -C /usr/local -xzf /tmp/go.tgz \
 && rm -f /tmp/go.tgz

# GOPATH mode, exactly what these revisions expect. CGO on, because the paper's
# deadlock detectors and some dependencies need it.
ENV PATH=/usr/local/go/bin:/work/gopath/bin:$PATH \
    GOPATH=/work/gopath \
    GO111MODULE=off \
    CGO_ENABLED=1 \
    TZ=UTC

RUN go version && mkdir -p /work/gopath/src /work/gopath/bin

COPY docker/legacy/build_legacy.sh /usr/local/bin/build_legacy.sh
RUN chmod +x /usr/local/bin/build_legacy.sh

WORKDIR /work
CMD ["bash"]
