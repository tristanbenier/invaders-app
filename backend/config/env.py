"""Load the project-wide .env file (repository root) into os.environ.

Values from .env take precedence over the shell, so variables exported for
another project (e.g. DJANGO_SETTINGS_MODULE) cannot leak into this one.
The few run switches in SHELL_OVERRIDABLE are the exception: a value given on
the command line wins (e.g. `DJANGO_VITE_DEV_MODE=False manage.py runserver`).
"""

import os
from pathlib import Path

import environ

ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"
SHELL_OVERRIDABLE = ["DJANGO_VITE_DEV_MODE"]
# Captured at import, before .env is read: later calls must not see .env values as shell ones.
_shell_values = {key: os.environ[key] for key in SHELL_OVERRIDABLE if key in os.environ}

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, []),
    CSRF_TRUSTED_ORIGINS=(list, []),
)


def load_env():
    if not ENV_FILE.exists():
        raise RuntimeError(f"Missing {ENV_FILE}: copy .env.example to .env and fill it in.")
    environ.Env.read_env(ENV_FILE, overwrite=True)
    os.environ.update(_shell_values)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
