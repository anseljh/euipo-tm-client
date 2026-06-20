"""Configuration and environment handling for the EUIPO trademark search client."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

Environment = Literal["sandbox", "production"]

# Base URL of the trademark search API per environment.
API_BASE_URLS: dict[Environment, str] = {
    "sandbox": "https://api-sandbox.euipo.europa.eu/trademark-search",
    "production": "https://api.euipo.europa.eu/trademark-search",
}

# OAuth2 token endpoints per environment.
# The sandbox URL is documented at https://dev-sandbox.euipo.europa.eu/security.
# The production URL is the sandbox mirror and is UNVERIFIED against EUIPO docs;
# override it explicitly if EUIPO publishes a different production token endpoint.
TOKEN_URLS: dict[Environment, str] = {
    "sandbox": "https://auth-sandbox.euipo.europa.eu/oidc/accessToken",
    "production": "https://auth.euipo.europa.eu/oidc/accessToken",
}


def _load_dotenv(path: str | os.PathLike[str] = ".env") -> None:
    """Populate os.environ from a .env file without adding a dependency.

    Existing environment variables take precedence (we never overwrite them).
    Lines that are blank, comments, or lack an ``=`` are ignored. Surrounding
    quotes and inline ``# ...`` comments are stripped from values.
    """
    env_path = Path(path)
    if not env_path.is_file():
        return
    for raw_line in env_path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if key in os.environ:
            continue
        value = value.strip()
        if value and value[0] in "\"'":
            # Quoted value: take everything up to the matching closing quote and
            # discard any trailing inline comment (e.g. `"abc" # note`).
            quote = value[0]
            end = value.find(quote, 1)
            if end != -1:
                value = value[1:end]
        elif "#" in value:
            # Unquoted value: an inline comment starts at the first '#'.
            value = value.split("#", 1)[0].strip()
        os.environ[key] = value


@dataclass(frozen=True)
class Settings:
    """Resolved client settings.

    Use :meth:`from_env` to build these from environment variables (loading
    ``.env`` if present), or construct directly for tests.
    """

    api_key: str
    api_secret: str
    environment: Environment = "sandbox"

    @property
    def api_base_url(self) -> str:
        return API_BASE_URLS[self.environment]

    @property
    def token_url(self) -> str:
        return TOKEN_URLS[self.environment]

    @classmethod
    def from_env(cls, *, load_dotenv: bool = True) -> "Settings":
        """Build settings from ``EUIPO_API_KEY``/``EUIPO_API_SECRET``/``EUIPO_ENVIRONMENT``."""
        if load_dotenv:
            _load_dotenv()
        api_key = os.environ.get("EUIPO_API_KEY")
        api_secret = os.environ.get("EUIPO_API_SECRET")
        environment = os.environ.get("EUIPO_ENVIRONMENT", "sandbox").strip().lower()

        missing = [
            name
            for name, value in (
                ("EUIPO_API_KEY", api_key),
                ("EUIPO_API_SECRET", api_secret),
            )
            if not value
        ]
        if missing:
            raise ValueError(
                f"Missing required environment variable(s): {', '.join(missing)}"
            )
        if environment not in API_BASE_URLS:
            raise ValueError(
                f"EUIPO_ENVIRONMENT must be one of {sorted(API_BASE_URLS)}, "
                f"got {environment!r}"
            )

        # api_key/api_secret are guaranteed non-None by the missing check above.
        return cls(
            api_key=api_key,  # type: ignore[arg-type]
            api_secret=api_secret,  # type: ignore[arg-type]
            environment=environment,  # type: ignore[arg-type]
        )
