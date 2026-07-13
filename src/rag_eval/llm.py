"""LLM backend abstraction: swap between the Anthropic API and a local Ollama model.

``generation.py`` and ``judge.py`` are written against the ``LLMBackend``
protocol so the same generation/judging code runs unmodified against either
backend. Pick a backend via ``build_backend()``, typically from the CLI's
``--backend`` flag.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Protocol

DEFAULT_OLLAMA_HOST = "http://localhost:11434"
DEFAULT_OLLAMA_MODEL = "qwen2.5:3b"
DEFAULT_ANTHROPIC_MODEL = "claude-sonnet-5"


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


def build_backend(backend: str, model: str) -> LLMBackend:
    if backend == "local":
        return OllamaBackend(model=model)
    if backend == "api":
        return AnthropicBackend(model=model)
    raise ValueError(f"Unknown backend '{backend}'. Expected 'local' or 'api'.")
