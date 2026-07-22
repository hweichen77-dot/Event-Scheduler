# Event Scheduler - Multi-language Implementation
# Makefile for both Go and Python versions

.PHONY: help go-build go-run go-test python-run python-test clean-all

# Default target
help:
	@echo "Event Scheduler - Multi-language Implementation"
	@echo ""
	@echo "Go targets:"
	@echo "  go-build    - Build Go binary"
	@echo "  go-run      - Run Go implementation"
	@echo "  go-test     - Run Go tests"
	@echo ""
	@echo "Python targets:"
	@echo "  python-run  - Run Python implementation"
	@echo "  python-test - Run Python tests"
	@echo ""
	@echo "Utility targets:"
	@echo "  clean-all   - Clean all output files"
	@echo "  help        - Show this help message"

# Go targets
go-build:
	cd cmd/real && go build

go-run: go-build
	cd cmd/real && ./real

go-test:
	go test ./tests/...

# Python targets
python-run:
	cd python && python main.py

python-test:
	python -m unittest python.test_scheduler -v

# Clean targets
clean-all:
	rm -f cmd/real/real
	rm -f cmd/real/output.csv
	rm -f cmd/real/output.log
	rm -f python/output.csv
	rm -f python/output.log
	rm -rf python/__pycache__
	@echo "Cleaned all output files"