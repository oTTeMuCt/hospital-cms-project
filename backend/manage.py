#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from pathlib import Path


def _load_env() -> None:
    """Load .env files from project root and backend directory."""
    from dotenv import load_dotenv

    # Load from project root first (docker-compose style)
    root_env = Path(__file__).resolve().parent.parent / ".env"
    if root_env.exists():
        load_dotenv(root_env)

    # Load from backend directory (local dev overrides)
    backend_env = Path(__file__).resolve().parent / ".env"
    if backend_env.exists():
        load_dotenv(backend_env)


def main() -> None:
    _load_env()
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
