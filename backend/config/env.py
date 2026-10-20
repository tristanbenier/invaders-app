"""Load the project-wide .env file (repository root) into os.environ.

Values from .env take precedence over the shell, so variables exported for
another project (e.g. DJANGO_SETTINGS_MODULE) cannot leak into this one.
"""

import os
from pathlib import Path

import environ

ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, []),
    CSRF_TRUSTED_ORIGINS=(list, []),
)


def load_env():
    if not ENV_FILE.exists():
        raise RuntimeError(f"Missing {ENV_FILE}: copy .env.example to .env and fill it in.")
    environ.Env.read_env(ENV_FILE, overwrite=True)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
