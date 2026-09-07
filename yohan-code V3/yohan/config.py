"""
YOHAN CODE - Configuration & API Key Manager
Loads all API keys from .env with automatic rotation support.
"""

import os
import re
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
ENV_PATH = Path(__file__).parent.parent / ".env"
load_dotenv(ENV_PATH)

VERSION = "1.0.0"
APP_NAME = "YOHAN CODE"

# ─── Provider definitions ────────────────────────────────────────────────────

PROVIDERS = {
    "groq": {
        "name": "Groq",
        "base_url": "https://api.groq.com/openai/v1",
        "models": [
            "openai/gpt-oss-120b",
            "openai/gpt-oss-20b",
            "qwen/qwen3.6-27b",
            "qwen/qwen3.8-27b",
        ],
        "default_model": "openai/gpt-oss-20b",
        "env_prefix": "GROQ_API",
        "type": "openai_compat",
        "supports_model_list": True,
    },
    "gemini": {
        "name": "Google Gemini",
        "base_url": "https://generativelanguage.googleapis.com/v1beta",
        "models": [
            "gemini-3.5-flash",
            "gemini-3.1-flash-lite",
            "gemini-3-pro",
            "gemini-2.5-flash",
        ],
        "default_model": "gemini-3.5-flash",
        "env_prefix": "GEMINI_API",
        "type": "gemini",
    },
    "cloudflare": {
        "name": "Cloudflare Workers AI",
        "base_url": "https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/v1",
        "models": [
            "@cf/meta/llama-3.3-70b-instruct-fp8-fast",
            "@cf/meta/llama-3.1-8b-instruct-fp8",
            "@cf/meta/llama-3.2-3b-instruct",
            "@cf/meta/llama-4-scout-17b-16e-instruct",
            "@cf/qwen/qwen3-30b-a3b-fp8",
            "@cf/qwen/qwq-32b",
            "@cf/deepseek/deepseek-r1-distill-qwen-32b",
            "@cf/mistral/mistral-small-3.1-24b-instruct",
            "@cf/openai/gpt-oss-20b",
            "@cf/openai/gpt-oss-120b",
        ],
        "default_model": "@cf/meta/llama-3.3-70b-instruct-fp8-fast",
        "env_prefix": "CLOUDFLARE_API",
        "type": "openai_compat",
        "extra_env": "CLOUDFLARE_ACCOUNT_ID",
    },
    "openrouter": {
        "name": "OpenRouter",
        "base_url": "https://openrouter.ai/api/v1",
        "models": [
            "meta-llama/llama-3.3-70b-instruct",
            "google/gemini-2.0-flash-exp:free",
            "deepseek/deepseek-chat",
            "mistralai/mixtral-8x7b-instruct",
            "anthropic/claude-3-haiku",
            "openai/gpt-4o-mini",
            "qwen/qwen-2.5-72b-instruct",
        ],
        "default_model": "meta-llama/llama-3.3-70b-instruct",
        "env_prefix": "OPENROUTER_API",
        "type": "openai_compat",
    },
    "openai": {
        "name": "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "models": [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-3.5-turbo",
        ],
        "default_model": "gpt-4o-mini",
        "env_prefix": "OPENAI_API",
        "type": "openai_compat",
    },
    "anthropic": {
        "name": "Anthropic",
        "base_url": "https://api.anthropic.com/v1",
        "models": [
            "claude-opus-5",
            "claude-sonnet-5",
            "claude-haiku-4-5-20251001",
            "claude-sonnet-4-6",
        ],
        "default_model": "claude-haiku-4-5-20251001",
        "env_prefix": "ANTHROPIC_API",
        "type": "anthropic",
    },
    "mistral": {
        "name": "Mistral AI",
        "base_url": "https://api.mistral.ai/v1",
        "models": [
            "mistral-large-latest",
            "mistral-small-latest",
            "open-mixtral-8x22b",
            "open-mistral-7b",
        ],
        "default_model": "mistral-small-latest",
        "env_prefix": "MISTRAL_API",
        "type": "openai_compat",
    },
    "cohere": {
        "name": "Cohere",
        "base_url": "https://api.cohere.ai/v1",
        "models": [
            "command-r-plus",
            "command-r",
            "command",
        ],
        "default_model": "command-r",
        "env_prefix": "COHERE_API",
        "type": "cohere",
    },
}


def load_keys(provider_id: str) -> list[str]:
    """Load all API keys for a provider from .env (PROVIDER_API_1, _2, _3, ...)"""
    prefix = PROVIDERS[provider_id]["env_prefix"]
    keys = []

    # Load numbered keys: PREFIX_1, PREFIX_2, ...
    i = 1
    while True:
        key = os.getenv(f"{prefix}_{i}")
        if key and key.strip():
            keys.append(key.strip())
            i += 1
        else:
            break

    # Also accept bare PREFIX (no number)
    bare = os.getenv(prefix)
    if bare and bare.strip() and bare.strip() not in keys:
        keys.insert(0, bare.strip())

    return keys


def get_all_available_providers() -> dict:
    """Returns providers that have at least one API key configured."""
    available = {}
    for pid, pconf in PROVIDERS.items():
        keys = load_keys(pid)
        if keys:
            available[pid] = {**pconf, "keys": keys}
    return available


def get_default_provider() -> str:
    """Returns the first available provider."""
    available = get_all_available_providers()
    if not available:
        return None
    # Priority order
    priority = ["groq", "gemini", "openrouter", "cloudflare", "openai", "anthropic", "mistral", "cohere"]
    for p in priority:
        if p in available:
            return p
    return list(available.keys())[0]


def get_cloudflare_account_id() -> str:
    return os.getenv("CLOUDFLARE_ACCOUNT_ID", "")
