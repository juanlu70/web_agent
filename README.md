# Web Agent

A browser agent managed by IA. It searches the web, gathers information, and analyzes files — powered by a local LLM via Ollama.

It is intended as a mix of a personal Perplexity and OpenClaw but without the insecure environment of OpenClaw.


## Architecture

```
┌──────────────┐   ┌─────────────┐   ┌─────────────┐
│  CLI Client  │   │  Streamlit  │   │  HTTP API   │
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
- [Ollama](https://ollama.ai) running locally with a model pulled (e.g. `ollama pull glm-5.1:cloud`)
- Chromium (for Playwright — auto-installed)

## Install

```bash
pip install -r requirements.txt
playwright install chromium
```

## Quick Start

**1. Start the server:**

```bash
./web_agent.py
```

**2. Query from a client:**

```bash
# Single query
./web_agent_client.py "search for wireless headphones"

# Interactive mode
./web_agent_client.py

# Web UI
streamlit run web_agent/ui/app.py
```

---

## Server (`web_agent.py`)

The server is a daemon that listens for HTTP requests and runs the orchestrator with browsing agents.

```bash
./web_agent.py [OPTIONS]
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

---

## CLI Client (`web_agent_client.py`)

```bash
./web_agent_client.py [REQUEST] [OPTIONS]
```

If no request is given, enters interactive mode.

| Flag | Default | Description |
|------|---------|-------------|
| `--files`, `-f` | none | Files to analyze (supports multiple: `-f a.pdf b.md`) |
| `--server` | from config | Server URL (e.g. `http://192.168.1.10:8400`) |
| `--deep` | off | Deep search: 50 results instead of 10 |
| `--config` | `config.yaml` | Path to YAML config file |
| `--verbose`, `-v` | off | Enable debug logging |

### Examples

```bash
# Web search
./web_agent_client.py "search for Python async tutorials"

# Deep search (50 results, slower)
./web_agent_client.py --deep "compare React vs Vue frameworks"

# Analyze one file
./web_agent_client.py -f report.pdf "summarize this report"

# Analyze multiple files
./web_agent_client.py -f report.pdf notes.md data.csv "compare these documents"

# Connect to remote server
./web_agent_client.py --server http://192.168.1.10:8400 "search for laptops"

# Interactive mode
./web_agent_client.py
You> search for wireless headphones
You> file:report.pdf,notes.md compare both
You> exit
```

---

## Streamlit Web UI

```bash
streamlit run web_agent/ui/app.py
```

The sidebar provides controls for all settings: server URL, deep search, file upload (multiple files), config display, and logging. Opens at `http://localhost:8501`.

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

---

## Configuration (`config.yaml`)

```yaml
# Server
server_host: "127.0.0.1"    # 0.0.0.0 to open to network
server_port: 8400

# LLM
ollama_base_url: "http://localhost:11434"
ollama_model: "glm-5.1:cloud"

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
```

---

## Project Structure

```
web_agent.py              # Server entry point
web_agent_client.py       # CLI client entry point
config.yaml               # Main configuration
guardrails.md             # Safety rules for all agents
skills/                   # Website navigation skills
  google-search/SKILL.md
  web-browsing/SKILL.md
  linkedin/SKILL.md
web_agent/
  server/                 # HTTP server (aiohttp)
  client/                 # HTTP client
  agent/                  # Orchestrator, BrowsingAgent, AnalysisAgent
  browser/                # Playwright browser session
  search/                 # Google search scraper
  llm/                    # Ollama API client
  skills/                 # Skill manager (SKILL.md loader)
  tools/                  # browser, web_search, web_fetch, file_analyzer
  config/                 # Settings (YAML loader)
  ui/                     # Streamlit app
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

