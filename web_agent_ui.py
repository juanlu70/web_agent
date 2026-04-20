#!/usr/bin/env python3
"""Launch the Streamlit web interface for web_agent.

Usage:
    streamlit run web_agent_ui.py
"""

import subprocess
import sys

subprocess.run(
    [sys.executable, "-m", "streamlit", "run", "web_agent/ui/app.py"],
    check=True,
)