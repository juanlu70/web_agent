import argparse
import asyncio
import json
import logging
import sys

from web_agent.client import WebAgentClient
from web_agent.config.settings import Config


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


async def send_request(client: WebAgentClient, query: str, deep: bool = False, file_paths: list[str] = None) -> str:
    try:
        result = await client.request(query, deep=deep, file_paths=file_paths, sync=True)
    except Exception as e:
        return f"Error connecting to server: {e}"

    status = result.get("status", "unknown")
    if status == "completed":
        return result.get("result", "No result")
    elif status == "failed":
        return f"Error: {result.get('error', 'Unknown error')}"
    else:
        return json.dumps(result, indent=2)


async def interactive_mode(client: WebAgentClient, deep: bool = False) -> None:
    try:
        health = await client.health()
        print(f"Connected to server: {health.get('model', 'unknown')} @ {health.get('host', '?')}:{health.get('port', '?')}")
    except Exception as e:
        print(f"Cannot connect to server: {e}")
        return

    print("web_agent client (type 'exit' or 'quit' to stop)")
    if deep:
        print(f"Deep search: ON ({client.config.deep_search_results} results)")
    else:
        print(f"Normal search: {client.config.normal_search_results} results")
    print("Tips:")
    print("  - prefix with 'file:path1,path2 ' to analyze files, e.g.: file:report.pdf,notes.md summarize")
    print("  - type 'exit' or 'quit' to stop")
    print()

    while True:
        try:
            request = input("You> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not request:
            continue
        if request.lower() in ("exit", "quit", "q"):
            print("Goodbye!")
            break

        file_paths = None
        if request.lower().startswith("file:"):
            parts = request.split(None, 1)
            file_part = parts[0][5:]
            file_paths = [f.strip() for f in file_part.split(",")]
            request = parts[1] if len(parts) > 1 else "analyze these files"

        try:
            result = await send_request(client, request, deep=deep, file_paths=file_paths)
            print(f"\nAgent> {result}\n")
        except KeyboardInterrupt:
            print("\nInterrupted.")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="web_agent_client",
        description="Client for the Web Agent server",
    )
    parser.add_argument(
        "request",
        nargs="*",
        help="The request to process (if omitted, enters interactive mode)",
    )
    parser.add_argument(
        "--files", "-f",
        nargs="+",
        default=None,
        dest="files",
        help="Files to analyze (supports multiple: -f file1.pdf file2.md)",
    )
    parser.add_argument(
        "--server",
        default=None,
        help="Server URL (default: from config.yaml)",
    )
    parser.add_argument(
        "--deep",
        action="store_true",
        help="Deep search mode: return up to 50 results instead of 10 (slower)",
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

    setup_logging(args.verbose)

    config = Config.load(args.config)

    client = WebAgentClient(server_url=args.server, config=config)

    request = " ".join(args.request) if args.request else None
    file_paths = args.files

    if request and file_paths:
        result = asyncio.run(send_request(client, request, deep=args.deep, file_paths=file_paths))
        print(result)
    elif request:
        result = asyncio.run(send_request(client, request, deep=args.deep))
        print(result)
    elif file_paths:
        result = asyncio.run(send_request(client, "analyze these files", deep=args.deep, file_paths=file_paths))
        print(result)
    else:
        asyncio.run(interactive_mode(client, deep=args.deep))


if __name__ == "__main__":
    main()