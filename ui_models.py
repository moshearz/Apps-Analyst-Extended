from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class AppRecord:
    record_id: str
    name: str
    version: str
    publisher: str
    install_location: str
    source_kind: str
    discovered_at: datetime
    install_date: str = "Unknown"
    source_registry: str = "Unknown"
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RiskAssessment:
    app_id: str
    app_name: str
    overview: str
    risk_flags: list[bool]
    risk_level: str
    evidence: dict[str, str]
    detected_indicators: list[str]
    why_this_matters: str
    user_warning: str
    recommended_action: str
    raw_llm_text: str


@dataclass(slots=True)
class ExportOptions:
    time_range: str = "All results"
    include_summary: bool = True
    include_detailed_risks: bool = True
    include_system_log: bool = False
    format: str = "pdf"
