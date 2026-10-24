.PHONY: dev

# Django (http://localhost:8000) and the Vite dev server together; Ctrl+C stops both.
dev:
	@trap 'kill 0' INT TERM EXIT; \
	(cd backend && .venv/bin/python manage.py runserver) & \
	npm --prefix frontend run dev & \
	wait
