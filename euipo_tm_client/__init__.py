"""Minimal Python client for the EUIPO trademark search API."""

from __future__ import annotations

from .client import TrademarkSearchClient
from .config import Settings
from .errors import EUIPOAPIError, EUIPOAuthError, EUIPOError

__all__ = [
    "TrademarkSearchClient",
    "Settings",
    "EUIPOError",
    "EUIPOAuthError",
    "EUIPOAPIError",
]
