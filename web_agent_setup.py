#!/usr/bin/env python3
"""Interactive setup tool for web_agent — configure LLM provider and model."""

import asyncio
import sys

from web_agent.config.settings import Config, DEFAULT_CONFIG_PATH
from web_agent.llm.llm_client import LLMClient, PROVIDERS, list_providers, get_provider_info


def print_header():
    print()
    print("=" * 50)
    print("  Web Agent Setup")
    print("=" * 50)
    print()


def print_current_config(config: Config):
    provider = config.llm_provider
    print(f"  Current provider: {provider}")
    if provider == "ollama":
        print(f"  Ollama URL:   {config.ollama_base_url}")
        print(f"  Ollama model: {config.effective_model}")
    else:
        info = get_provider_info(provider)
        print(f"  API URL:  {config.llm_api_url or info.get('default_url', 'not set')}")
        print(f"  Model:    {config.llm_model or 'not set'}")
        print(f"  API key:  {'configured' if config.llm_api_key else 'not set'}")
    print()


def select_provider(config: Config) -> str:
    providers = list_providers()
    print("Available LLM providers:")
    print()
    for i, p in enumerate(providers, 1):
        marker = " (current)" if p["id"] == config.llm_provider else ""
        key_needed = " [requires API key]" if p["needs_api_key"] else ""
        print(f"  {i}. {p['name']}{key_needed}{marker}")
    print()

    current_idx = next(i for i, p in enumerate(providers) if p["id"] == config.llm_provider) + 1
    choice = input(f"Select provider [{current_idx}]: ").strip()
    if not choice:
        choice = str(current_idx)
    try:
        idx = int(choice)
        if 1 <= idx <= len(providers):
            return providers[idx - 1]["id"]
    except ValueError:
        pass
    print("Invalid choice, keeping current provider.")
    return config.llm_provider


async def setup_ollama(config: Config) -> Config:
    print()
    url = input(f"Ollama URL [{config.ollama_base_url}]: ").strip()
    if url:
        config.ollama_base_url = url

    print()
    print("Checking Ollama for available models...")

    from web_agent.llm.llm_client import OllamaClient
    client = OllamaClient(base_url=config.ollama_base_url, model="")

    if not await client.is_available():
        print(f"Cannot connect to Ollama at {config.ollama_base_url}")
        print("Make sure Ollama is running (https://ollama.ai)")
        model = input("Enter model name manually: ").strip()
        if model:
            config.ollama_model = model
        return config

    models = await client.list_models()
    if not models:
        print("No models found. Enter model name manually.")
        model = input("Model name: ").strip()
        if model:
            config.ollama_model = model
        return config

    print()
    print("Available models:")
    for i, m in enumerate(models, 1):
        size_mb = m.get("size", 0) / (1024 * 1024) if m.get("size") else 0
        marker = " (current)" if m["name"] == config.ollama_model else ""
        size_str = f" ({size_mb:.0f} MB)" if size_mb else ""
        print(f"  {i}. {m['name']}{size_str}{marker}")
    print()

    current_idx = None
    for i, m in enumerate(models, 1):
        if m["name"] == config.ollama_model:
            current_idx = i

    prompt = f"Select model [{current_idx or 1}]: "
    choice = input(prompt).strip()
    if not choice and current_idx:
        config.ollama_model = models[current_idx - 1]["name"]
    else:
        try:
            idx = int(choice)
            if 1 <= idx <= len(models):
                config.ollama_model = models[idx - 1]["name"]
            else:
                print("Invalid choice, keeping current model.")
        except ValueError:
            config.ollama_model = choice

    return config


def setup_cloud_provider(config: Config, provider: str) -> Config:
    info = get_provider_info(provider)
    print()
    print(f"  Setting up {info['name']}")
    print()

    default_url = info.get("default_url", "")
    current_url = config.llm_api_url or default_url
    url = input(f"API URL [{current_url}]: ").strip()
    config.llm_api_url = url if url else current_url

    key = input("API key (leave empty to keep current): ").strip()
    if key:
        config.llm_api_key = key
    elif not config.llm_api_key:
        print("  Warning: no API key set. The provider will not work without it.")

    models = info.get("models", [])
    if models:
        print()
        print("  Available models:")
        for i, m in enumerate(models, 1):
            marker = " (current)" if m["name"] == config.llm_model else ""
            print(f"    {i}. {m['name']}{marker}")
        print()

        current_idx = None
        for i, m in enumerate(models, 1):
            if m["name"] == config.llm_model:
                current_idx = i

        prompt = f"  Select model [{current_idx or 1}]: "
        choice = input(prompt).strip()
        if not choice and current_idx:
            config.llm_model = models[current_idx - 1]["name"]
        else:
            try:
                idx = int(choice)
                if 1 <= idx <= len(models):
                    config.llm_model = models[idx - 1]["name"]
            except ValueError:
                if choice:
                    config.llm_model = choice
    else:
        model = input(f"  Model name [{info.get('default_model', config.llm_model)}]: ").strip()
        config.llm_model = model or config.llm_model or info.get("default_model", "")

    config.llm_provider = provider
    return config


def main():
    print_header()

    config_path = str(DEFAULT_CONFIG_PATH)
    config = Config.load(config_path)
    print_current_config(config)

    provider = select_provider(config)
    config.llm_provider = provider

    if provider == "ollama":
        config = asyncio.run(setup_ollama(config))
    else:
        config = setup_cloud_provider(config, provider)

    print()
    print("-" * 50)
    print("  Configuration summary:")
    print()
    print(f"  Provider: {config.llm_provider}")
    if config.llm_provider == "ollama":
        print(f"  Ollama URL:   {config.ollama_base_url}")
        print(f"  Model:         {config.effective_model}")
    else:
        print(f"  API URL:  {config.llm_api_url}")
        print(f"  Model:     {config.llm_model}")
        print(f"  API key:   {'*' * 8 if config.llm_api_key else 'not set'}")
    print()

    save = input("Save configuration? [Y/n]: ").strip().lower()
    if save not in ("n", "no"):
        config.save(config_path)
        print(f"  Saved to {config_path}")
    else:
        print("  Configuration not saved.")

    print()
    print("Setup complete. You can now start the server with: ./web_agent.py")
    print()


if __name__ == "__main__":
    main()