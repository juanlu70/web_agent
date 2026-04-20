import logging
import urllib.parse
from typing import Optional

from web_agent.browser.session import BrowserSession
from web_agent.config.settings import Config

logger = logging.getLogger(__name__)

GOOGLE_SEARCH_URL = "https://www.google.com/search"
GOOGLE_RESULTS_PER_PAGE = 10


class GoogleSearchScraper:
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.normal_results = self.config.normal_search_results
        self.deep_results = self.config.deep_search_results

    async def search(self, query: str, browser: BrowserSession, deep: bool = False) -> list[dict]:
        max_results = self.deep_results if deep else self.normal_results
        encoded = urllib.parse.quote_plus(query)
        all_results = []

        pages_needed = (max_results + GOOGLE_RESULTS_PER_PAGE - 1) // GOOGLE_RESULTS_PER_PAGE

        for page in range(pages_needed):
            start = page * GOOGLE_RESULTS_PER_PAGE
            url = f"{GOOGLE_SEARCH_URL}?q={encoded}&num={GOOGLE_RESULTS_PER_PAGE}&start={start}"

            await browser.navigate(url)

            remaining = max_results - len(all_results)
            page_results = await browser.page.evaluate(
                f"""() => {{
                const items = [];
                const resultElements = document.querySelectorAll('div.g, div[data-sokoban-container], .tF2Cxc');
                const limit = {remaining};
                for (let i = 0; i < Math.min(resultElements.length, limit); i++) {{
                    const el = resultElements[i];
                    const titleEl = el.querySelector('h3');
                    const linkEl = el.querySelector('a[href]');
                    const snippetEl = el.querySelector('.VwiC3b, .IsZvec, span[style]');

                    if (titleEl && linkEl) {{
                        items.push({{
                            title: titleEl.textContent.trim(),
                            url: linkEl.href,
                            snippet: snippetEl ? snippetEl.textContent.trim() : ''
                        }});
                    }}
                }}
                return items;
            }}"""
            )

            if not page_results:
                page_results = await self._fallback_extract(browser, remaining)

            all_results.extend(page_results)

            if len(all_results) >= max_results or not page_results:
                break

        all_results = all_results[:max_results]
        logger.info("Google search for '%s' returned %d results (deep=%s)", query, len(all_results), deep)
        return all_results

    async def _fallback_extract(self, browser: BrowserSession, limit: int = 10) -> list[dict]:
        return await browser.page.evaluate(
            f"""() => {{
            const items = [];
            const links = document.querySelectorAll('a[href]');
            const limit = {limit};
            for (const link of links) {{
                const href = link.href;
                if (href && href.startsWith('http') && !href.includes('google.com') &&
                    !href.includes('gstatic') && !href.includes('schema.org')) {{
                    const title = link.textContent.trim();
                    if (title && title.length > 5) {{
                        items.push({{
                            title: title,
                            url: href,
                            snippet: ''
                        }});
                        if (items.length >= limit) break;
                    }}
                }}
            }}
            return items;
        }}"""
        )