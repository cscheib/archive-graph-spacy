"""Project configuration loaded from the local environment."""

from __future__ import annotations

import os

from dotenv import load_dotenv

# Load the repo-local .env file for all Python entrypoints.
load_dotenv()


def get_owner_person_id() -> str | None:
    value = os.getenv("OWNER_PERSON_ID", "").strip()
    return value or None
