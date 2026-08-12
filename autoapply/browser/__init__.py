"""Browser automation module for autoapply using Playwright."""

from .session import launch_browser_session
from .filler import FormFiller
from .discovery import JobDiscoveryEngine

__all__ = ["launch_browser_session", "FormFiller", "JobDiscoveryEngine"]
