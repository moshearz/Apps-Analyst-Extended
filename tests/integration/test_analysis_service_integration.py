from __future__ import annotations

from datetime import datetime
from pathlib import Path
import socket
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ui_models import AppRecord, RiskAssessment
from ui_services import AnalysisService


pytestmark = [pytest.mark.integration, pytest.mark.web, pytest.mark.ollama]


def _skip_if_no_internet() -> None:
    try:
        with socket.create_connection(("duckduckgo.com", 443), timeout=3):
            return
    except OSError as exc:
        pytest.skip(f"No outbound internet connectivity for web integration test: {exc}")


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


def test_analysis_service_analyze_returns_structured_risk_assessment() -> None:
    _skip_if_no_internet()
    _skip_if_ollama_not_running()
    _skip_if_model_missing()

    app = AppRecord(
        record_id="registry:teamviewer:15.0:c:\\program files\\teamviewer",
        name="TeamViewer",
        version="15.0",
        publisher="TeamViewer GmbH",
        install_location=r"C:\Program Files\TeamViewer",
        source_kind="Registry",
        discovered_at=datetime(2026, 1, 1, 12, 0, 0),
        install_date="20260101",
        source_registry=r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\TeamViewer",
        raw={"name": "TeamViewer"},
    )

    assessment = AnalysisService.analyze(app)

    assert isinstance(assessment, RiskAssessment)
    assert assessment.app_id == app.record_id
    assert assessment.app_name == app.name
    assert isinstance(assessment.overview, str)
    assert assessment.overview.strip()
    assert isinstance(assessment.risk_flags, list)
    assert len(assessment.risk_flags) == 4
    assert all(isinstance(value, bool) for value in assessment.risk_flags)
    assert assessment.risk_level in {"low", "medium", "high"}
    assert isinstance(assessment.recommended_action, str)
    assert assessment.recommended_action.strip()
    assert isinstance(assessment.raw_llm_text, str)
    assert assessment.raw_llm_text.strip()
