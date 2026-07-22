# Makefile for Python Event Scheduler

.PHONY: run test clean help

# Default target
help:
	@echo "Event Scheduler Python Implementation"
	@echo ""
	@echo "Available targets:"
	@echo "  run     - Run the scheduler with default files"
	@echo "  test    - Run unit tests"
	@echo "  clean   - Clean output files"
	@echo "  help    - Show this help message"

# Run the scheduler
run:
	python main.py

# Run tests
test:
	cd .. && python -m unittest python.test_scheduler -v

# Clean output files
clean:
	rm -f output.csv output.log
	rm -rf __pycache__
	rm -rf *.pyc

# Run with custom files (example)
run-custom:
	python main.py --student custom_students.csv --judge custom_judges.csv --conference custom_conference.csv