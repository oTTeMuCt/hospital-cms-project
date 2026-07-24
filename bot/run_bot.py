"""
Bot launcher that reads .env file and sets environment variables correctly.
"""
import os
import sys
from pathlib import Path

# Read .env from project root
env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.exists():
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        os.environ.setdefault(key, value)

# Override API_BASE_URL for local development
os.environ["API_BASE_URL"] = "http://localhost:8000/api"

# Now import and run the bot
from app import main

if __name__ == "__main__":
    main()