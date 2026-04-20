#!/usr/bin/env python3
import argparse
import logging
import sys

from web_agent.config.settings import Config


def main():
    parser = argparse.ArgumentParser(
        prog="web_agent",
        description="Web Agent server - a daemon that processes requests via HTTP API",
    )
    parser.add_argument(
        "--host",
        default=None,
        help="Server host (default: from config.yaml)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Server port (default: from config.yaml)",
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Path to config.yaml file",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    config = Config.load(args.config)

    if args.host:
        config.server_host = args.host
    if args.port:
        config.server_port = args.port

    from web_agent.server import WebAgentServer

    server = WebAgentServer(config)
    print(f"Web Agent server starting on http://{config.server_host}:{config.server_port}")
    print(f"Model: {config.ollama_model} | Max subagents: {config.max_subagents}")
    print(f"Endpoints:")
    print(f"  POST /request  - Send a query (JSON: {{\"query\": \"...\", \"deep\": false, \"file_path\": null, \"sync\": true}})")
    print(f"  GET  /health    - Check server health")
    print(f"  GET  /config    - Get server configuration")
    print(f"  GET  /status/{{task_id}} - Check async task status")
    print()

    server.run(host=config.server_host, port=config.server_port)


if __name__ == "__main__":
    main()