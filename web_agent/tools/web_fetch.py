import aiohttp
import logging
import re
from typing import Optional
from html.parser import HTMLParser

from web_agent.config.settings import Config

logger = logging.getLogger(__name__)

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)
DEFAULT_MAX_CHARS = 20000
DEFAULT_TIMEOUT_SECONDS = 30


class _HTMLToMarkdown(HTMLParser):
    BLOCK_TAGS = {"p", "div", "section", "article", "main", "header", "footer", "nav", "aside", "blockquote", "li"}
    SKIP_TAGS = {"script", "style", "noscript", "svg", "math"}
    HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}

    def __init__(self):
        super().__init__()
        self._result: list[str] = []
        self._skip_depth = 0
        self._current_tag: Optional[str] = None
        self._in_link = False
        self._link_href = ""
        self._link_text = ""

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        self._current_tag = tag
        if tag in self.SKIP_TAGS:
            self._skip_depth += 1
            return
        if self._skip_depth > 0:
            return
        if tag in self.HEADING_TAGS:
            level = int(tag[1])
            self._result.append("\n" + "#" * level + " ")
        elif tag == "li":
            self._result.append("\n- ")
        elif tag == "br":
            self._result.append("\n")
        elif tag == "a":
            for name, value in attrs:
                if name == "href":
                    self._in_link = True
                    self._link_href = value or ""
                    self._link_text = ""
                    break
        elif tag == "code":
            self._result.append("`")
        elif tag == "strong" or tag == "b":
            self._result.append("**")
        elif tag == "em" or tag == "i":
            self._result.append("*")
        elif tag == "hr":
            self._result.append("\n---\n")
        elif tag in self.BLOCK_TAGS:
            self._result.append("\n")

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in self.SKIP_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)
            return
        if self._skip_depth > 0:
            return
        if tag == "a" and self._in_link:
            self._result.append(f"[{self._link_text}]({self._link_href})")
            self._in_link = False
        elif tag == "code":
            self._result.append("`")
        elif tag in ("strong", "b"):
            self._result.append("**")
        elif tag in ("em", "i"):
            self._result.append("*")
        elif tag in self.BLOCK_TAGS:
            self._result.append("\n")

    def handle_data(self, data):
        if self._skip_depth > 0:
            return
        text = data
        if self._in_link:
            self._link_text += text
        else:
            self._result.append(text)

    def get_markdown(self) -> str:
        raw = "".join(self._result)
        raw = re.sub(r"\n{3,}", "\n\n", raw)
        return raw.strip()


def html_to_markdown(html: str) -> str:
    parser = _HTMLToMarkdown()
    parser.feed(html)
    return parser.get_markdown()


async def fetch_url(
    url: str,
    extract_mode: str = "markdown",
    max_chars: int = DEFAULT_MAX_CHARS,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> dict:
    timeout_obj = aiohttp.ClientTimeout(total=timeout)
    headers = {"User-Agent": DEFAULT_USER_AGENT}

    try:
        async with aiohttp.ClientSession(timeout=timeout_obj, headers=headers) as session:
            async with session.get(url) as resp:
                resp.raise_for_status()
                content_type = resp.headers.get("Content-Type", "")
                body = await resp.text()

        if "text/html" in content_type or extract_mode == "markdown":
            text = html_to_markdown(body)
        else:
            text = body

        if len(text) > max_chars:
            text = text[:max_chars] + f"\n\n[... truncated at {max_chars} chars]"

        return {
            "url": url,
            "title": _extract_title(body),
            "content": text,
            "content_length": len(text),
            "status": resp.status,
        }
    except Exception as e:
        logger.error("Failed to fetch %s: %s", url, e)
        return {
            "url": url,
            "error": str(e),
            "content": "",
        }


def _extract_title(html: str) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else ""

