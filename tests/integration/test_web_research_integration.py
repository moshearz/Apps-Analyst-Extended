from __future__ import annotations

from pathlib import Path
import socket
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from analysis.web_researcher import search_web_info


pytestmark = [pytest.mark.integration, pytest.mark.web]


def _skip_if_no_internet() -> None:
    try:
        with socket.create_connection(("duckduckgo.com", 443), timeout=3):
            return
    except OSError as exc:
        pytest.skip(f"No outbound internet connectivity for web integration test: {exc}")


def test_search_web_info_returns_aggregated_results_for_known_app() -> None:
    _skip_if_no_internet()

    text = search_web_info("TeamViewer")

    assert isinstance(text, str)
    assert text.strip()
    assert "- Title:" in text
    assert "Info:" in text
