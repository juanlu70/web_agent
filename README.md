# Web Agent

A browser agent managed by IA. It searches the web, gathers information, and analyzes files — powered by a local LLM via Ollama.

It is intended as a mix of a personal Perplexity and OpenClaw but without the insecure environment of OpenClaw.


## Architecture

```
┌──────────────┐   ┌─────────────┐   ┌─────────────┐
│  CLI Client  │   │  Next.js    │   │  HTTP API   │
│  (terminal)  │   │  Web UI     │   │  (curl,etc) │
└──────┬───────┘   └──────┬──────┘   └──────┬──────┘
       │                  │                 │
       └──────────────────┼─────────────────┘
                          │ HTTP
                   ┌──────▼───────┐
                   │   Server     │
                   │ (Orchestrator│
                   │  + Agents)   │
                   └──────┬───────┘
                          │
              ┌───────────┼───────────┐
              │           │           │
         ┌────▼───┐  ┌────▼───┐  ┌────▼───┐
         │Subagent│  │Subagent│  │ Ollama │
         │  1     │  │  2     │  │  LLM   │
         └────────┘  └────────┘  └────────┘
```

The server is the main orchestrator. Clients connect via HTTP. The orchestrator asks the LLM first; only if it lacks knowledge does it spawn browsing subagents.

## Requirements

- Python 3.11+
- Node.js 18+ (for the web UI)
- [pnpm](https://pnpm.io) (for the web UI)
- An LLM provider: [Ollama](https://ollama.ai) (local, free) **or** an OpenAI/Anthropic/OpenRouter API key
- Chromium (for Playwright — auto-installed)

## Install

### Python backend

```bash
pip install -r requirements.txt
playwright install chromium
```

### Web UI (Next.js)

The web UI is a Next.js application located at `web_agent/web/`. You need Node.js (18+) and pnpm installed.

**1. Install Node.js** (if you don't have it):

Using [nvm](https://github.com/nvm-sh/nvm) (recommended):

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.0/install.sh | bash
source ~/.bashrc
nvm install --lts
```

Or download directly from [nodejs.org](https://nodejs.org/).

**2. Install pnpm:**

```bash
npm install -g pnpm
```

**3. Install web UI dependencies:**

```bash
cd web_agent/web
pnpm install
```

This installs Next.js, React, Tailwind CSS, and all other dependencies defined in `package.json`.

**4. Verify the installation:**

```bash
pnpm build
```

If the build succeeds, the web UI is ready to run.

## Setup

Before running for the first time, configure your LLM provider and model:

```bash
./web_agent_setup.py
```

This interactive tool will:

1. **List available providers**: Ollama (local), OpenAI, Anthropic, OpenRouter
2. **For Ollama**: connect to your local instance, list all pulled models, and let you pick one
3. **For cloud providers**: ask for your API key, API URL, and model name
4. **Save** everything to `config.yaml`

Example session:

```
==================================================
  Web Agent Setup
==================================================

  Current provider: ollama
  Ollama URL:   http://localhost:11434
  Ollama model: glm-5.1:cloud

Available LLM providers:

  1. Ollama (local)
  2. OpenAI [requires API key]
  3. Anthropic [requires API key]
  4. OpenRouter [requires API key]

Select provider [1]: 1

Checking Ollama for available models...

Available models:
  1. glm-5.1:cloud (323 MB)
  2. glm-4.7-flash-agent:latest (19019 MB)
  3. qwen3-coder:480b-cloud

Select model [1]: 1

--------------------------------------------------
  Configuration summary:

  Provider: ollama
  Ollama URL:   http://localhost:11434
  Model:         glm-5.1:cloud

Save configuration? [Y/n]: Y
  Saved to .../config.yaml

Setup complete. You can now start the server with: ./web_agent_server.py
```

You can also edit `config.yaml` directly (see [Configuration](#configuration-configyaml) below).

## Quick Start

**1. Start the server:**

```bash
./web_agent_server.py
```

**2. Query from a client:**

```bash
# Single query
./web_agent.py "search for wireless headphones"

# Interactive mode
./web_agent.py

# View request history
./web_agent.py --history
./web_agent.py --history --history-limit 5

# Web UI
./web_agent_ui.py         # dev mode (port 3000)
./web_agent_ui.py --build # production build + start
```

---

## Server (`web_agent_server.py`)

The server is a daemon that listens for HTTP requests and runs the orchestrator with browsing agents.

```bash
./web_agent_server.py [OPTIONS]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--host` | `127.0.0.1` | Bind address (`0.0.0.0` for all interfaces) |
| `--port` | `8400` | Listen port |
| `--config` | `config.yaml` | Path to YAML config file |
| `--verbose`, `-v` | off | Enable debug logging |

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/request` | Send a query |
| `GET` | `/health` | Server health check |
| `GET` | `/config` | Get server configuration |
| `GET` | `/status/{task_id}` | Check async task status |
| `DELETE` | `/cancel/{task_id}` | Cancel a running task |
| `GET` | `/history` | Get request history |
| `GET` | `/history/{entry_id}` | Get a specific history entry by ID |
| `GET` | `/memory` | Get user memory (MEMORY.md) |
| `POST` | `/memory` | Update user memory |
| `GET` | `/cron` | List cron jobs |
| `POST` | `/cron` | Add a cron job |
| `DELETE` | `/cron/{job_id}` | Remove a cron job |
| `GET` | `/heartbeat/status` | Get heartbeat status |

#### POST /request

```json
{
  "query": "search for wireless headphones",
  "deep": false,
  "file_paths": ["/path/to/file.pdf"],
  "sync": true
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `query` | string | required | The request to process |
| `deep` | bool | `false` | Deep search (50 results instead of 10) |
| `file_paths` | string[] | `null` | Files to analyze |
| `sync` | bool | `true` | Wait for result (`false` returns a task ID) |

**Response (sync):**

```json
{
  "task_id": "a1b2c3d4",
  "status": "completed",
  "result": "Here is a summary of..."
}
```

**Response (async):**

```json
{
  "task_id": "a1b2c3d4",
  "status": "running"
}
```

Then poll `GET /status/a1b2c3d4` until `status` is `completed` or `failed`.

#### GET /history

Returns the full request history log. Each entry includes the query, result, file paths, source, and deep mode flag.

**Query params:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `limit` | int | all | Maximum number of entries to return |

**Response:**

```json
{
  "history": [
    {
      "id": "a1b2c3d4",
      "timestamp": "2025-04-23T14:30:00",
      "query": "search for wireless headphones",
      "file_paths": [],
      "result": "Here is a summary...",
      "source": "web search",
      "deep": false
    }
  ],
  "count": 1
}
```

#### GET /history/{entry_id}

Returns a single history entry by its ID. Useful for re-running past requests programmatically.

**Response:**

```json
{
  "id": "a1b2c3d4",
  "timestamp": "2025-04-23T14:30:00",
  "query": "search for wireless headphones",
  "file_paths": [],
  "result": "Here is a summary...",
  "source": "web search",
  "deep": false
}
```

---

## CLI Client (`web_agent.py`)

```bash
./web_agent.py [REQUEST] [OPTIONS]
```

If no request is given, enters interactive mode.

| Flag | Default | Description |
|------|---------|-------------|
| `--files`, `-f` | none | Files to analyze (supports multiple: `-f a.pdf b.md`) |
| `--server` | from config | Server URL (e.g. `http://192.168.1.10:8400`) |
| `--deep` | off | Deep search: 50 results instead of 10 |
| `--history` | off | Show request history from the server |
| `--history-limit` | all | Limit number of history entries (use with `--history`) |
| `--history-id` | — | Re-run a specific past request by its ID (shown in `--history`) |
| `--config` | `config.yaml` | Path to YAML config file |
| `--verbose`, `-v` | off | Enable debug logging |

### Examples

```bash
# Web search
./web_agent.py "search for Python async tutorials"

# Deep search (50 results, slower)
./web_agent.py --deep "compare React vs Vue frameworks"

# Analyze one file
./web_agent.py -f report.pdf "summarize this report"

# Analyze multiple files
./web_agent.py -f report.pdf notes.md data.csv "compare these documents"

# Connect to remote server
./web_agent.py --server http://192.168.1.10:8400 "search for laptops"

# Interactive mode
./web_agent.py
You> search for wireless headphones
You> file:report.pdf,notes.md compare both
You> exit

# View request history
./web_agent.py --history

# View last 5 requests
./web_agent.py --history --history-limit 5

# Re-run a past request by ID (IDs shown in --history)
./web_agent.py --history-id a1b2c3d4
```

---

## Next.js Web UI

A ChatGPT-style web interface built with Next.js, TypeScript, and Tailwind CSS.

```bash
# Development mode (hot reload)
./web_agent_ui.py

# Or directly:
cd web_agent/web && pnpm dev

# Production build + start
./web_agent_ui.py --build
```

Opens at `http://localhost:3000`.

### Features

- **ChatGPT-style layout**: Sidebar with conversation threads, main chat area, input bar
- **Conversation threads**: Create, switch, and delete separate chat threads
- **File upload**: Attach files for analysis via the input bar
- **Deep search toggle**: Enable 50-result deep search per message
- **Markdown rendering**: Assistant responses render with full markdown (code blocks, tables, etc.)
- **Request history**: View and re-run past requests from the history panel
- **Server connection status**: Live indicator showing server connectivity and model

---

## How It Works

1. **AI-first**: The orchestrator asks the LLM if it can answer from its own knowledge
2. **Web search**: If the LLM needs current/updated info, it triggers web search via Google (up to 10 results, or 50 with `--deep`)
3. **Domain-specific**: If you specify a website (e.g. "search on amazon.com"), it browses directly — no Google search
4. **Parallel subagents**: Complex tasks are split into subtasks, each handled by a separate browsing agent (max 3 by default)
5. **File analysis**: Upload files and the LLM analyzes/summarizes/compares them
6. **Skills**: The agent learns how to browse specific websites from `skills/*.md` files
7. **Guardrails**: Safety rules from `guardrails.md` are injected into all agents
8. **Conversation history**: Last 15 interactions are stored and used as context for future requests
9. **Request log**: All requests (including files provided) are logged to `~/.web_agent/request_log.json` and accessible via `--history` CLI flag, `/history` API endpoint, or the web UI
10. **User Memory**: Personal preferences and context stored in `~/.web_agent/MEMORY.md`, injected into all prompts
11. **Heartbeat**: Recurring tasks defined in `~/.web_agent/HEARTBEAT.md`, executed automatically on a schedule
12. **Cron**: Precise scheduled jobs (cron expressions, intervals, one-shot) stored in `~/.web_agent/cron/jobs.json`

---

## Configuration (`config.yaml`)

```yaml
# Server
server_host: "127.0.0.1"    # 0.0.0.0 to open to network
server_port: 8400

# LLM Provider (ollama, openai, anthropic, openrouter)
llm_provider: "ollama"
ollama_base_url: "http://localhost:11434"
ollama_model: "glm-5.1:cloud"     # Ollama model (auto-detected if empty)
llm_api_url: ""                   # API URL for cloud providers
llm_api_key: ""                   # API key for cloud providers
llm_model: ""                     # Model name for cloud providers

# Search
normal_search_results: 10   # results per normal search
deep_search_results: 50     # results per deep search

# Agents
max_subagents: 3            # max agents running simultaneously
subagent_depth_limit: 3
max_agent_iterations: 10

# Browser
headless: true
browser_timeout_ms: 30000

# Paths (leave empty for defaults)
skills_dir: ""
guardrails_file: ""

# History
max_history_entries: 15

# Heartbeat (recurring tasks)
heartbeat_enabled: false    # set true to enable
heartbeat_every: "30m"      # check interval

# Cron (precise scheduled jobs)
cron_enabled: false          # set true to enable
```

### LLM Providers

| Provider | Config | API Key Required |
|----------|--------|:---:|
| **Ollama** (local) | `ollama_base_url` + `ollama_model` | No |
| **OpenAI** | `llm_api_url` + `llm_api_key` + `llm_model` | Yes |
| **Anthropic** | `llm_api_url` + `llm_api_key` + `llm_model` | Yes |
| **OpenRouter** | `llm_api_url` + `llm_api_key` + `llm_model` | Yes |

Use `./web_agent_setup.py` to configure interactively, or edit `config.yaml` directly.

#### Ollama (default, local, free)

```yaml
llm_provider: "ollama"
ollama_base_url: "http://localhost:11434"
ollama_model: "glm-5.1:cloud"
```

#### OpenAI

```yaml
llm_provider: "openai"
llm_api_url: "https://api.openai.com/v1"
llm_api_key: "sk-..."
llm_model: "gpt-4o"
```

#### Anthropic

```yaml
llm_provider: "anthropic"
llm_api_url: "https://api.anthropic.com"
llm_api_key: "sk-ant-..."
llm_model: "claude-sonnet-4-20250514"
```

#### OpenRouter

```yaml
llm_provider: "openrouter"
llm_api_url: "https://openrouter.ai/api/v1"
llm_api_key: "sk-or-..."
llm_model: "openai/gpt-4o"
```

---

## User Memory (`~/.web_agent/MEMORY.md`)

The agent reads your personal memory file before every request. Store your preferences, personal context, and notes there.

**Template** (copy from `web_agent/defaults/MEMORY.md` to `~/.web_agent/MEMORY.md`):

```markdown
# User Memory

## Preferences
- Language: English
- Response style: concise and technical

## Personal Context
- I work as a software engineer
- I prefer Python for scripting
```

- **Long-term**: `MEMORY.md` + dated entries in `memory/YYYY-MM-DD.md`
- **Short-term**: Session observations kept in memory (max 10), flushable to long-term storage
- **API**: `GET /memory` to read, `POST /memory` with `{"content": "..."}` or `{"append": "..."}` or `{"short_term": "..."}` or `{"flush_short_term": "summary"}`

---

## Heartbeat (`~/.web_agent/HEARTBEAT.md`)

Recurring tasks that the agent executes automatically on a schedule. Inspired by OpenClaw's heartbeat system.

**Template** (copy from `web_agent/defaults/HEARTBEAT.md` to `~/.web_agent/HEARTBEAT.md`):

```markdown
---
tasks:
  - name: morning-briefing
    interval: 24h
    prompt: "Give me a morning briefing with top news"
  - name: github-check
    interval: 1h
    prompt: "Check my GitHub notifications"
---
```

Enable in `config.yaml`:

```yaml
heartbeat_enabled: true
heartbeat_every: "30m"
```

- **API**: `GET /heartbeat/status` returns task list and due tasks
- Agent replies `HEARTBEAT_OK` when nothing needs attention

---

## Cron Service (`~/.web_agent/cron/jobs.json`)

Precise scheduled task execution with three schedule types:

| Type | Format | Example |
|------|--------|---------|
| `cron` | Standard 5-field cron expression | `0 9 * * 1-5` (weekdays 9am) |
| `every` | Interval in seconds | `schedule_interval_seconds: 3600` (every hour) |
| `at` | ISO-8601 timestamp (one-shot) | `schedule_at: "2025-05-01T09:00:00"` |

Enable in `config.yaml`:

```yaml
cron_enabled: true
```

**Add a cron job via API:**

```bash
curl -X POST http://localhost:8400/cron -H 'Content-Type: application/json' -d '{
  "name": "daily-summary",
  "prompt": "Summarize today's Hacker News top posts",
  "schedule_kind": "cron",
  "schedule_expr": "0 9 * * *"
}'
```

**List jobs:** `GET /cron` | **Remove:** `DELETE /cron/{job_id}`

---

## Project Structure

```
web_agent_server.py       # Server entry point
web_agent.py              # CLI client entry point
web_agent_setup.py        # Interactive setup tool (provider & model config)
config.yaml               # Main configuration
guardrails.md             # Safety rules for all agents
skills/                   # Website navigation skills
  google-search/SKILL.md
  web-browsing/SKILL.md
  linkedin/SKILL.md
web_agent/
  server/                 # HTTP server (aiohttp) with CORS
  client/                 # HTTP client
  agent/                  # Orchestrator, BrowsingAgent, AnalysisAgent
  agent/request_log.py   # Structured request history logger (JSON)
  agent/user_memory.py   # User memory (MEMORY.md + short-term)
  agent/heartbeat.py     # Heartbeat runner (HEARTBEAT.md task scheduler)
  agent/cron_service.py  # Cron job service (precise scheduling)
  browser/                # Playwright browser session
  search/                 # Google search scraper
  llm/                    # Unified LLM client (Ollama, OpenAI, Anthropic, OpenRouter)
  skills/                 # Skill manager (SKILL.md loader)
  tools/                  # browser, web_search, web_fetch, file_analyzer
  config/                 # Settings (YAML loader)
  web/                    # Next.js frontend (TypeScript, Tailwind)
  cli/                    # CLI client
trash/                    # Downloaded files from browsing
```

---

## Skills

Skills are markdown files in `skills/<name>/SKILL.md` that teach the agent how to browse specific websites. They are automatically loaded when a query matches the skill's description.

To create a skill:

```markdown
---
name: my-site
description: "Browse my-site.com for X. Use when: user asks about X on my-site. NOT for: general searches."
website_url: "https://my-site.com"
---

# My Site Skill

## Instructions
1. Navigate to https://my-site.com/search?q={query}
2. Extract content from the results
```

---

## License

MIT

