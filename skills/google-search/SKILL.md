---
name: google-search
description: "Search the web using Google and extract information from search results. Use when: user asks to search for information on any topic, find websites, look up facts, research topics, or compare information across sources. NOT for: direct URL access (use web_fetch), interacting with specific websites (use browser)."
website_url: "https://www.google.com"
---

# Google Search Skill

Search Google and extract information from the top results.

## When to Use

- User asks to search for information
- Need to find websites related to a topic
- Research tasks requiring multiple sources
- Fact-checking and verification

## When NOT to Use

- Accessing a known URL directly (use web_fetch)
- Interacting with a website (use browser)
- Local file operations

## Instructions

1. Use the `web_search` tool with a clear, specific query
2. Review the search results (title, URL, snippet)
3. Use `web_fetch` on the most relevant results to extract content
4. Summarize findings and cite sources

## Search Tips

- Use specific queries: "Python async await tutorial" instead of "Python"
- Add site: prefix for site-specific searches if useful
- The tool returns up to 10 results maximum
- Always extract content from promising results before summarizing
