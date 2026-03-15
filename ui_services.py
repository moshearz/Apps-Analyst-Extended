from __future__ import annotations

import csv
import re
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from analysis.llm_analyzer import parseOllamaRes, sendToOllama
from analysis.web_researcher import search_web_info
from collectors.win_apps_scanner import WinAppsScanner
from ui_models import AppRecord, ExportOptions, RiskAssessment
from utils.llm_setup import check_and_pull_model

CAPABILITY_LABELS = [
    "Remote Administration",
    "Remote File Sharing",
    "Keylogging",
    "Server Hosting",
]

RISK_DESCRIPTIONS = {
    "Remote Administration": (
        "May allow a stranger to remotely control the computer, access files, "
        "or execute actions without the user's understanding."
    ),
    "Remote File Sharing": (
        "May allow sending, receiving, uploading, or downloading files from "
        "outside the device."
    ),
    "Keylogging": (
        "May capture keyboard input and expose passwords, payment details, "
        "or private messages."
    ),
    "Server Hosting": (
        "May expose services or files over the network and create an access "
        "point on the device."
    ),
}


class ScanService:
    @staticmethod
    def scan(progress_callback=None, include_registry=True, include_filesystem=True) -> list[AppRecord]:
        registry_apps, exe_apps = WinAppsScanner().scan(
            progress_callback=progress_callback,
            include_registry=include_registry,
            include_filesystem=include_filesystem,
        )
        discovered_at = datetime.now()
        unified: list[AppRecord] = []

        for raw in registry_apps:
            unified.append(
                AppRecord(
                    record_id=ScanService._record_id(raw, "registry"),
                    name=raw.get("name", "Unknown"),
                    version=raw.get("version", "Unknown"),
                    publisher=raw.get("publisher", "Unknown"),
                    install_location=raw.get("install_location", "Unknown"),
                    source_kind="Registry",
                    discovered_at=discovered_at,
                    install_date=raw.get("install_date", "Unknown"),
                    source_registry=raw.get("source_registry", "Unknown"),
                    raw=raw,
                )
            )

        for raw in exe_apps:
            unified.append(
                AppRecord(
                    record_id=ScanService._record_id(raw, "filesystem"),
                    name=raw.get("name", "Unknown"),
                    version=raw.get("version", "Unknown"),
                    publisher=raw.get("publisher", "Unknown"),
                    install_location=raw.get("install_location", "Unknown"),
                    source_kind="Filesystem",
                    discovered_at=discovered_at,
                    install_date=raw.get("install_date", "Unknown"),
                    source_registry=raw.get("source_registry", "Unknown"),
                    raw=raw,
                )
            )

        unified.sort(key=lambda app: (app.name.lower(), app.source_kind, app.install_location.lower()))
        return unified

    @staticmethod
    def _record_id(raw: dict, source_kind: str) -> str:
        name = raw.get("name", "unknown").strip().lower()
        location = raw.get("install_location", "unknown").strip().lower()
        version = raw.get("version", "unknown").strip().lower()
        return f"{source_kind}:{name}:{version}:{location}"


class AnalysisService:
    @staticmethod
    def ensure_model(progress_callback=None):
        return check_and_pull_model(progress_callback=progress_callback)

    @staticmethod
    def analyze(app: AppRecord) -> RiskAssessment:
        web_info = search_web_info(app.name)
        llm_result = sendToOllama(web_info)
        if not llm_result:
            raise RuntimeError(f"LLM analysis failed for {app.name}.")
        risk_flags = parseOllamaRes(llm_result)
        return AnalysisService._build_assessment(app, llm_result, risk_flags)

    @staticmethod
    def _build_assessment(app: AppRecord, llm_text: str, risk_flags: list[bool]) -> RiskAssessment:
        overview = AnalysisService._extract_single_line(llm_text, "App Overview") or (
            f"{app.name} was analyzed from web search results."
        )

        evidence = {
            label: AnalysisService._extract_evidence(llm_text, label)
            for label in CAPABILITY_LABELS
        }
        indicators = AnalysisService._extract_bullets(llm_text, "Detected Indicators")
        why_this_matters = AnalysisService._extract_block(llm_text, "Why This Matters") or (
            "Unexpected remote-control or file-transfer tools can be used in scams or social-engineering attacks."
        )
        user_warning = AnalysisService._extract_block(llm_text, "User Warning") or (
            "If you did not expect this software, do not keep using it until you verify the source."
        )
        recommended_action = AnalysisService._extract_block(llm_text, "Recommended Action") or (
            "Verify the software source and remove it if it was not intentionally installed."
        )
        risk_level = AnalysisService._extract_single_line(llm_text, "Risk Level").lower()
        if risk_level not in {"low", "medium", "high"}:
            risk_level = AnalysisService._derive_risk_level(risk_flags)

        if not indicators:
            indicators = [
                label
                for label, flagged in zip(CAPABILITY_LABELS, risk_flags)
                if flagged
            ]

        return RiskAssessment(
            app_id=app.record_id,
            app_name=app.name,
            overview=overview,
            risk_flags=list(risk_flags),
            risk_level=risk_level,
            evidence=evidence,
            detected_indicators=indicators,
            why_this_matters=why_this_matters,
            user_warning=user_warning,
            recommended_action=recommended_action,
            raw_llm_text=llm_text,
        )

    @staticmethod
    def _derive_risk_level(risk_flags: list[bool]) -> str:
        if risk_flags[0] or risk_flags[2]:
            return "high"
        if any(risk_flags):
            return "medium"
        return "low"

    @staticmethod
    def _extract_single_line(text: str, label: str) -> str:
        pattern = rf"^{re.escape(label)}:\s*(.+)$"
        match = re.search(pattern, text, flags=re.MULTILINE)
        return match.group(1).strip() if match else ""

    @staticmethod
    def _extract_evidence(text: str, label: str) -> str:
        pattern = rf"^- {re.escape(label)}:\s*(.+)$"
        match = re.search(pattern, text, flags=re.MULTILINE)
        if match:
            return match.group(1).strip()
        return RISK_DESCRIPTIONS[label]

    @staticmethod
    def _extract_bullets(text: str, section: str) -> list[str]:
        block = AnalysisService._extract_block(text, section)
        if not block:
            return []
        items = []
        for line in block.splitlines():
            stripped = line.strip()
            if stripped.startswith("- "):
                items.append(stripped[2:].strip())
        return items

    @staticmethod
    def _extract_block(text: str, label: str) -> str:
        pattern = rf"{re.escape(label)}:\s*(.*?)(?:\n[A-Z][A-Za-z ]+:\s|\Z)"
        match = re.search(pattern, text, flags=re.DOTALL)
        if not match:
            return ""
        block = match.group(1).strip()
        lines = [line.rstrip() for line in block.splitlines() if line.strip()]
        return "\n".join(lines).strip()


class ExportService:
    @staticmethod
    def export_csv(path: str, apps: list[AppRecord], results: dict[str, RiskAssessment], options: ExportOptions) -> None:
        with open(path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(
                [
                    "App Name",
                    "Risk Level",
                    "Remote Administration",
                    "Remote File Sharing",
                    "Keylogging",
                    "Server Hosting",
                    "Publisher",
                    "Location",
                    "Recommended Action",
                ]
            )

            for app in apps:
                assessment = results.get(app.record_id)
                if not assessment:
                    continue
                writer.writerow(
                    [
                        assessment.app_name,
                        assessment.risk_level.title(),
                        ExportService._yes_no(assessment.risk_flags[0]),
                        ExportService._yes_no(assessment.risk_flags[1]),
                        ExportService._yes_no(assessment.risk_flags[2]),
                        ExportService._yes_no(assessment.risk_flags[3]),
                        app.publisher,
                        app.install_location,
                        assessment.recommended_action,
                    ]
                )

            if options.include_system_log:
                writer.writerow([])
                writer.writerow(["Export Metadata", "", "", "", "", "", "", "", ""])
                writer.writerow(["Generated At", datetime.now().isoformat(), "", "", "", "", "", "", ""])
                writer.writerow(["Export Options", str(asdict(options)), "", "", "", "", "", "", ""])

    @staticmethod
    def export_pdf(path: str, apps: list[AppRecord], results: dict[str, RiskAssessment], options: ExportOptions) -> None:
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
            from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
        except Exception as exc:
            raise RuntimeError(
                "reportlab is required to export PDF. Install with: pip install reportlab"
            ) from exc

        doc = SimpleDocTemplate(path, pagesize=letter)
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "AppsAnalystTitle",
            parent=styles["Heading1"],
            textColor=colors.HexColor("#0f172a"),
            spaceAfter=18,
        )
        section_style = ParagraphStyle(
            "AppsAnalystSection",
            parent=styles["Heading2"],
            textColor=colors.HexColor("#1152d4"),
            spaceAfter=8,
        )
        body_style = ParagraphStyle(
            "AppsAnalystBody",
            parent=styles["BodyText"],
            leading=14,
            spaceAfter=6,
        )

        elements = [Paragraph("Apps-Analyst Security Report", title_style)]
        elements.append(Paragraph(f"Time Range: {options.time_range}", body_style))
        elements.append(Spacer(1, 10))

        export_rows = [["App", "Level", "Remote", "File", "Keylog", "Server"]]
        for app in apps:
            assessment = results.get(app.record_id)
            if not assessment:
                continue
            export_rows.append(
                [
                    assessment.app_name,
                    assessment.risk_level.title(),
                    ExportService._yes_no(assessment.risk_flags[0]),
                    ExportService._yes_no(assessment.risk_flags[1]),
                    ExportService._yes_no(assessment.risk_flags[2]),
                    ExportService._yes_no(assessment.risk_flags[3]),
                ]
            )

        if len(export_rows) == 1:
            elements.append(Paragraph("No analyzed results are available for export.", body_style))
        else:
            table = Table(export_rows, repeatRows=1)
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1152d4")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.HexColor("#f8fafc")]),
                        ("PADDING", (0, 0), (-1, -1), 6),
                    ]
                )
            )
            elements.append(table)

        if options.include_detailed_risks:
            elements.append(Spacer(1, 16))
            elements.append(Paragraph("Detailed Findings", section_style))
            for app in apps:
                assessment = results.get(app.record_id)
                if not assessment:
                    continue
                elements.append(
                    Paragraph(
                        f"<b>{assessment.app_name}</b> ({assessment.risk_level.title()})",
                        body_style,
                    )
                )
                elements.append(Paragraph(assessment.overview, body_style))
                elements.append(Paragraph(f"Warning: {assessment.user_warning}", body_style))
                elements.append(Paragraph(f"Action: {assessment.recommended_action}", body_style))
                elements.append(Spacer(1, 8))

        if options.include_system_log:
            elements.append(Spacer(1, 16))
            elements.append(Paragraph("Export Metadata", section_style))
            elements.append(Paragraph(f"Generated At: {datetime.now().isoformat()}", body_style))
            elements.append(Paragraph(f"Export Path: {Path(path).name}", body_style))

        doc.build(elements)

    @staticmethod
    def _yes_no(value: bool) -> str:
        return "Yes" if value else "No"
