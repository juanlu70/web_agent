#!/usr/bin/env python3
"""Launch the Next.js web interface for web_agent.

Usage:
    ./web_agent_ui.py          # starts dev server on port 3000
    ./web_agent_ui.py --build  # builds for production first
"""

import subprocess
import sys
import os

WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web_agent", "web")


def main():
    build = "--build" in sys.argv
    os.chdir(WEB_DIR)

    if build:
        subprocess.run(["pnpm", "build"], check=True)
        subprocess.run(["pnpm", "start"], check=True)
    else:
        subprocess.run(["pnpm", "dev"], check=True)


if __name__ == "__main__":
    main()