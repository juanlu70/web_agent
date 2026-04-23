import asyncio
import logging
import traceback
from pathlib import Path

import streamlit as st

from web_agent.client import WebAgentClient
from web_agent.config.settings import Config, DEFAULT_CONFIG_PATH

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

st.set_page_config(
    page_title="Web Agent",
    page_icon="🌐",
    layout="wide",
)


def _get_or_create_event_loop():
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop


def run_async(coro):
    loop = _get_or_create_event_loop()
    return loop.run_until_complete(coro)


def init_session_state():
    defaults = {
        "messages": [],
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def render_history(client):
    st.subheader("📋 Request History")
    limit = st.number_input("Max entries to show", min_value=1, max_value=500, value=20, key="history_limit")
    if st.button("🔄 Load History", key="load_history"):
        try:
            data = run_async(client.get_history(limit=limit))
            entries = data.get("history", [])
            if not entries:
                st.info("No request history found.")
                return
            st.caption(f"Showing {len(entries)} of {data.get('count', len(entries))} entries")
            for i, entry in enumerate(reversed(entries), 1):
                ts = entry.get("timestamp", "?")
                query = entry.get("query", "")
                files = entry.get("file_paths", [])
                source = entry.get("source", "")
                deep = entry.get("deep", False)
                result = entry.get("result", "")
                result_preview = result[:300] + "..." if len(result) > 300 else result

                flags = []
                if deep:
                    flags.append("deep")
                flags.append(source)
                label = f"{ts} — {query[:80]}"
                if files:
                    label += f" [{len(files)} file(s)]"

                with st.expander(label):
                    st.markdown(f"**Query:** {query}")
                    if files:
                        st.markdown(f"**Files:** {', '.join(files)}")
                    st.markdown(f"**Mode:** {' | '.join(flags)}")
                    st.markdown(f"**Result:**\n\n{result_preview}")
        except Exception as e:
            st.warning(f"Cannot load history: {e}")


def render_sidebar():
    with st.sidebar:
        st.header("⚙️ Configuration")

        config_path = st.text_input("Config file (YAML)", value=str(DEFAULT_CONFIG_PATH), help="Path to config.yaml")
        config = Config.load(config_path)

        st.divider()
        st.subheader("🔌 Server Connection")
        server_url = st.text_input("Server URL", value=f"http://{config.server_host}:{config.server_port}")

        st.divider()
        st.subheader("Search Settings")
        deep = st.toggle("Deep Search Mode", value=False, help=f"Return up to {config.deep_search_results} results instead of {config.normal_search_results}")

        st.divider()
        st.subheader("File Analysis")
        uploaded_files = st.file_uploader(
            "Upload files to analyze (multiple allowed)",
            type=["txt", "md", "csv", "json", "py", "js", "ts", "html", "css", "xml", "yaml", "yml", "pdf", "docx"],
            accept_multiple_files=True,
            help="Upload one or more files for the agent to analyze",
        )

        st.divider()
        show_config = st.toggle("Show Server Config", value=False)
        if show_config:
            try:
                client = WebAgentClient(server_url=server_url, config=config)
                server_config = run_async(client.get_config())
                st.json(server_config)
            except Exception as e:
                st.warning(f"Cannot reach server: {e}")

        st.divider()
        verbose = st.toggle("Verbose Logging", value=False, help="Show debug-level logs")

        if st.button("🗑️ Clear Conversation", type="secondary"):
            st.session_state.messages = []
            st.rerun()

        if verbose:
            logging.getLogger().setLevel(logging.DEBUG)

        st.divider()
        show_history = st.toggle("📋 Request History", value=False, help="View request history from server")

        return server_url, config, deep, uploaded_files, show_history


def save_uploaded_file(uploaded_file) -> str:
    tmp_dir = Path.home() / ".web_agent" / "uploads"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    dest = tmp_dir / uploaded_file.name
    dest.write_bytes(uploaded_file.getbuffer())
    return str(dest)


def render_chat():
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"], unsafe_allow_html=True)


def main():
    init_session_state()
    server_url, config, deep, uploaded_files, show_history = render_sidebar()

    st.title("🌐 Web Agent")
    st.caption(f"Client connected to: {server_url}")

    client = WebAgentClient(server_url=server_url, config=config)

    if show_history:
        render_history(client)
        st.divider()

    try:
        health = run_async(client.health())
        st.success(f"Connected — Model: {health.get('model', '?')} | Subagents: {health.get('max_subagents', '?')}")
    except Exception:
        st.error(f"Cannot reach server at {server_url}. Start it with: `./web_agent.py`")

    render_chat()

    if prompt := st.chat_input("Type your request..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            file_paths = []
            if uploaded_files:
                for uf in uploaded_files:
                    file_paths.append(save_uploaded_file(uf))
                st.info(f"📎 Analyzing {len(uploaded_files)} file(s): {', '.join(uf.name for uf in uploaded_files)}")

            status_area = st.empty()
            result_area = st.empty()

            flags = []
            if deep:
                flags.append(f"🔍 Deep search ({config.deep_search_results} results)")
            else:
                flags.append(f"🔍 Normal search ({config.normal_search_results} results)")
            if file_paths:
                flags.append(f"📎 {len(file_paths)} file(s)")
            flags.append(f"🔌 Server: {server_url}")

            status_area.info(" | ".join(flags))

            try:
                status_area.info("⏳ Processing your request...")
                result = run_async(
                    client.request(prompt, deep=deep, file_paths=file_paths or None, sync=True)
                )
                status_val = result.get("status", "unknown")
                if status_val == "completed":
                    answer = result.get("result", "No result")
                    result_area.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                elif status_val == "failed":
                    error_msg = f"**Error:** {result.get('error', 'Unknown error')}"
                    result_area.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
                else:
                    result_area.json(result)
            except Exception as e:
                error_msg = f"**Error connecting to server:** {e}"
                result_area.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
            finally:
                status_area.empty()


if __name__ == "__main__":
    main()