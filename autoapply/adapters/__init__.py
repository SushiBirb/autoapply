"""Job application platform adapters module."""

from .base import BaseAdapter
from .linkedin import LinkedInEasyApplyAdapter

__all__ = ["BaseAdapter", "LinkedInEasyApplyAdapter"]
