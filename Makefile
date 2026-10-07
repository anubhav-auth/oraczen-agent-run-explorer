# One-command dev: `make dev`, then open the links it prints.
BACKEND_PORT ?= 8000
FRONTEND_PORT ?= 3000
RUNS_PATH ?= data/runs.jsonl

.PHONY: help install backend frontend dev stop test build

help:
	@echo "  make install  - pip + npm install"
	@echo "  make dev      - start backend + frontend, prints test links (Ctrl-C stops both)"
	@echo "  make backend  - FastAPI only (port $(BACKEND_PORT))"
	@echo "  make frontend - Next.js only (port $(FRONTEND_PORT))"
	@echo "  make test     - backend + frontend tests"
	@echo "  make build    - frontend production build"
	@echo "  make stop     - kill dev servers"

install:
	pip install -r backend/requirements.txt
	npm install --prefix frontend

backend:
	RUNS_PATH=$(RUNS_PATH) python -m uvicorn backend.app:app --port $(BACKEND_PORT)

frontend:
	npm run dev --prefix frontend -- --port $(FRONTEND_PORT)

dev:
	@echo ""
	@echo "  backend:  http://localhost:$(BACKEND_PORT)/api/stats  (docs: http://localhost:$(BACKEND_PORT)/docs)"
	@echo "  runs:     http://localhost:$(FRONTEND_PORT)/runs"
	@echo "  dashboard: http://localhost:$(FRONTEND_PORT)/dashboard"
	@echo ""
	trap 'kill 0' INT TERM; \
	RUNS_PATH=$(RUNS_PATH) python -m uvicorn backend.app:app --port $(BACKEND_PORT) & \
	npm run dev --prefix frontend -- --port $(FRONTEND_PORT) & \
	wait

stop:
	-pkill -f '[u]vicorn backend.app:app --port'
	-pkill -f '[n]ext-server'

test:
	pytest backend/tests -q
	npm test --prefix frontend -- --run

build:
	npm run build --prefix frontend
