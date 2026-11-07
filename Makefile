PY ?= python

.PHONY: help setup check tables env docker-build docker-smoke clean

help:
	@echo "make setup         - fetch and verify the pinned dataset (data/bug_table.xlsx)"
	@echo "make check         - verify the dataset hash"
	@echo "make tables        - recompute Tables 5/6/7/9/10 and compare with the paper"
	@echo "make env           - print machine/toolchain facts for docs/environment.md"
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

docker-build:
	docker build --build-arg GO_IMAGE=golang:1.22.4-bookworm -t cs340-repro:go1.22 .

docker-smoke:
	docker run --rm cs340-repro:go1.22 sh -c 'uname -a; go version; gcc --version | head -1'

clean:
	rm -rf results/raw __pycache__ scripts/__pycache__
