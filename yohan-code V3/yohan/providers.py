"""
YOHAN CODE - AI Providers with automatic key rotation
Rotates keys within the same provider on rate limit / error.
"""

import os
import json
import time
import httpx
from typing import Iterator, AsyncIterator
from yohan.config import PROVIDERS, load_keys, get_cloudflare_account_id


def _raise_clear_http_error(resp: httpx.Response) -> None:
    """Raise a human-readable error from an HTTP response."""
    try:
        body = resp.json()
        # OpenAI-style: { "error": { "message": "..." } }
        msg = (body.get("error", {}) or {}).get("message") or str(body)
    except Exception:
        msg = resp.text[:300] or f"HTTP {resp.status_code}"
    raise RuntimeError(f"API error {resp.status_code}: {msg}")


class RateLimitError(Exception):
    pass


class AllKeysExhausted(Exception):
    """All keys for this provider are rate limited."""
    pass


class ProviderKeyRotator:
    """Manages key rotation for a single provider."""

    def __init__(self, provider_id: str):
        self.provider_id = provider_id
        self.config = PROVIDERS[provider_id]
        self._keys: list[str] = []
        self._exhausted: set[str] = set()
        self._current_index = 0
        self._reload_keys()

    def _reload_keys(self):
        """Reload keys from environment (picks up new keys added at runtime)."""
        self._keys = load_keys(self.provider_id)

    def get_current_key(self) -> str | None:
        available = [k for k in self._keys if k not in self._exhausted]
        if not available:
            return None
        idx = self._current_index % len(available)
        return available[idx]

    def rotate(self) -> str | None:
        """Mark current key as exhausted, move to next."""
        current = self.get_current_key()
        if current:
            self._exhausted.add(current)
        self._reload_keys()  # Maybe new keys were added to .env
        return self.get_current_key()

    def all_exhausted(self) -> bool:
        self._reload_keys()
        available = [k for k in self._keys if k not in self._exhausted]
        return len(available) == 0

    def reset(self):
        self._exhausted.clear()
        self._current_index = 0

    def has_keys(self) -> bool:
        self._reload_keys()
        return len(self._keys) > 0


def _parse_sse_json(data: str):
    """Parse an SSE data payload, tolerating gateways that split JSON across
    data lines with or without newline semantics."""
    for candidate in (data, data.replace("\n", "")):
        try:
            obj = json.loads(candidate)
            return obj if isinstance(obj, dict) else None
        except Exception:
            continue
    return None


def _extract_delta_content(chunk: dict):
    """Return delta content as a string, or None if this chunk has none.

    Never truthiness-test the content: gateways may serialize numeric
    fragments as raw JSON numbers (0, 5, 42), and 0 is falsy — `if delta`
    silently drops every "0" in the stream.
    """
    try:
        delta = chunk["choices"][0]["delta"]
    except Exception:
        return None
    if not isinstance(delta, dict):
        return None
    content = delta.get("content")
    if content is None:
        return None
    return content if isinstance(content, str) else str(content)


class AIProvider:
    """Base provider with key rotation and streaming support."""

    def __init__(self, provider_id: str):
        self.provider_id = provider_id
        self.config = PROVIDERS[provider_id]
        self.rotator = ProviderKeyRotator(provider_id)

    def _build_url(self, endpoint: str) -> str:
        base = self.config["base_url"]
        if self.provider_id == "cloudflare":
            account_id = get_cloudflare_account_id()
            if not account_id:
                raise RuntimeError(
                    "CLOUDFLARE_ACCOUNT_ID is not set in .env\n"
                    "Add: CLOUDFLARE_ACCOUNT_ID=your_account_id"
                )
            base = base.format(account_id=account_id)
        return f"{base}{endpoint}"

    def _is_rate_limit(self, status_code: int, body: str) -> bool:
        if status_code == 429:
            return True
        if status_code in (401, 403):
            return True  # Invalid key, rotate
        return False

    def chat(
        self,
        messages: list[dict],
        model: str | None = None,
        stream: bool = True,
        max_tokens: int = 8192,
        system: str | None = None,
        **kwargs,
    ) -> Iterator[str]:
        """Chat with automatic key rotation on failure."""
        model = model or self.config["default_model"]

        while True:
            key = self.rotator.get_current_key()
            if key is None:
                raise AllKeysExhausted(
                    f"All API keys for {self.config['name']} are exhausted. "
                    f"Please add more keys to .env"
                )

            try:
                yield from self._do_chat(key, messages, model, stream, max_tokens, system, **kwargs)
                return  # Success
            except RateLimitError:
                next_key = self.rotator.rotate()
                if next_key is None:
                    raise AllKeysExhausted(
                        f"All API keys for {self.config['name']} are rate limited. "
                        f"Please add more keys to .env"
                    )
                # Try next key
                continue

    def _do_chat(self, key, messages, model, stream, max_tokens, system, **kwargs) -> Iterator[str]:
        ptype = self.config["type"]
        if ptype == "openai_compat":
            yield from self._openai_chat(key, messages, model, stream, max_tokens, system)
        elif ptype == "gemini":
            yield from self._gemini_chat(key, messages, model, stream, max_tokens, system)
        elif ptype == "anthropic":
            yield from self._anthropic_chat(key, messages, model, stream, max_tokens, system)
        elif ptype == "cohere":
            yield from self._cohere_chat(key, messages, model, stream, max_tokens, system)
        else:
            raise ValueError(f"Unknown provider type: {ptype}")

    # ── OpenAI-compatible (Groq, OpenRouter, Cloudflare, OpenAI, Mistral) ────

    def _sanitize_messages(self, messages: list[dict]) -> list[dict]:
        """Merge consecutive same-role messages to maintain user/assistant alternation.

        Some models (Mistral on Cloudflare, older Llama) reject histories where
        two user or two assistant messages appear in a row. This collapses them.
        """
        if not messages:
            return messages

        def to_str(content) -> str:
            """Coerce any content value to a plain string safely."""
            if content is None:
                return ""
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                # Anthropic-style content blocks: [{"type": "text", "text": "..."}, ...]
                parts = []
                for block in content:
                    if isinstance(block, dict):
                        parts.append(block.get("text") or block.get("content") or str(block))
                    else:
                        parts.append(str(block))
                return "\n".join(parts)
            # int, float, bool, or anything unexpected — just stringify
            return str(content)

        merged: list[dict] = []
        for msg in messages:
            entry = {"role": msg["role"], "content": to_str(msg.get("content"))}
            if merged and entry["role"] == merged[-1]["role"]:
                merged[-1]["content"] += "\n\n" + entry["content"]
            else:
                merged.append(entry)
        return merged

    def _openai_chat(self, key, messages, model, stream, max_tokens, system) -> Iterator[str]:
        url = self._build_url("/chat/completions")
        all_messages = []
        if system:
            all_messages.append({"role": "system", "content": system})
        all_messages.extend(self._sanitize_messages(messages))

        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }
        if self.provider_id == "openrouter":
            headers["HTTP-Referer"] = "https://yohan-code"
            headers["X-Title"] = "YOHAN CODE"

        payload = {
            "model": model,
            "messages": all_messages,
            "stream": stream,
            "max_tokens": max_tokens,
        }

        with httpx.Client(timeout=120) as client:
            if stream:
                with client.stream("POST", url, headers=headers, json=payload) as resp:
                    if self._is_rate_limit(resp.status_code, ""):
                        raise RateLimitError()
                    if not resp.is_success:
                        resp.read()
                        _raise_clear_http_error(resp)
                    # Proper SSE event parsing: an event may span multiple
                    # `data:` lines (joined per the SSE spec), and some gateways
                    # (Cloudflare) send `data:` without a space, split chunks
                    # across lines, or emit delta content as raw JSON numbers
                    # instead of strings ("content": 0). The old code parsed
                    # each line on its own, silently dropped unparseable
                    # fragments, and truthiness-tested content — so numeric 0
                    # was eaten and digits crashed str+int concatenation.
                    data_lines: list[str] = []
                    for line in resp.iter_lines():
                        if line.startswith(":"):
                            continue  # SSE comment / keep-alive
                        if line.startswith("data:"):
                            data_lines.append(line[5:].lstrip(" "))
                            continue
                        if line == "":
                            if not data_lines:
                                continue  # event separator with no payload
                            data = "\n".join(data_lines)
                            data_lines.clear()
                            if data.strip() == "[DONE]":
                                break
                            chunk = _parse_sse_json(data)
                            if chunk is not None:
                                delta = _extract_delta_content(chunk)
                                if delta is not None:
                                    yield delta
                    # Flush a trailing event if the stream ended without a
                    # final blank line.
                    if data_lines:
                        data = "\n".join(data_lines)
                        if data.strip() != "[DONE]":
                            chunk = _parse_sse_json(data)
                            if chunk is not None:
                                delta = _extract_delta_content(chunk)
                                if delta is not None:
                                    yield delta
            else:
                resp = client.post(url, headers=headers, json=payload)
                if self._is_rate_limit(resp.status_code, resp.text):
                    raise RateLimitError()
                if not resp.is_success:
                    _raise_clear_http_error(resp)
                yield resp.json()["choices"][0]["message"]["content"]

    # ── Gemini ───────────────────────────────────────────────────────────────

    def _gemini_chat(self, key, messages, model, stream, max_tokens, system) -> Iterator[str]:
        endpoint = "stream" if stream else "generate"
        action = "streamGenerateContent" if stream else "generateContent"
        url = f"{self.config['base_url']}/models/{model}:{action}?key={key}"

        contents = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})

        payload = {
            "contents": contents,
            "generationConfig": {"maxOutputTokens": max_tokens},
        }
        if system:
            payload["systemInstruction"] = {"parts": [{"text": system}]}

        with httpx.Client(timeout=120) as client:
            if stream:
                with client.stream("POST", url, json=payload) as resp:
                    if self._is_rate_limit(resp.status_code, ""):
                        raise RateLimitError()
                    if not resp.is_success:
                        resp.read()
                        _raise_clear_http_error(resp)
                    buffer = ""
                    for chunk in resp.iter_text():
                        buffer += chunk
                        try:
                            for item in self._parse_gemini_stream(buffer):
                                text = (item.get("candidates", [{}])[0]
                                        .get("content", {})
                                        .get("parts", [{}])[0]
                                        .get("text", ""))
                                if text:
                                    yield text
                            buffer = ""
                        except Exception:
                            continue
            else:
                resp = client.post(url, json=payload)
                if self._is_rate_limit(resp.status_code, resp.text):
                    raise RateLimitError()
                if not resp.is_success:
                    _raise_clear_http_error(resp)
                data = resp.json()
                text = (data.get("candidates", [{}])[0]
                        .get("content", {})
                        .get("parts", [{}])[0]
                        .get("text", ""))
                yield text

    def _parse_gemini_stream(self, buffer: str) -> list:
        """Parse Gemini's chunked JSON array stream."""
        results = []
        decoder = json.JSONDecoder()
        # Work on a local copy so we don't mutate the caller's buffer mid-loop
        remaining = buffer.lstrip(" \n\r,[]")
        while remaining:
            try:
                obj, end = decoder.raw_decode(remaining)
                results.append(obj)
                # Advance past what we just parsed, skip separators
                remaining = remaining[end:].lstrip(" \n\r,[]")
            except json.JSONDecodeError:
                break
        return results

    # ── Anthropic ────────────────────────────────────────────────────────────

    def _anthropic_chat(self, key, messages, model, stream, max_tokens, system) -> Iterator[str]:
        url = self._build_url("/messages")
        headers = {
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "stream": stream,
        }
        if system:
            payload["system"] = system

        with httpx.Client(timeout=120) as client:
            if stream:
                with client.stream("POST", url, headers=headers, json=payload) as resp:
                    if self._is_rate_limit(resp.status_code, ""):
                        raise RateLimitError()
                    if not resp.is_success:
                        resp.read()
                        _raise_clear_http_error(resp)
                    for line in resp.iter_lines():
                        if line.startswith("data: "):
                            try:
                                data = json.loads(line[6:])
                                if data.get("type") == "content_block_delta":
                                    yield data["delta"].get("text", "")
                            except Exception:
                                continue
            else:
                resp = client.post(url, headers=headers, json=payload)
                if self._is_rate_limit(resp.status_code, resp.text):
                    raise RateLimitError()
                if not resp.is_success:
                    _raise_clear_http_error(resp)
                yield resp.json()["content"][0]["text"]

    # ── Cohere ───────────────────────────────────────────────────────────────

    def _cohere_chat(self, key, messages, model, stream, max_tokens, system) -> Iterator[str]:
        url = self._build_url("/chat")
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }
        # Convert to Cohere format
        chat_history = []
        user_message = ""
        for msg in messages:
            if msg["role"] == "user":
                user_message = msg["content"]
            else:
                chat_history.append({
                    "role": "CHATBOT",
                    "message": msg["content"],
                })

        payload = {
            "model": model,
            "message": user_message,
            "chat_history": chat_history,
            "stream": stream,
            "max_tokens": max_tokens,
        }
        if system:
            payload["preamble"] = system

        with httpx.Client(timeout=120) as client:
            if stream:
                with client.stream("POST", url, headers=headers, json=payload) as resp:
                    if self._is_rate_limit(resp.status_code, ""):
                        raise RateLimitError()
                    if not resp.is_success:
                        resp.read()
                        _raise_clear_http_error(resp)
                    for line in resp.iter_lines():
                        try:
                            data = json.loads(line)
                            if data.get("event_type") == "text-generation":
                                yield data.get("text", "")
                        except Exception:
                            continue
            else:
                resp = client.post(url, headers=headers, json=payload)
                if self._is_rate_limit(resp.status_code, resp.text):
                    raise RateLimitError()
                if not resp.is_success:
                    _raise_clear_http_error(resp)
                yield resp.json().get("text", "")


# ── Provider Registry ─────────────────────────────────────────────────────────

_provider_cache: dict[str, AIProvider] = {}


def get_provider(provider_id: str) -> AIProvider:
    if provider_id not in _provider_cache:
        _provider_cache[provider_id] = AIProvider(provider_id)
    return _provider_cache[provider_id]


# ── Dynamic model listing ─────────────────────────────────────────────────────

def fetch_models(provider_id: str) -> list[str] | None:
    """Fetch available models from provider API. Returns None if not supported."""
    from yohan.config import PROVIDERS, load_keys
    config = PROVIDERS[provider_id]

    # Only providers with OpenAI-compat /models endpoint
    if not config.get("supports_model_list"):
        return None

    keys = load_keys(provider_id)
    if not keys:
        return None

    key = keys[0]
    base_url = config["base_url"]

    # Cloudflare has dynamic base_url, skip
    if "{account_id}" in base_url:
        return None

    try:
        with httpx.Client(timeout=10) as client:
            resp = client.get(
                f"{base_url}/models",
                headers={"Authorization": f"Bearer {key}"},
            )
            if not resp.is_success:
                return None
            data = resp.json()
            models = [m["id"] for m in data.get("data", [])
                      if m.get("id") and "whisper" not in m["id"].lower()
                      and "guard" not in m["id"].lower()]
            return sorted(models) if models else None
    except Exception:
        return None
