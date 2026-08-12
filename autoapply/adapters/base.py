from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from playwright.sync_api import Page


class BaseAdapter(ABC):
    """Abstract base class for job platform application adapters."""

    def __init__(self, page: Page, profile: dict[str, Any]):
        self.page = page
        self.profile = profile

    @classmethod
    @abstractmethod
    def can_handle(cls, url: str) -> bool:
        """Return True if this adapter handles the target job posting URL."""
        pass

    @abstractmethod
    def apply(self, url: str, review: bool = True, auto_submit: bool = False) -> dict[str, Any]:
        """Execute the application workflow for a target job posting URL.
        
        Returns dict containing application metadata (company, title, platform, status, etc.).
        """
        pass
