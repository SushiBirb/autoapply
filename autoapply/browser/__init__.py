"""Browser automation module for autoapply using Playwright."""

from .session import launch_browser_session
from .filler import FormFiller

__all__ = ["launch_browser_session", "FormFiller"]
