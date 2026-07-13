"""LLM backend abstraction: swap between the Anthropic API, a local Ollama model, and Groq.

``generation.py`` and ``judge.py`` are written against the ``LLMBackend``
protocol so the same generation/judging code runs unmodified against any
backend. Pick a backend via ``build_backend()``, typically from the CLI's
``--backend`` flag. Groq exists alongside the Anthropic API specifically as
a free-tier option for public deployments where per-request API cost isn't
acceptable — see ``backend/README.md``.
"""

from __future__ import annotations

import json
import os
import ssl
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Protocol

import certifi

# Explicit CA bundle for HTTPS calls (GroqBackend). Some Python installs
# (notably python.org's macOS installer, before "Install Certificates.command"
# has been run) ship without a populated default cert store, which makes
# urllib fail SSL verification even though the server's cert is fine.
# certifi's bundle is reliable across platforms, so use it explicitly rather
# than depending on whatever the local system happens to have configured.
_SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())

DEFAULT_OLLAMA_HOST = "http://localhost:11434"
DEFAULT_OLLAMA_MODEL = "qwen2.5:3b"
DEFAULT_ANTHROPIC_MODEL = "claude-sonnet-5"
DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"
DEFAULT_GROQ_HOST = "https://api.groq.com/openai/v1"


@dataclass(frozen=True)
class CompletionResult:
    text: str
    model: str
    input_tokens: int
    output_tokens: int


class LLMBackend(Protocol):
    model: str

    def complete(self, system: str, user: str, max_tokens: int) -> CompletionResult:
        """Free-form text completion."""
        ...

    def complete_json(self, system: str, user: str, schema: dict[str, Any], max_tokens: int) -> dict[str, Any]:
        """Completion constrained to the given JSON schema; returns the parsed object."""
        ...


class AnthropicBackend:
    """Backend calling the Anthropic API (Claude)."""

    def __init__(self, model: str = DEFAULT_ANTHROPIC_MODEL, client: Any = None) -> None:
        import anthropic

        self.model = model
        self.client = client or anthropic.Anthropic()

    def complete(self, system: str, user: str, max_tokens: int) -> CompletionResult:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        text = next((b.text for b in response.content if b.type == "text"), "")
        return CompletionResult(
            text=text,
            model=response.model,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )

    def complete_json(self, system: str, user: str, schema: dict[str, Any], max_tokens: int) -> dict[str, Any]:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
            output_config={"format": {"type": "json_schema", "schema": schema}},
        )
        text = next(b.text for b in response.content if b.type == "text")
        return json.loads(text)


class OllamaBackend:
    """Backend calling a local Ollama server's /api/chat endpoint.

    Uses Ollama's structured-output support (the ``format`` field accepting a
    JSON schema) for ``complete_json``, and plain chat for ``complete``. Uses
    only the standard library (``urllib``) so no extra HTTP client dependency
    is required.
    """

    def __init__(
        self,
        model: str = DEFAULT_OLLAMA_MODEL,
        host: str = DEFAULT_OLLAMA_HOST,
        timeout: float = 180.0,
    ) -> None:
        self.model = model
        self.host = host.rstrip("/")
        self.timeout = timeout

    def _chat(self, system: str, user: str, max_tokens: int, format: Any = None) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "options": {"num_predict": max_tokens},
        }
        if format is not None:
            payload["format"] = format

        request = urllib.request.Request(
            f"{self.host}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise RuntimeError(
                f"Could not reach Ollama at {self.host}. Is `ollama serve` running "
                f"and is the '{self.model}' model pulled (`ollama pull {self.model}`)?"
            ) from exc

    def complete(self, system: str, user: str, max_tokens: int) -> CompletionResult:
        data = self._chat(system, user, max_tokens)
        text = data["message"]["content"]
        return CompletionResult(
            text=text,
            model=self.model,
            input_tokens=data.get("prompt_eval_count", 0),
            output_tokens=data.get("eval_count", 0),
        )

    def complete_json(self, system: str, user: str, schema: dict[str, Any], max_tokens: int) -> dict[str, Any]:
        # Small local models occasionally emit truncated/empty JSON under load; one retry
        # is cheap insurance and avoids failing an entire eval run on a single flaky call.
        last_error: Exception | None = None
        for _ in range(2):
            data = self._chat(system, user, max_tokens, format=schema)
            text = data["message"]["content"]
            try:
                return json.loads(text)
            except json.JSONDecodeError as exc:
                last_error = exc
        raise RuntimeError(f"Ollama returned invalid JSON after retry: {last_error}")


class GroqBackend:
    """Backend calling Groq's OpenAI-compatible chat completions API.

    Free-tier alternative to the Anthropic API for public deployments where
    per-request cost isn't acceptable. Uses ``response_format: json_object``
    (universally supported across Groq's model lineup) rather than the
    newer ``json_schema`` structured-output mode, and instead embeds the
    schema directly in the prompt — this trades a small amount of extra
    prompt tokens for not depending on per-model structured-output support
    varying across Groq's free-tier model lineup. Uses only the standard
    library, matching ``OllamaBackend``.
    """

    def __init__(
        self,
        model: str = DEFAULT_GROQ_MODEL,
        api_key: str | None = None,
        host: str = DEFAULT_GROQ_HOST,
        timeout: float = 60.0,
    ) -> None:
        self.model = model
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        if not self.api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Get a free key at https://console.groq.com/keys"
            )
        self.host = host.rstrip("/")
        self.timeout = timeout

    def _chat(self, messages: list[dict[str, str]], max_tokens: int, json_mode: bool = False) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "max_completion_tokens": max_tokens,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        request = urllib.request.Request(
            f"{self.host}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                # Groq's API sits behind Cloudflare, which blocks the default
                # "Python-urllib/x.y" User-Agent as bot traffic (HTTP 403,
                # Cloudflare error 1010). Any ordinary-looking UA clears it.
                "User-Agent": "rag-eval/1.0",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout, context=_SSL_CONTEXT) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Groq API error {exc.code}: {body}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Could not reach Groq API at {self.host}: {exc}") from exc

    def complete(self, system: str, user: str, max_tokens: int) -> CompletionResult:
        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        data = self._chat(messages, max_tokens)
        choice = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        return CompletionResult(
            text=choice,
            model=data.get("model", self.model),
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
        )

    def complete_json(self, system: str, user: str, schema: dict[str, Any], max_tokens: int) -> dict[str, Any]:
        schema_system = (
            f"{system}\n\nRespond with a single JSON object only, no other text, "
            f"matching exactly this JSON schema:\n{json.dumps(schema)}"
        )
        messages = [{"role": "system", "content": schema_system}, {"role": "user", "content": user}]

        last_error: Exception | None = None
        for _ in range(2):
            data = self._chat(messages, max_tokens, json_mode=True)
            text = data["choices"][0]["message"]["content"]
            try:
                return json.loads(text)
            except json.JSONDecodeError as exc:
                last_error = exc
        raise RuntimeError(f"Groq returned invalid JSON after retry: {last_error}")


def build_backend(backend: str, model: str) -> LLMBackend:
    if backend == "local":
        return OllamaBackend(model=model)
    if backend == "api":
        return AnthropicBackend(model=model)
    if backend == "groq":
        return GroqBackend(model=model)
    raise ValueError(f"Unknown backend '{backend}'. Expected 'local', 'api', or 'groq'.")
