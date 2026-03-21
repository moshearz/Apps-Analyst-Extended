from __future__ import annotations

from pathlib import Path
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from analysis.llm_analyzer import parseOllamaRes, sendToOllama


pytestmark = [pytest.mark.integration, pytest.mark.ollama]


def _skip_if_ollama_not_running() -> None:
    ollama = pytest.importorskip("ollama")
    try:
        ollama.list()
    except Exception as exc:
        pytest.skip(f"Ollama is not running or unavailable: {exc}")


def _skip_if_model_missing(model_name: str = "gemma3:1b") -> None:
    ollama = pytest.importorskip("ollama")
    try:
        listing = ollama.list()
    except Exception as exc:
        pytest.skip(f"Could not query Ollama models: {exc}")
    raw_models = getattr(listing, "models", None)
    if raw_models is None and hasattr(listing, "get"):
        raw_models = listing.get("models", [])
    raw_models = raw_models or []
    models = []
    for model in raw_models:
        if isinstance(model, dict):
            models.append(model.get("name") or model.get("model") or "")
        else:
            models.append(getattr(model, "name", "") or getattr(model, "model", ""))
    if not any(model_name in name for name in models):
        pytest.skip(f"Required model '{model_name}' is not installed.")


def test_send_to_ollama_returns_structured_non_empty_response() -> None:
    _skip_if_ollama_not_running()
    _skip_if_model_missing()

    web_data = """- Title: TeamViewer overview
  Info: TeamViewer is a remote support and remote access application with remote control features and file transfer.
"""

    response = sendToOllama(web_data)

    assert isinstance(response, str)
    assert response.strip()
    assert "Remote Administration:" in response
    assert "Remote File Sharing:" in response
    assert "Keylogging:" in response
    assert "Server Hosting:" in response


def test_send_to_ollama_response_can_be_parsed_into_four_flags() -> None:
    _skip_if_ollama_not_running()
    _skip_if_model_missing()

    web_data = """- Title: Remote admin tool
  Info: This software provides remote desktop access, unattended support, and file transfer.
"""

    response = sendToOllama(web_data)
    flags = parseOllamaRes(response)

    assert isinstance(flags, list)
    assert len(flags) == 4
    assert all(isinstance(value, bool) for value in flags)
