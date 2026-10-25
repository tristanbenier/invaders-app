.PHONY: dev build hooks

# Django (http://localhost:8000) and the Vite dev server together; Ctrl+C stops both.
dev:
	@trap 'kill 0' INT TERM EXIT; \
	(cd backend && .venv/bin/python manage.py runserver) & \
	npm --prefix frontend run dev & \
	wait

# Type check and build the Vue app into frontend/dist (committed: production serves it as is).
build:
	npm --prefix frontend run build

# Enable the repository git hooks (.githooks/pre-commit checks that frontend/dist is up to date).
hooks:
	git config core.hooksPath .githooks
