from __future__ import annotations

import contextlib
from pathlib import Path
from typing import Generator

from playwright.sync_api import BrowserContext, Page, Playwright, sync_playwright

from ..config import get_browser_profile_dir


@contextlib.contextmanager
def launch_browser_session(
    user_data_dir: Path | str | None = None,
    headless: bool = False,
    viewport_width: int = 1280,
    viewport_height: int = 900,
) -> Generator[tuple[BrowserContext, Page], None, None]:
    """Launch a Playwright persistent context browser session.
    
    Preserves cookies, session storage, and login tokens across runs.
    """
    profile_dir = Path(user_data_dir or get_browser_profile_dir())
    profile_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            headless=headless,
            viewport={"width": viewport_width, "height": viewport_height},
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
            ),
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ],
        )
        page = context.pages[0] if context.pages else context.new_page()
        try:
            yield context, page
        finally:
            context.close()
