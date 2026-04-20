---
name: web-browsing
description: "Interact with web pages using a full browser. Use when: user needs to browse websites that require JavaScript, fill forms, click buttons, navigate multi-page workflows, log into accounts, or extract content that dynamic rendering provides. NOT for: simple URL content extraction (use web_fetch), searching the web (use web_search)."
---

# Web Browsing Skill

Control a browser to interact with web pages that require JavaScript or user interaction.

## When to Use

- Websites that require JavaScript rendering
- Filling out forms or submitting data
- Clicking through multi-page workflows
- Logging into accounts
- Extracting content from dynamic pages
- Taking screenshots of web pages

## When NOT to Use

- Simple URL content extraction (use web_fetch for static pages)
- Searching for information (use web_search)

## Browser Actions

| Action | Description | Key Parameters |
|--------|-------------|----------------|
| navigate | Go to a URL | url |
| snapshot | Get page structure (accessibility tree) | - |
| screenshot | Take a screenshot | path |
| click | Click an element | selector |
| type | Type text into an element | selector, text |
| press | Press a key | selector, key |
| extract_text | Get all visible text | - |
| extract_links | Get all links on the page | - |
| wait_for_selector | Wait for an element | selector, timeout |

## Workflow

1. Navigate to the target URL
2. Take a snapshot to understand the page structure
3. Interact with elements using click/type/press
4. Wait for navigation or content changes
5. Extract the desired information
6. If navigating to a new page, take another snapshot

## CSS Selector Tips

- Use `#id` for elements by ID
- Use `.class` for elements by class
- Use `input[name='field']` for form fields
- Use `a[href*='pattern']` for links matching a pattern
- Use `button:has-text('Submit')` for buttons by text

## Constraints

- Don't use more than 3 agents at the same time, wait for the one of the working agents to finish to launch the next agent.

