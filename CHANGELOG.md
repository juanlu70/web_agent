# Changelog

All notable changes to the web_agent project will be documented in this file.

## [1.1.0] - 2025-04-19

### Added

- **Multiple file analysis**: `--files` / `-f` flag now accepts multiple files: `-f file1.pdf file2.md file3.csv`
- `FileAnalyzer.read_files()` method for batch file reading
- `AnalysisAgent` combines content from all files into a single analysis prompt
- Streamlit UI: file uploader now supports multiple files (`accept_multiple_files=True`)

### Changed

- `--file` renamed to `--files` / `-f` (accepts multiple values via `nargs='+'`)
- `file_path: str` changed to `file_paths: list[str]` across: Orchestrator, AnalysisAgent, Server, Client, CLI, UI
- Server API: `file_path` field changed to `file_paths` (array of strings)
- Client API: `file_path` parameter changed to `file_paths` (list of strings)

## [1.0.0] - 2025-04-19

### Added

- **Server/daemon mode**: `web_agent.py` is now an HTTP server (aiohttp) that listens for requests
  - `POST /request` — Send a query (JSON: `query`, `deep`, `file_path`, `sync`)
  - `GET /health` — Check server health
  - `GET /config` — Get server configuration
  - `GET /status/{task_id}` — Check async task status
- **CLI client**: `web_agent_client.py` connects to the server via HTTP
  - Supports all previous flags: `--deep`, `--file`, `--server`, `--config`, `--verbose`
  - Interactive mode and single-request mode
- **Streamlit UI updated**: Now connects to server via `WebAgentClient` instead of running orchestrator directly
- **Server config in `config.yaml`**:
  - `server_host`: Listen address (default: `127.0.0.1` for localhost only, set `0.0.0.0` for all interfaces)
  - `server_port`: Listen port (default: `8400`)

### Changed

- `web_agent.py` is now the **server** entry point (was CLI)
- `web_agent_client.py` is the new **CLI client** entry point
- Server and clients are fully independent — server runs as daemon, clients connect remotely

### Added

- **YAML config file** (`config.yaml`): Central configuration for all major settings
  - `normal_search_results`: Number of search results in normal mode (default: 10)
  - `deep_search_results`: Number of search results in deep mode (default: 50)
  - `max_subagents`: Maximum agents running simultaneously (default: 3)
  - `max_agent_iterations`: Maximum iterations per agent (default: 10)
  - `max_history_entries`: Conversation history entries to keep (default: 15)
  - `subagent_depth_limit`, `	headless`, `browser_timeout_ms`, `ollama_*`, `skills_dir`, `guardrails_file`
- **Guardrails system** (`guardrails.md`): Safety rules and behavioral constraints loaded into all agents (main, sub, analysis, AI-first)
  - Safety rules (no weapons, hacking, illegal content, etc.)
  - Behavioral rules (cite sources, respect rate limits, identify as AI)
  - Agent constraints (max subagents, no purchases, no form submissions)
  - Content guidelines (accuracy, multiple viewpoints, language matching)
- **Default max_subagents changed from 5 to 3** as per config
- Guardrails injected into all system prompts: BrowsingAgent, Orchestrator, AnalysisAgent, AI-first check

### Changed

- Config format migrated from JSON (`~/.web_agent/config.json`) to YAML (`config.yaml` in project root)
- `Config.max_search_results` replaced by `Config.normal_search_results` and `Config.deep_search_results`
- ConversationHistory now reads `max_entries` from config instead of hardcoded constant
- GoogleSearchScraper now uses config values for result limits
- Streamlit UI updated with all new config options and guardrails preview

## [0.7.0] - 2025-04-17

### Added

- **Streamlit web interface**: Independent frontend at `web_agent_ui.py` with all CLI options as sidebar controls
- Sidebar controls: Ollama URL, model, deep search toggle, headless mode, browser timeout, max subagents, subagent depth, skills directory, verbose logging
- File upload support in the web UI for file analysis
- Chat-style interface with conversation history
- Clear conversation button
- Status indicators showing active flags during processing

## [0.6.0] - 2025-04-17

### Added

- **Trash directory**: All downloaded files from browsing (images, CSS, JS, HTML, fonts, media) are saved to `trash/` directory
- Files are saved asynchronously after each page navigation with hashed filenames
- `BrowserSession.save_downloaded_files()` method to flush pending downloads to disk

## [0.5.0] - 2025-04-17

### Added

- **Domain-specific browsing**: When the user specifies a website/domain (e.g. "search on amazon.com for..."), the agent navigates directly to that site instead of searching Google first
- **Domain extraction**: Automatically detects URLs and domain names in the request; skips Google search and AI-first check for domain-targeted requests
- **Updated BrowsingAgent prompt**: Clear instructions to not use `web_search` when a specific domain is requested — browse directly instead

## [0.4.0] - 2025-04-17

### Added

- **AI-first flow**: Orchestrator asks the AI model first before searching the web. Web search only triggers when the model responds with `NEEDS_WEB_SEARCH` (for current/updated info it lacks)
- **Conversation history**: Last 15 request/result pairs stored in `~/.web_agent/conversation_history.md`, loaded as context for future requests so the model learns user behavior
- **History context injection**: Previous conversation history is included in AI-first check and task planning prompts

## [0.3.0] - 2025-04-17

### Added

- **`--deep` CLI flag**: Enables deep search mode with up to 50 Google results instead of the default 10
- **Multi-page scraping**: In deep mode, the Google scraper paginates through multiple result pages (10 per page) to collect up to 50 results
- Deep mode propagated through all layers: CLI → OrchestratorAgent → BrowsingAgent → execute_tool → GoogleSearchScraper

## [0.2.0] - 2025-04-17

### Added

- **File Analysis**: Analyze, summarize, and review files via `--file` CLI argument or `file:<path>` in interactive mode
- **FileAnalyzer Tool**: Reads text files (txt, md, csv, json, py, js, etc.), PDF (via pdfplumber), and DOCX (via python-docx)
- **AnalysisAgent**: Dedicated agent for file content analysis using the LLM
- **CLI `--file` / `-f` flag**: Pass a file path as second argument alongside the request
- **Interactive `file:` prefix**: Type `file:report.pdf summarize this` in interactive mode

## [0.1.0] - 2025-04-17

### Added

- **Core Architecture**: Main orchestrator agent that receives requests and dispatches child agents
- **Ollama LLM Integration**: Client for local Ollama API with chat and generate endpoints, streaming support
- **Browser Automation**: Playwright-based browser session management (navigate, click, type, screenshot, snapshot, extract)
- **Google Search Scraper**: Direct Google search scraping without API key, configurable max results (default 10)
- **Web Fetch Tool**: HTTP fetch with HTML-to-markdown extraction, configurable max content size
- **Skill System**: Markdown-based skill definitions (SKILL.md) with YAML frontmatter, skill discovery by query relevance, skill storage and retrieval
- **Parallel Subagent Processing**: asyncio-based parallel execution of multiple child agents, configurable max subagents and depth limits
- **Tool System**: Three main tools exposed to LLM: browser, web_search, web_fetch
- **CLI Interface**: Single-request and interactive modes, configurable model, URL, headless mode, and skills directory
- **Configuration**: JSON config file support (~/.web_agent/config.json), environment variable overrides, sensible defaults
- **Initial Skills**: google-search skill, web-browsing skill

### Architecture

Inspired by OpenClaw's web browsing mechanism:
- Playwright + CDP for browser automation (mirroring OpenClaw's pw-session.ts approach)
- Tool-based LLM interaction pattern (browser, web_search, web_fetch tools)
- Skill-based MCP for website navigation learning (matching OpenClaw's SKILL.md pattern)
- Subagent spawning for parallel task execution (mirroring OpenClaw's sessions_spawn pattern)