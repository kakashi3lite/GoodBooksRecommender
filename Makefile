# Makefile for GoodBooksRecommender project

.PHONY: setup clean test lint format pipeline prepare train monitor

# Python executable
PYTHON = python

# Virtual environment
VENV = venv
VENV_BIN = $(VENV)/Scripts

# Project directories
SRC_DIR = src
TESTS_DIR = tests
DATA_DIR = data
MODEL_DIR = models
REPORTS_DIR = reports
LOGS_DIR = logs

# Create virtual environment and install dependencies
setup:
	$(PYTHON) -m venv $(VENV)
	$(VENV_BIN)/pip install --upgrade pip
	$(VENV_BIN)/pip install -r requirements.txt

# Clean generated files and directories
clean:
	-rm -rf $(VENV)
	-rm -rf __pycache__
	-rm -rf $(SRC_DIR)/__pycache__
	-rm -rf $(TESTS_DIR)/__pycache__
	-rm -rf .pytest_cache
	-rm -rf $(LOGS_DIR)/*.log
	-rm -rf $(REPORTS_DIR)/*.json
	-rm -rf $(REPORTS_DIR)/*.png

# Run tests
test:
	$(VENV_BIN)/pytest $(TESTS_DIR) -v

# Run linting
lint:
	$(VENV_BIN)/flake8 $(SRC_DIR)
	$(VENV_BIN)/flake8 $(TESTS_DIR)

# Format code
format:
	$(VENV_BIN)/black $(SRC_DIR)
	$(VENV_BIN)/black $(TESTS_DIR)

# Run complete pipeline
pipeline:
	$(VENV_BIN)/python run_pipeline.py

# Run data preparation only
prepare:
	$(VENV_BIN)/python run_pipeline.py --steps prepare

# Run model training only
train:
	$(VENV_BIN)/python run_pipeline.py --steps train

# Run performance monitoring only
monitor:
	$(VENV_BIN)/python run_pipeline.py --steps monitor

# Create necessary directories
dirs:
	mkdir -p $(DATA_DIR)
	mkdir -p $(MODEL_DIR)
	mkdir -p $(REPORTS_DIR)
	mkdir -p $(LOGS_DIR)

# Default target
all: setup dirs test lint format

# Help target
help:
	@echo "Available targets:"
	@echo "  setup    : Create virtual environment and install dependencies"
	@echo "  clean    : Remove generated files and directories"
	@echo "  test     : Run tests"
	@echo "  lint     : Run code linting"
	@echo "  format   : Format code using black"
	@echo "  pipeline : Run complete pipeline"
	@echo "  prepare  : Run data preparation step"
	@echo "  train    : Run model training step"
	@echo "  monitor  : Run performance monitoring step"
	@echo "  dirs     : Create necessary directories"
	@echo "  all      : Run setup, create dirs, test, lint, and format"