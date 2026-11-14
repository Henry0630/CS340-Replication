PY ?= python

# Base images pinned by digest (measured 2026-11-14, see docs/environment.md)
GO22 ?= golang:1.22.4-bookworm@sha256:0c02666907338370a3272af1b4642a184968911d2317f0bd010dcef89a081d6f
GO21 ?= golang:1.21.13-bookworm@sha256:c6a5b9308b3f3095e8fde83c8bf4d68bd101fce606c1a0a1394522542509dda9

.PHONY: help setup check tables env verify docker-build docker-smoke clean

help:
	@echo "make setup         - fetch and verify the pinned dataset (data/bug_table.xlsx)"
	@echo "make check         - verify the dataset hash"
	@echo "make tables        - recompute Tables 5/6/7/9/10 and compare with the paper"
	@echo "make env           - print machine/toolchain facts for docs/environment.md"
	@echo "make verify        - build both images and save the measurement to results/local/"
	@echo "make docker-build  - build the go1.22 experiment image"
	@echo "make docker-smoke  - show uname/go version inside that image"
	@echo "make clean         - drop caches and raw run logs"

setup:
	$(PY) scripts/fetch_dataset.py

check:
	$(PY) scripts/fetch_dataset.py --check

tables:
	$(PY) scripts/parse_dataset.py

env:
	$(PY) scripts/check_env.py

verify:
	bash docker/verify.sh --out results/local/env-L2-$$(hostname).md

docker-build:
	docker build --build-arg GO_IMAGE=$(GO22) -t cs340-repro:go1.22 .

docker-smoke:
	docker run --rm cs340-repro:go1.22 sh -c 'uname -a; go version; gcc --version | head -1'

clean:
	rm -rf results/raw __pycache__ scripts/__pycache__
