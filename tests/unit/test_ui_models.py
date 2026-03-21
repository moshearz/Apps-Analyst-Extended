from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ui_models import AppRecord, ExportOptions, RiskAssessment


def test_app_record_stores_required_and_optional_fields() -> None:
    raw = {"name": "TeamViewer"}
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
        raw=raw,
    )

    assert app.name == "TeamViewer"
    assert app.source_kind == "Registry"
    assert app.raw == raw


def test_risk_assessment_stores_analysis_fields() -> None:
    assessment = RiskAssessment(
        app_id="app-1",
        app_name="TeamViewer",
        overview="Remote access tool used for support.",
        risk_flags=[True, True, False, False],
        risk_level="high",
        evidence={"Remote Administration": "Supports remote control."},
        detected_indicators=["Remote control", "File transfer"],
        why_this_matters="Unexpected remote access software can be abused in scams.",
        user_warning="Verify whether you installed this intentionally.",
        recommended_action="Review the software source before using it.",
        raw_llm_text="App Overview: Remote access tool",
    )

    assert assessment.app_name == "TeamViewer"
    assert assessment.risk_flags == [True, True, False, False]
    assert assessment.risk_level == "high"


def test_export_options_defaults_match_expected_values() -> None:
    options = ExportOptions()

    assert options.time_range == "All results"
    assert options.include_summary is True
    assert options.include_detailed_risks is True
    assert options.include_system_log is False
    assert options.format == "pdf"
