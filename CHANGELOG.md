# Changelog

All notable changes to the web_agent project will be documented in this file.

## [1.4.0] - 2025-04-30

### Added

- **User Memory system** (`web_agent/agent/user_memory.py`): Personal memory stored in `~/.web_agent/MEMORY.md`
  - Long-term memory: preferences, personal context, and notes persisted in MEMORY.md and `memory/YYYY-MM-DD.md` dated entries
  - Short-term memory: in-memory session observations (max 10), flushable to long-term memory
  - Memory context injected into all orchestrator prompts (AI-first check, task planning, browsing)
  - Server API: `GET /memory` (read), `POST /memory` (save/append/flush short-term)
- **Heartbeat system** (`web_agent/agent/heartbeat.py`): Recurring task execution inspired by OpenClaw
  - `HEARTBEAT.md` file (at `~/.web_agent/HEARTBEAT.md`) defines scheduled tasks with YAML frontmatter
  - Task definition: `name`, `interval` (e.g., 30m, 1h, 24h), `prompt`
  - Periodic runner checks due tasks and sends them to the orchestrator
  - State persistence (`heartbeat_state.json`) so tasks survive restarts
  - Enabled via `heartbeat_enabled: true` + `heartbeat_every: "30m"` in `config.yaml`
  - Server API: `GET /heartbeat/status`
- **Cron service** (`web_agent/agent/cron_service.py`): Precise scheduled task execution
  - Three schedule types: `cron` (standard 5-field expressions), `every` (interval in seconds), `at` (one-shot ISO timestamp)
  - JSON persistence at `~/.web_agent/cron/jobs.json`
  - Jobs run as isolated orchestrator requests
  - Auto-disabled after consecutive errors
  - Enabled via `cron_enabled: true` in `config.yaml`
  - Server API: `GET /cron`, `POST /cron`, `DELETE /cron/{job_id}`
- **Default templates**: `web_agent/defaults/MEMORY.md` and `web_agent/defaults/HEARTBEAT.md`
- **Config fields**: `heartbeat_enabled`, `heartbeat_every`, `cron_enabled`

### Changed

- `web_agent.py` renamed to `web_agent_server.py` (server entry point)
- `web_agent_client.py` renamed to `web_agent.py` (CLI client entry point)
- CLI `prog` name updated from `web_agent_client` to `web_agent`

## [1.3.0] - 2025-04-23

### Added

- **Request history log**: All requests to the model are saved to `~/.web_agent/request_log.json`, including query, result, file paths provided, source (AI knowledge / web search / error), and deep mode flag
- **`RequestLog` class** (`web_agent/agent/request_log.py`): Structured JSON-based request logger with add/get/clear methods
- **`GET /history` API endpoint**: Returns full request history from the server, with optional `?limit=N` query param
- **`GET /history/{entry_id}` API endpoint**: Returns a single history entry by ID
- **`--history` CLI flag**: View request history from the command line
- **`--history-limit` CLI flag**: Limit number of history entries displayed (use with `--history`)
- **`--history-id` CLI flag**: Re-run a specific past request by its ID (IDs are shown in `--history` output)
- **Next.js web UI**: Replaced Streamlit with a ChatGPT-style Next.js frontend (TypeScript + Tailwind CSS)
  - **Centered input**: Empty state shows a centered input box (ChatGPT-style); once messages exist, input moves to bottom
  - **Deep search pill**: On/off toggle inside the input bar (purple pill labeled "Deep")
  - **History in sidebar**: Left panel has "Chats" / "History" tabs — history shows all past requests with refresh + re-run
  - **Stop button**: During search, "Searching..." shows a Stop button that cancels the running task
  - **Task cancellation**: New `DELETE /cancel/{task_id}` endpoint cancels running orchestrator tasks (async.CancelledError)
  - Conversation threads with create/switch/delete in sidebar
  - ChatGPT-style message layout with markdown rendering (react-markdown + remark-gfm)
  - File upload in input bar with attachment badges
  - Server connection status indicator in header
  - API uses async mode (sync=false) with client-side polling for cancellability
  - CORS middleware (function-based) for cross-origin requests from localhost:3000
  - **Theme toggle**: Light / Dark / System with manual override and localStorage persistence
  - **Settings panel**: Server URL input, connection test, active model, theme switcher
- **Client**: Added `cancel()` method to `WebAgentClient`
- **Server**: `POST /request` default changed to `sync=false` for web UI; CLI client still sends `sync=true`
- **`web_agent_ui.py` launcher updated**: Now launches `pnpm dev` / `pnpm start`
- **Streamlit UI removed**: `streamlit` removed from `requirements.txt`

## [1.2.0] - 2025-04-23

### Added

- **Multi-provider LLM support**: Choose between Ollama, OpenAI, Anthropic, and OpenRouter
  - `llm_provider` config field: `"ollama"`, `"openai"`, `"anthropic"`, `"openrouter"`
  - `llm_api_url`, `llm_api_key`, `llm_model` fields for cloud providers
  - OpenAI-compatible chat endpoint for OpenAI and OpenRouter
  - Anthropic Messages API for Claude models
- **Setup tool** (`web_agent_setup.py`): Interactive CLI to configure LLM provider and model
  - Auto-detects Ollama models and lists them for selection
  - Lists known models for OpenAI, Anthropic, OpenRouter
  - Prompts for API keys for cloud providers
  - Saves to `config.yaml`
- **Unified `LLMClient`**: Replaces `OllamaClient` in orchestrator — routes to correct provider automatically

### Changed

- `OllamaClient` still exists internally but is wrapped by `LLMClient`
- Config: `ollama_base_url` + `ollama_model` for Ollama, `llm_api_url` + `llm_api_key` + `llm_model` for cloud

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


