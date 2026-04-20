import hashlib
import logging
import os
import urllib.parse
from pathlib import Path
from typing import Optional

from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from web_agent.config.settings import Config

logger = logging.getLogger(__name__)

TRASH_DIR = Path(__file__).resolve().parent.parent.parent / "trash"

_DOWNLOADABLE_RESOURCE_TYPES = frozenset({
    "image", "stylesheet", "script", "font", "media",
    "manifest", "texttrack", "eventsource", "websocket",
})


def _trash_path_for_url(url: str, content_type: str = "") -> Path:
    url_parsed = urllib.parse.urlparse(url)
    url_path = url_parsed.path or "/"
    _, ext = os.path.splitext(url_path)
    if not ext and content_type:
        mime_map = {
            "text/html": ".html",
            "text/css": ".css",
            "application/javascript": ".js",
            "image/png": ".png",
            "image/jpeg": ".jpg",
            "image/gif": ".gif",
            "image/svg+xml": ".svg",
            "image/webp": ".webp",
            "image/x-icon": ".ico",
        }
        ext = mime_map.get(content_type.split(";")[0].strip(), "")

    url_hash = hashlib.md5(url.encode()).hexdigest()[:10]
    host = url_parsed.netloc.replace(":", "_")
    filename = f"{host}_{url_hash}{ext}"
    return TRASH_DIR / filename


class BrowserSession:
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._console_messages: list[dict] = []
        self._errors: list[dict] = []
        self._network_requests: list[dict] = []
        self._downloaded_files: list[str] = []
        self._pending_downloads: list[tuple] = []

    async def start(self) -> None:
        TRASH_DIR.mkdir(parents=True, exist_ok=True)

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=self.config.headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )
        self._context = await self._browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            ),
            accept_downloads=True,
        )
        self._page = await self._context.new_page()
        self._page.set_default_timeout(self.config.browser_timeout_ms)

        self._page.on("console", self._on_console)
        self._page.on("pageerror", self._on_page_error)
        self._page.on("request", self._on_request)
        self._page.on("response", self._on_response)

        logger.info("Browser session started (headless=%s, trash_dir=%s)", self.config.headless, TRASH_DIR)

    async def stop(self) -> None:
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        self._browser = None
        self._context = None
        self._page = None
        self._playwright = None
        self._pending_downloads.clear()
        logger.info("Browser session stopped")

    async def save_downloaded_files(self) -> list[str]:
        TRASH_DIR.mkdir(parents=True, exist_ok=True)
        saved = []
        for response, dest in self._pending_downloads:
            if dest.exists():
                continue
            try:
                body = await response.body()
                dest.write_bytes(body)
                saved.append(str(dest))
                logger.debug("Saved to trash/: %s", dest.name)
            except Exception as e:
                logger.debug("Failed to save %s: %s", dest.name, e)
        self._downloaded_files.extend(saved)
        self._pending_downloads.clear()
        return saved

    @property
    def page(self) -> Page:
        if self._page is None:
            raise RuntimeError("Browser session not started. Call start() first.")
        return self._page

    @property
    def is_running(self) -> bool:
        return self._browser is not None

    async def navigate(self, url: str) -> dict:
        response = await self._page.goto(url, wait_until="domcontentloaded")
        title = await self._page.title()
        status = response.status if response else None

        await self.save_downloaded_files()

        return {
            "url": self._page.url,
            "title": title,
            "status": status,
        }

    async def snapshot(self) -> dict:
        title = await self._page.title()
        url = self._page.url
        accessibility = await self._page.accessibility.snapshot()
        content = await self._page.content()
        return {
            "url": url,
            "title": title,
            "accessibility_tree": accessibility,
            "html_length": len(content),
        }

    async def screenshot(self, path: str = "screenshot.png") -> str:
        await self._page.screenshot(path=path, full_page=False)
        return path

    async def click(self, selector: str) -> dict:
        await self._page.click(selector)
        return {"action": "click", "selector": selector, "ok": True}

    async def type_text(self, selector: str, text: str) -> dict:
        await self._page.fill(selector, text)
        return {"action": "type", "selector": selector, "text": text, "ok": True}

    async def press_key(self, selector: str, key: str) -> dict:
        await self._page.press(selector, key)
        return {"action": "press", "selector": selector, "key": key, "ok": True}

    async def extract_text(self) -> str:
        return await self._page.inner_text("body")

    async def extract_links(self) -> list[dict]:
        links = await self._page.evaluate(
            """() => {
            return Array.from(document.querySelectorAll('a[href]')).map(a => ({
                href: a.href,
                text: a.textContent.trim()
            }));
        }"""
        )
        return links

    async def evaluate(self, expression: str) -> any:
        return await self._page.evaluate(expression)

    async def wait_for_selector(self, selector: str, timeout: Optional[int] = None) -> dict:
        timeout = timeout or self.config.browser_timeout_ms
        await self._page.wait_for_selector(selector, timeout=timeout)
        return {"action": "wait_for_selector", "selector": selector, "ok": True}

    async def get_console_messages(self) -> list[dict]:
        return list(self._console_messages)

    async def get_errors(self) -> list[dict]:
        return list(self._errors)

    def _on_console(self, msg):
        self._console_messages.append(
            {
                "type": msg.type,
                "text": msg.text,
                "location": msg.location,
            }
        )
        if len(self._console_messages) > 1000:
            self._console_messages = self._console_messages[-500:]

    def _on_page_error(self, error):
        self._errors.append(
            {
                "message": str(error),
                "name": getattr(error, "name", ""),
            }
        )
        if len(self._errors) > 500:
            self._errors = self._errors[-250:]

    def _on_request(self, request):
        self._network_requests.append(
            {
                "method": request.method,
                "url": request.url,
                "resource_type": request.resource_type,
            }
        )
        if len(self._network_requests) > 1000:
            self._network_requests = self._network_requests[-500:]

    def _on_response(self, response):
        resource_type = response.request.resource_type
        if resource_type not in _DOWNLOADABLE_RESOURCE_TYPES:
            return

        status = response.status
        if status < 200 or status >= 400:
            return

        url = response.url
        content_type = response.headers.get("content-type", "")
        dest = _trash_path_for_url(url, content_type)

        if dest.exists():
            return

        self._pending_downloads.append((response, dest))