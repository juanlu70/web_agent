# Heartbeat

This file defines recurring tasks that the agent should execute automatically on a schedule.

## Tasks

Define tasks in the YAML frontmatter below. Each task has:
- `name`: A unique identifier
- `interval`: How often to run (e.g., 30m, 1h, 24h)
- `prompt`: What the agent should do when the task fires

---

```yaml
tasks:
  # Example tasks (uncomment and edit to use):
  # - name: morning-briefing
  #   interval: 24h
  #   prompt: "Give me a morning briefing with today's top news, weather, and my calendar events"
  # - name: email-check
  #   interval: 30m
  #   prompt: "Check for any urgent unread emails"
  # - name: github-review
  #   interval: 1h
  #   prompt: "Check my GitHub notifications for new PRs or issues"
```

## Instructions

If nothing needs attention, the agent will reply `HEARTBEAT_OK`.
To enable heartbeat, set `heartbeat_enabled: true` in `config.yaml`.