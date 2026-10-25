.PHONY: dev build hooks lan

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

# Test on another device of the local network (e.g. a phone): built app served by Django on
# 0.0.0.0:8000. Plain HTTP: geolocation, service worker and app install need HTTPS and stay off.
# The Mac's IP must be in ALLOWED_HOSTS and CSRF_TRUSTED_ORIGINS (.env).
lan:
	@npm --prefix frontend run build --silent >/dev/null
	@IP=$$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "<Mac IP>"); \
	grep -Eq "^ALLOWED_HOSTS=.*$$IP" .env || echo "Warning: add $$IP to ALLOWED_HOSTS and http://$$IP:8000 to CSRF_TRUSTED_ORIGINS in .env."; \
	echo; echo "  On a device of the same network: http://$$IP:8000"; echo; \
	cd backend && DJANGO_VITE_DEV_MODE=False exec .venv/bin/python manage.py runserver 0.0.0.0:8000

