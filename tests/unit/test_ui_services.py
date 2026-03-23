from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ui_models import AppRecord
from ui_services import AnalysisService, RISK_DESCRIPTIONS, ScanService


def make_app_record() -> AppRecord:
    return AppRecord(
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


def test_extract_single_line_returns_value_when_label_exists() -> None:
    text = "App Overview: Remote support tool\nRisk Level: high"
    assert AnalysisService._extract_single_line(text, "App Overview") == "Remote support tool"


def test_extract_single_line_returns_empty_string_when_label_missing() -> None:
    assert AnalysisService._extract_single_line("No matching label here", "App Overview") == ""


def test_extract_block_returns_trimmed_text_until_next_section() -> None:
    text = """Why This Matters:
Unexpected remote access can be abused.
Users may be tricked into installing it.

User Warning:
Verify the source first.
"""
    assert AnalysisService._extract_block(text, "Why This Matters") == (
        "Unexpected remote access can be abused.\nUsers may be tricked into installing it."
    )


def test_extract_block_returns_empty_string_when_section_missing() -> None:
    assert AnalysisService._extract_block("Risk Level: low", "Why This Matters") == ""


def test_extract_bullets_returns_only_bullet_items() -> None:
    text = """Detected Indicators:
- Remote control
- File transfer
Ignored line

Why This Matters:
Review the software.
"""
    assert AnalysisService._extract_bullets(text, "Detected Indicators") == [
        "Remote control",
        "File transfer",
    ]


def test_extract_evidence_returns_specific_line_when_present() -> None:
    text = "- Remote Administration: Provides unattended remote access."
    assert (
        AnalysisService._extract_evidence(text, "Remote Administration")
        == "Provides unattended remote access."
    )


def test_extract_evidence_returns_default_description_when_missing() -> None:
    assert (
        AnalysisService._extract_evidence("No evidence lines here", "Keylogging")
        == RISK_DESCRIPTIONS["Keylogging"]
    )


def test_derive_risk_level_returns_high_for_remote_admin() -> None:
    assert AnalysisService._derive_risk_level([True, False, False, False]) == "high"


def test_derive_risk_level_returns_high_for_keylogging() -> None:
    assert AnalysisService._derive_risk_level([False, False, True, False]) == "high"


def test_derive_risk_level_returns_medium_when_non_high_capability_present() -> None:
    assert AnalysisService._derive_risk_level([False, True, False, False]) == "medium"


def test_derive_risk_level_returns_low_when_no_capabilities_present() -> None:
    assert AnalysisService._derive_risk_level([False, False, False, False]) == "low"


def test_build_assessment_parses_structured_llm_response() -> None:
    app = make_app_record()
    llm_text = """App Overview: Remote support application

Remote Administration: yes
Remote File Sharing: yes
Keylogging: no
Server Hosting: no

Capability Evidence:
- Remote Administration: Provides unattended remote access.
- Remote File Sharing: Includes file transfer features.
- Keylogging: Not mentioned in the provided text.
- Server Hosting: Not mentioned in the provided text.

Risk Level: high

Detected Indicators:
- Remote control
- File transfer

Why This Matters:
An unexpected remote support tool could let a stranger access the device.

User Warning:
If you do not recognize this app, do not use it until you verify the source.

Recommended Action:
Confirm the software was intentionally installed and remove it if necessary.
"""

    assessment = AnalysisService._build_assessment(app, llm_text, [True, True, False, False])

    assert assessment.app_id == app.record_id
    assert assessment.app_name == "TeamViewer"
    assert assessment.overview == "Remote support application"
    assert assessment.risk_flags == [True, True, False, False]
    assert assessment.risk_level == "high"
    assert assessment.evidence["Remote Administration"] == "Provides unattended remote access."
    assert assessment.detected_indicators == ["Remote control", "File transfer"]
    assert "unexpected remote support tool" in assessment.why_this_matters.lower()
    assert "verify the source" in assessment.user_warning.lower()
    assert "remove it" in assessment.recommended_action.lower()
    assert assessment.raw_llm_text == llm_text


def test_build_assessment_uses_fallbacks_when_sections_are_missing() -> None:
    app = make_app_record()
    llm_text = """Remote Administration: no
Remote File Sharing: yes
Keylogging: no
Server Hosting: no

Capability Evidence:
- Remote File Sharing: Can transfer files.

Risk Level: suspicious
"""

    assessment = AnalysisService._build_assessment(app, llm_text, [False, True, False, False])

    assert assessment.overview == "TeamViewer was analyzed from web search results."
    assert assessment.risk_level == "medium"
    assert assessment.detected_indicators == ["Remote File Sharing"]
    assert assessment.evidence["Remote File Sharing"] == "Can transfer files."
    assert assessment.evidence["Server Hosting"] == RISK_DESCRIPTIONS["Server Hosting"]
    assert "unexpected remote-control or file-transfer tools" in assessment.why_this_matters.lower()
    assert "verify the software source" in assessment.recommended_action.lower()


def test_record_id_normalizes_case_and_whitespace() -> None:
    raw = {
        "name": "  TeamViewer  ",
        "version": " 15.0 ",
        "install_location": r" C:\Program Files\TeamViewer ",
    }
    assert ScanService._record_id(raw, "registry") == "registry:teamviewer:15.0:c:\\program files\\teamviewer"
