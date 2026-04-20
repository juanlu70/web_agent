import json
import logging
from typing import Optional

from web_agent.browser.session import BrowserSession
from web_agent.config.settings import Config
from web_agent.search.google_scraper import GoogleSearchScraper
from web_agent.tools.web_fetch import fetch_url

logger = logging.getLogger(__name__)

BROWSER_TOOL_DESCRIPTION = """Control the browser to navigate, extract content, and interact with web pages.
Actions:
- navigate: Go to a URL
- snapshot: Get page accessibility tree and metadata
- screenshot: Take a screenshot and save to path
- click: Click on an element by CSS selector
- type: Type text into an element by CSS selector
- press: Press a key on an element
- extract_text: Get all text content from the page
- extract_links: Get all links from the page
- wait_for_selector: Wait for an element to appear
"""

WEB_SEARCH_TOOL_DESCRIPTION = """Search the web using Google and return the top results.
Returns a list of results with title, URL, and snippet for each.
"""

WEB_FETCH_TOOL_DESCRIPTION = """Fetch a URL and extract its content as markdown.
Returns the page title, content (as markdown), and metadata.
"""


def browser_tool_schema() -> dict:
    return {
        "type": "function",
        "function": {
            "name": "browser",
            "description": BROWSER_TOOL_DESCRIPTION,
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "navigate",
                            "snapshot",
                            "screenshot",
                            "click",
                            "type",
                            "press",
                            "extract_text",
                            "extract_links",
                            "wait_for_selector",
                        ],
                        "description": "The browser action to perform",
                    },
                    "url": {
                        "type": "string",
                        "description": "URL for navigate action",
                    },
                    "selector": {
                        "type": "string",
                        "description": "CSS selector for click/type/press/wait actions",
                    },
                    "text": {
                        "type": "string",
                        "description": "Text to type",
                    },
                    "key": {
                        "type": "string",
                        "description": "Key to press",
                    },
                    "path": {
                        "type": "string",
                        "description": "File path for screenshot",
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Timeout in ms for wait_for_selector",
                    },
                },
                "required": ["action"],
            },
        },
    }


def web_search_tool_schema() -> dict:
    return {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": WEB_SEARCH_TOOL_DESCRIPTION,
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query",
                    }
                },
                "required": ["query"],
            },
        },
    }


def web_fetch_tool_schema() -> dict:
    return {
        "type": "function",
        "function": {
            "name": "web_fetch",
            "description": WEB_FETCH_TOOL_DESCRIPTION,
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to fetch",
                    },
                    "extract_mode": {
                        "type": "string",
                        "enum": ["markdown", "text"],
                        "description": "Extraction mode",
                    },
                    "max_chars": {
                        "type": "integer",
                        "description": "Maximum characters to return",
                    },
                },
                "required": ["url"],
            },
        },
    }


def get_all_tool_schemas() -> list[dict]:
    return [
        browser_tool_schema(),
        web_search_tool_schema(),
        web_fetch_tool_schema(),
    ]


async def execute_tool(
    tool_name: str,
    arguments: dict,
    browser: BrowserSession,
    search_scraper: GoogleSearchScraper,
    config: Config,
    deep: bool = False,
) -> str:
    try:
        if tool_name == "browser":
            return await _execute_browser_tool(arguments, browser)
        elif tool_name == "web_search":
            return await _execute_web_search(arguments, search_scraper, browser, deep)
        elif tool_name == "web_fetch":
            return await _execute_web_fetch(arguments)
        else:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})
    except Exception as e:
        logger.error("Tool execution error (%s): %s", tool_name, e)
        return json.dumps({"error": str(e)})


async def _execute_browser_tool(arguments: dict, browser: BrowserSession) -> str:
    action = arguments.get("action", "")

    if action == "navigate":
        url = arguments.get("url", "")
        result = await browser.navigate(url)
        return json.dumps(result)

    elif action == "snapshot":
        result = await browser.snapshot()
        return json.dumps(result, default=str)

    elif action == "screenshot":
        path = arguments.get("path", "screenshot.png")
        result = await browser.screenshot(path)
        return json.dumps({"screenshot_path": result})

    elif action == "click":
        selector = arguments.get("selector", "")
        result = await browser.click(selector)
        return json.dumps(result)

    elif action == "type":
        selector = arguments.get("selector", "")
        text = arguments.get("text", "")
        result = await browser.type_text(selector, text)
        return json.dumps(result)

    elif action == "press":
        selector = arguments.get("selector", "")
        key = arguments.get("key", "Enter")
        result = await browser.press_key(selector, key)
        return json.dumps(result)

    elif action == "extract_text":
        text = await browser.extract_text()
        return json.dumps({"text": text[:50000]})

    elif action == "extract_links":
        links = await browser.extract_links()
        return json.dumps({"links": links})

    elif action == "wait_for_selector":
        selector = arguments.get("selector", "")
        timeout = arguments.get("timeout")
        result = await browser.wait_for_selector(selector, timeout)
        return json.dumps(result)

    else:
        return json.dumps({"error": f"Unknown browser action: {action}"})


async def _execute_web_search(arguments: dict, scraper: GoogleSearchScraper, browser: BrowserSession, deep: bool = False) -> str:
    query = arguments.get("query", "")
    results = await scraper.search(query, browser, deep=deep)
    return json.dumps(results, ensure_ascii=False)


async def _execute_web_fetch(arguments: dict) -> str:
    url = arguments.get("url", "")
    extract_mode = arguments.get("extract_mode", "markdown")
    max_chars = arguments.get("max_chars", 20000)
    result = await fetch_url(url, extract_mode=extract_mode, max_chars=max_chars)
    return json.dumps(result, ensure_ascii=False)

