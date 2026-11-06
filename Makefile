# Convenience commands (Linux/macOS). On Windows run the same commands in PowerShell.
.PHONY: test snapshot dev-backend dev-frontend build

test:
	OFFLINE=1 python -m pytest -q backend/tests

snapshot:
	python -m scripts.build_snapshot

dev-backend:
	python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000

dev-frontend:
	cd frontend && npm install && npm run dev

build:
	cd frontend && npm install && npm run build
