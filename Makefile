# DeckDex MTG — Development Makefile
#
# Available targets:
#   make install      Create .venv/, install Python and npm dependencies
#   make dev          Start backend (:8000) and frontend (:5173) concurrently
#   make backend      Start backend only (uvicorn --reload)
#   make frontend     Start frontend only (npm run dev)
#   make test         Run pytest tests/
#   make db-setup     Initialize database (delegates to scripts/setup_db.sh)
#   make docker-up    Build and start full stack via Docker Compose
#   make docker-down  Stop Docker Compose services
#   make clean        Remove .venv/ and Python cache artifacts
#   make help         Show this message

.DEFAULT_GOAL := help

VENV         := .venv
PYTHON       := $(VENV)/bin/python
PIP          := $(VENV)/bin/pip
UVICORN      := $(VENV)/bin/uvicorn
FRONTEND_DIR := frontend
SYSTEM_PYTHON := $(shell command -v python3 2>/dev/null)

define PYTHON_GUARD
	@if [ -z "$(SYSTEM_PYTHON)" ]; then \
		echo "Error: python3 not found. Install Python 3.9+ and retry."; \
		exit 1; \
	fi
endef

define VENV_GUARD
	@if [ ! -f "$(PYTHON)" ]; then \
		echo "Error: venv not found. Run 'make install' first."; \
		exit 1; \
	fi
endef

.PHONY: install dev backend frontend test db-setup docker-up docker-down clean help

help:
	@echo ""
	@echo "DeckDex MTG — Development Makefile"
	@echo "======================================"
	@echo ""
	@echo "  make install      Create .venv/, install Python and npm dependencies"
	@echo "  make dev          Start backend (:8000) and frontend (:5173) concurrently"
	@echo "  make backend      Start backend only (uvicorn --reload)"
	@echo "  make frontend     Start frontend only (npm run dev)"
	@echo "  make test         Run pytest tests/"
	@echo "  make db-setup     Initialize database (delegates to scripts/setup_db.sh)"
	@echo "  make docker-up    Build and start full stack via Docker Compose"
	@echo "  make docker-down  Stop Docker Compose services"
	@echo "  make clean        Remove .venv/ and Python cache artifacts"
	@echo "  make help         Show this message"
	@echo ""

install:
	$(call PYTHON_GUARD)
	@if [ ! -d "$(VENV)" ]; then \
		echo "Creating virtual environment at $(VENV)/..."; \
		python3 -m venv $(VENV); \
	fi
	$(PIP) install --quiet --upgrade pip
	$(PIP) install --quiet -r requirements.txt
	$(PIP) install --quiet -r backend/requirements-api.txt
	cd $(FRONTEND_DIR) && npm install
	@echo "Installation complete. Run 'make dev' to start all services."

dev:
	$(call VENV_GUARD)
	@echo "Starting backend on :8000 and frontend on :5173..."
	@$(UVICORN) backend.api.main:app --reload --port 8000 & \
	BACKEND_PID=$$!; \
	trap "kill $$BACKEND_PID 2>/dev/null; wait $$BACKEND_PID 2>/dev/null" INT TERM; \
	cd $(FRONTEND_DIR) && npm run dev; \
	kill $$BACKEND_PID 2>/dev/null; \
	wait $$BACKEND_PID 2>/dev/null

backend:
	$(call VENV_GUARD)
	$(UVICORN) backend.api.main:app --reload --port 8000

frontend:
	@if [ ! -d "$(FRONTEND_DIR)/node_modules" ]; then \
		echo "Error: node_modules not found. Run 'make install' first."; \
		exit 1; \
	fi
	cd $(FRONTEND_DIR) && npm run dev

test:
	$(call VENV_GUARD)
	$(PYTHON) -m pytest tests/ -v

db-setup:
	./scripts/setup_db.sh

docker-up:
	docker compose up --build

docker-down:
	docker compose down

clean:
	rm -rf $(VENV)
	find . -type d -name __pycache__ -not -path "./.venv/*" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -not -path "./.venv/*" -delete 2>/dev/null || true
	@echo "Cleaned venv and Python cache artifacts."
