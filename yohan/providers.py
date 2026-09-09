"""
YOHAN CODE - AI Providers with automatic key rotation
Rotates keys within the same provider on rate limit / error.
"""

import os
import json
import time
import httpx
from typing import Iterator, AsyncIterator
from yohan.config import PROVIDERS, load_keys, get_cloudflare_account_id, get_cloudflare_account_id_for_key, get_cloudflare_account_id_for_key


def _raise_clear_http_error(resp: httpx.Response) -> None:
    """Raise a human-readable error from an HTTP response."""
    try:
        body = resp.json()
        # OpenAI-style: { "error": { "message": "..." } }
        msg = (body.get("error", {}) or {}).get("message") or str(body)
    except Exception:
        msg = resp.text[:300] or f"HTTP {resp.status_code}"
    if "User location is not supported" in msg:
        msg += (
            " | This is a Google region/network block, not a key-format issue. "
            "For Google AI Studio keys, use a network/region supported by Google Gemini, "
            "or explicitly configure a Gemini-compatible proxy with GEMINI_API_TYPE/GEMINI_BASE_URL."
        )
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
        self._manual_index: int | None = None  # For /keys select
        self._reload_keys()

    def _reload_keys(self):
        """Reload keys from environment (picks up new keys added at runtime)."""
        old_keys = self._keys
        self._keys = load_keys(self.provider_id)
        # If keys changed, reset exhausted set for keys that no longer exist
        self._exhausted = {k for k in self._exhausted if k in self._keys}
        # Adjust manual index if out of bounds
        if self._manual_index is not None and self._manual_index >= len(self._keys):
            self._manual_index = None

    def get_current_key(self) -> str | None:
        available = [k for k in self._keys if k not in self._exhausted]
        if not available:
            return None
        # If manually selected, use that key (if available)
        if self._manual_index is not None:
            idx = self._manual_index % len(self._keys)
            key = self._keys[idx]
            if key not in self._exhausted:
                return key
            # Manually selected key is exhausted, fall through to rotation
        idx = self._current_index % len(available)
        return available[idx]

    def get_key_by_index(self, index: int) -> str | None:
        """Get key by 1-based index (for /keys commands)."""
        if 1 <= index <= len(self._keys):
            return self._keys[index - 1]
        return None

    def select_key(self, index: int) -> bool:
        """Manually select a key by 1-based index."""
        if 1 <= index <= len(self._keys):
            self._manual_index = index - 1
            return True
        return False

    def get_selected_index(self) -> int | None:
        """Get currently selected 1-based index, or None if auto-rotating."""
        if self._manual_index is not None:
            return self._manual_index + 1
        return None

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
        self._manual_index = None

    def has_keys(self) -> bool:
        self._reload_keys()
        return len(self._keys) > 0

    def get_keys_info(self) -> list[dict]:
        """Return info about all keys."""
        self._reload_keys()
        info = []
        for i, key in enumerate(self._keys, 1):
            masked = key[:8] + "..." + key[-4:] if len(key) > 12 else key[:4] + "..."
            info.append({
                "index": i,
                "masked": masked,
                "exhausted": key in self._exhausted,
                "selected": (self._manual_index == i - 1),
            })
        return info


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

    def _build_url(self, endpoint: str, api_key: str | None = None) -> str:
        base = self.config["base_url"]
        if self.provider_id == "cloudflare":
            account_id = (
                get_cloudflare_account_id_for_key(api_key)
                if api_key
                else get_cloudflare_account_id()
            )
            if not account_id:
                raise RuntimeError(
                    "CLOUDFLARE_ACCOUNT_ID not found for this key.\n"
                    "Add: CLOUDFLARE_ACCOUNT_ID_1=... paired with CLOUDFLARE_API_1=...\n"
                    "Or use the shared: CLOUDFLARE_ACCOUNT_ID=..."
                )
            base = base.format(account_id=account_id)
        return f"{base}{endpoint}"
    def _is_rate_limit(self, status_code: int, body: str) -> bool:
        if status_code == 429:
            return True
        if status_code in (401, 403):
            return True  # Invalid key, rotate
        return False

    def check_key(self, key_index: int) -> dict:
        """Check if a specific key is working. Returns status dict."""
        key = self.rotator.get_key_by_index(key_index)
        if key is None:
            return {"ok": False, "error": f"Key {key_index} not found for {self.config['name']}"}

        ptype = self.config["type"]
        try:
            if ptype == "openai_compat":
                return self._check_openai_key(key)
            elif ptype == "gemini":
                return self._check_gemini_key(key)
            elif ptype == "anthropic":
                return self._check_anthropic_key(key)
            elif ptype == "cohere":
                return self._check_cohere_key(key)
            else:
                return {"ok": False, "error": f"Unknown provider type: {ptype}"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def _check_openai_key(self, key: str) -> dict:
        url = self._build_url("/models", api_key=key)
        headers = {"Authorization": f"Bearer {key}"}
        if self.provider_id == "openrouter":
            headers["HTTP-Referer"] = "https://yohan-code"
            headers["X-Title"] = "YOHAN CODE"

        with httpx.Client(timeout=15) as client:
            resp = client.get(url, headers=headers)
            if resp.status_code == 200:
                return {"ok": True, "status": "active"}
            elif resp.status_code in (401, 403):
                return {"ok": False, "error": "Invalid API key (401/403)"}
            elif resp.status_code == 429:
                return {"ok": False, "error": "Rate limited (429)"}
            else:
                return {"ok": False, "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}

    def _check_gemini_key(self, key: str) -> dict:
        model = self.config["default_model"]
        url = f"{self.config['base_url']}/models/{model}?key={key}"
        with httpx.Client(timeout=15) as client:
            resp = client.get(url)
            if resp.status_code == 200:
                return {"ok": True, "status": "active"}
            elif resp.status_code in (401, 403):
                return {"ok": False, "error": "Invalid API key (401/403)"}
            elif resp.status_code == 429:
                return {"ok": False, "error": "Rate limited (429)"}
            else:
                return {"ok": False, "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}

    def _check_anthropic_key(self, key: str) -> dict:
        url = self._build_url("/models", api_key=key)
        headers = {
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
        }
        with httpx.Client(timeout=15) as client:
            resp = client.get(url, headers=headers)
            if resp.status_code == 200:
                return {"ok": True, "status": "active"}
            elif resp.status_code in (401, 403):
                return {"ok": False, "error": "Invalid API key (401/403)"}
            elif resp.status_code == 429:
                return {"ok": False, "error": "Rate limited (429)"}
            else:
                return {"ok": False, "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}

    def _check_cohere_key(self, key: str) -> dict:
        url = self._build_url("/models", api_key=key)
        headers = {"Authorization": f"Bearer {key}"}
        with httpx.Client(timeout=15) as client:
            resp = client.get(url, headers=headers)
            if resp.status_code == 200:
                return {"ok": True, "status": "active"}
            elif resp.status_code in (401, 403):
                return {"ok": False, "error": "Invalid API key (401/403)"}
            elif resp.status_code == 429:
                return {"ok": False, "error": "Rate limited (429)"}
            else:
                return {"ok": False, "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}

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

    # ── OpenAI-compatible (Groq, OpenRouter, Cloudflare, OpenAI, Mistral, ExperientialLabs) ────

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
        url = self._build_url("/chat/completions", api_key=key)
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


    @staticmethod
    def _to_text(content) -> str:
        if content is None:
            return ""
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for block in content:
                if isinstance(block, dict):
                    parts.append(block.get("text") or block.get("content") or "")
                else:
                    parts.append(str(block))
            return "\n".join(p for p in parts if p)
        return str(content)

    def _gemini_contents(self, messages: list[dict]) -> list[dict]:
        """Gemini is strict: first part must be user and roles must alternate."""
        contents: list[dict] = []
        for msg in messages:
            role = "user" if msg.get("role") == "user" else "model"
            text_value = self._to_text(msg.get("content")).strip()
            if not text_value:
                continue
            if contents and contents[-1]["role"] == role:
                contents[-1]["parts"][0]["text"] += "\n\n" + text_value
            else:
                contents.append({"role": role, "parts": [{"text": text_value}]})

        if not contents:
            contents.append({"role": "user", "parts": [{"text": "(empty)"}]})
        if contents[0]["role"] != "user":
            contents.insert(0, {"role": "user", "parts": [{"text": "(context)"}]})
        return contents

    def _gemini_chat(self, key, messages, model, stream, max_tokens, system) -> Iterator[str]:
        endpoint = "stream" if stream else "generate"
        action = "streamGenerateContent" if stream else "generateContent"
        url = f"{self.config['base_url']}/models/{model}:{action}?key={key}"

        contents = self._gemini_contents(messages)

        payload = {
            "contents": contents,
            "generationConfig": {
                "maxOutputTokens": max(max_tokens, 16384),
                "temperature": 0.7,
            },
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
                        parsed, buffer = self._parse_gemini_stream_incremental(buffer)
                        for item in parsed:
                            text = (item.get("candidates", [{}])[0]
                                    .get("content", {})
                                    .get("parts", [{}])[0]
                                    .get("text", ""))
                            if text:
                                yield text
                    # Flush any remaining buffer at end of stream
                    if buffer.strip():
                        parsed, _ = self._parse_gemini_stream_incremental(buffer + "]")
                        for item in parsed:
                            text = (item.get("candidates", [{}])[0]
                                    .get("content", {})
                                    .get("parts", [{}])[0]
                                    .get("text", ""))
                            if text:
                                yield text
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
        results, _ = self._parse_gemini_stream_incremental(buffer)
        return results

    def _parse_gemini_stream_incremental(self, buffer: str) -> tuple[list, str]:
        """Parse Gemini's chunked JSON array stream incrementally.

        Returns (parsed_objects, remaining_unparsed_buffer).
        The remaining buffer is kept so incomplete JSON chunks are not lost
        — they will be completed when more data arrives.
        """
        results = []
        decoder = json.JSONDecoder()
        remaining = buffer.lstrip(" \n\r,[")
        while remaining:
            try:
                obj, end = decoder.raw_decode(remaining)
                if isinstance(obj, dict):
                    results.append(obj)
                # Skip separators between JSON objects in the array
                remaining = remaining[end:].lstrip(" \n\r,")
                # Stop if we hit the closing bracket of the outer array
                if remaining.startswith("]"):
                    remaining = remaining[1:].lstrip(" \n\r")
            except json.JSONDecodeError:
                # Incomplete JSON — keep the remainder for the next chunk
                break
        return results, remaining

    # ── Anthropic ────────────────────────────────────────────────────────────

    def _anthropic_chat(self, key, messages, model, stream, max_tokens, system) -> Iterator[str]:
        url = self._build_url("/messages", api_key=key)
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
        url = self._build_url("/chat", api_key=key)
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


def reset_provider_cache():
    """Clear the provider cache (useful after key selection changes)."""
    global _provider_cache
    _provider_cache = {}


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
