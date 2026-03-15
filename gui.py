from __future__ import annotations

import sys
from datetime import datetime

from PySide6.QtCore import QObject, Qt, QThread, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QButtonGroup,
    QCheckBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QStackedWidget,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ui_models import AppRecord, ExportOptions, RiskAssessment
from ui_services import AnalysisService, CAPABILITY_LABELS, ExportService, ScanService

APP_STYLESHEET = """
QWidget { background: #0b1220; color: #e2e8f0; font-family: "Segoe UI"; font-size: 10.5pt; }
QFrame#Sidebar { background: #0f172a; border-right: 1px solid #1e293b; }
QFrame#Card { background: #111c31; border: 1px solid #243045; border-radius: 18px; }
QFrame#HeroCard { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #10254a, stop:1 #1152d4); border: 1px solid #2563eb; border-radius: 20px; }
QLabel#Title { font-size: 22pt; font-weight: 700; color: #f8fafc; }
QLabel#SectionTitle { font-size: 15pt; font-weight: 700; color: #f8fafc; }
QLabel#Muted { color: #94a3b8; }
QLabel#MetricValue { font-size: 24pt; font-weight: 700; color: #f8fafc; }
QPushButton { background: #17263e; border: 1px solid #31405c; border-radius: 14px; padding: 10px 16px; color: #e2e8f0; font-weight: 600; }
QPushButton:hover { border-color: #4f79d8; background: #1b2d49; }
QPushButton:disabled { color: #64748b; border-color: #233148; background: #10192b; }
QPushButton#PrimaryButton { background: #1152d4; border-color: #2563eb; color: white; }
QPushButton#PrimaryButton:hover { background: #0e47b5; }
QPushButton#NavButton { text-align: left; padding: 12px 16px; border: none; background: transparent; color: #94a3b8; }
QPushButton#NavButton:checked { background: rgba(17, 82, 212, 0.18); color: #dbeafe; border: 1px solid rgba(37, 99, 235, 0.35); }
QLineEdit, QTextEdit { background: #0f172a; border: 1px solid #334155; border-radius: 12px; padding: 10px 12px; }
QLineEdit:focus, QTextEdit:focus { border-color: #2563eb; }
QTableWidget { background: #0f172a; border: 1px solid #243045; border-radius: 14px; gridline-color: #1e293b; selection-background-color: rgba(17, 82, 212, 0.35); selection-color: #f8fafc; }
QHeaderView::section { background: #111c31; color: #94a3b8; border: none; border-bottom: 1px solid #243045; padding: 12px 10px; font-weight: 700; }
QProgressBar { border: 1px solid #243045; border-radius: 999px; background: #0f172a; text-align: center; min-height: 14px; }
QProgressBar::chunk { background: #1152d4; border-radius: 999px; }
QStatusBar { background: #0f172a; color: #94a3b8; }
"""


def chip_style(background: str, foreground: str) -> str:
    return f"border-radius: 999px; padding: 6px 12px; font-weight: 700; background: {background}; color: {foreground};"


def risk_colors(level: str) -> tuple[str, str]:
    if level == "high":
        return "#450a0a", "#fecaca"
    if level == "medium":
        return "#3f2d07", "#fde68a"
    return "#052e16", "#bbf7d0"


def set_cell(table: QTableWidget, row: int, col: int, text: str, color: QColor | None = None) -> None:
    item = QTableWidgetItem(text)
    item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
    if color is not None:
        item.setForeground(color)
    table.setItem(row, col, item)


class ScanWorker(QObject):
    finished = Signal(list)
    progress = Signal(str)
    error = Signal(str)

    def __init__(self, include_registry: bool, include_filesystem: bool) -> None:
        super().__init__()
        self.include_registry = include_registry
        self.include_filesystem = include_filesystem

    def run(self) -> None:
        try:
            self.progress.emit("Preparing system scan...")
            self.finished.emit(
                ScanService.scan(
                    progress_callback=self.progress.emit,
                    include_registry=self.include_registry,
                    include_filesystem=self.include_filesystem,
                )
            )
        except Exception as exc:
            self.error.emit(str(exc))


class AnalysisWorker(QObject):
    model_status = Signal(str)
    progress = Signal(int, int, str)
    result_ready = Signal(object)
    finished = Signal()
    error = Signal(str)

    def __init__(self, apps: list[AppRecord]) -> None:
        super().__init__()
        self.apps = apps

    def run(self) -> None:
        try:
            self.model_status.emit("Checking Ollama model availability...")
            ready = AnalysisService.ensure_model(progress_callback=self._emit_model_status)
            if ready is not True:
                if ready == "ERROR_OLLAMA_OFFLINE":
                    raise RuntimeError("Ollama is not running. Start Ollama and try again.")
                raise RuntimeError(str(ready))
            total = len(self.apps)
            for index, app in enumerate(self.apps, start=1):
                self.progress.emit(index, total, f"Analyzing {app.name}")
                self.result_ready.emit(AnalysisService.analyze(app))
            self.finished.emit()
        except Exception as exc:
            self.error.emit(str(exc))

    def _emit_model_status(self, message: str, update_last: bool = False) -> None:
        self.model_status.emit(message)


class StatCard(QFrame):
    def __init__(self, title: str, accent: str) -> None:
        super().__init__()
        self.setObjectName("Card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(8)
        title_label = QLabel(title)
        title_label.setObjectName("Muted")
        layout.addWidget(title_label)
        self.value_label = QLabel("--")
        self.value_label.setObjectName("MetricValue")
        layout.addWidget(self.value_label)
        self.sub_label = QLabel("No data yet")
        self.sub_label.setObjectName("Muted")
        self.sub_label.setWordWrap(True)
        layout.addWidget(self.sub_label)
        accent_bar = QFrame()
        accent_bar.setFixedHeight(4)
        accent_bar.setStyleSheet(f"background: {accent}; border-radius: 999px;")
        layout.addWidget(accent_bar)

    def set_content(self, value: str, subtitle: str) -> None:
        self.value_label.setText(value)
        self.sub_label.setText(subtitle)


class DashboardPage(QWidget):
    detection_requested = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.row_ids: list[str] = []
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(18)

        hero = QFrame()
        hero.setObjectName("HeroCard")
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(28, 24, 28, 24)
        hero_layout.setSpacing(10)
        title = QLabel("Security Command Center")
        title.setObjectName("Title")
        hero_layout.addWidget(title)
        subtitle = QLabel("Monitor installed software, review suspicious findings, and export clear reports.")
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: #dbeafe; font-size: 11.5pt;")
        hero_layout.addWidget(subtitle)
        root.addWidget(hero)

        grid = QGridLayout()
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(18)
        self.total_card = StatCard("Total Apps", "#60a5fa")
        self.high_card = StatCard("High Risk", "#f87171")
        self.medium_card = StatCard("Medium Risk", "#fbbf24")
        self.last_card = StatCard("Last Scan", "#34d399")
        grid.addWidget(self.total_card, 0, 0)
        grid.addWidget(self.high_card, 0, 1)
        grid.addWidget(self.medium_card, 0, 2)
        grid.addWidget(self.last_card, 0, 3)
        root.addLayout(grid)

        scan_card = QFrame()
        scan_card.setObjectName("Card")
        scan_layout = QVBoxLayout(scan_card)
        scan_layout.setContentsMargins(22, 20, 22, 20)
        scan_layout.setSpacing(14)
        row = QHBoxLayout()
        title = QLabel("Active System Scan")
        title.setObjectName("SectionTitle")
        row.addWidget(title)
        row.addStretch(1)
        self.scan_state = QLabel("Idle")
        self.scan_state.setObjectName("Muted")
        row.addWidget(self.scan_state)
        scan_layout.addLayout(row)
        self.scan_progress = QProgressBar()
        self.scan_progress.setRange(0, 100)
        self.scan_progress.setValue(0)
        scan_layout.addWidget(self.scan_progress)
        self.scan_detail = QLabel("Start a scan to populate the dashboard.")
        self.scan_detail.setObjectName("Muted")
        self.scan_detail.setWordWrap(True)
        scan_layout.addWidget(self.scan_detail)
        root.addWidget(scan_card)

        detections_card = QFrame()
        detections_card.setObjectName("Card")
        detections_layout = QVBoxLayout(detections_card)
        detections_layout.setContentsMargins(22, 20, 22, 20)
        detections_layout.setSpacing(12)
        detections_title = QLabel("Recent Detections")
        detections_title.setObjectName("SectionTitle")
        detections_layout.addWidget(detections_title)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["App", "Location", "Detection", "Risk"])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.cellDoubleClicked.connect(self._open_detection)
        detections_layout.addWidget(self.table)
        root.addWidget(detections_card, 1)

    def set_metrics(self, total: int, high: int, medium: int, last_scan: str) -> None:
        self.total_card.set_content(str(total), "Discovered across registry and filesystem")
        self.high_card.set_content(str(high), "Immediate review recommended")
        self.medium_card.set_content(str(medium), "Monitor and verify source")
        self.last_card.set_content(last_scan, "Most recent successful system scan")

    def set_scan_state(self, active: bool, state: str, detail: str) -> None:
        self.scan_state.setText(state)
        self.scan_detail.setText(detail)
        if active:
            self.scan_progress.setRange(0, 0)
        else:
            self.scan_progress.setRange(0, 100)
            self.scan_progress.setValue(100 if state == "Complete" else 0)

    def set_detections(self, apps: list[AppRecord], results: dict[str, RiskAssessment]) -> None:
        items = []
        for app in apps:
            assessment = results.get(app.record_id)
            if not assessment:
                continue
            detection = next((label for label, flagged in zip(CAPABILITY_LABELS, assessment.risk_flags) if flagged), "Review Needed")
            if assessment.risk_level == "low" and detection == "Review Needed":
                continue
            items.append((app, assessment, detection))
        priority = {"high": 0, "medium": 1, "low": 2}
        items.sort(key=lambda item: (priority.get(item[1].risk_level, 3), item[0].name.lower()))
        items = items[:10]
        self.table.setRowCount(len(items) or 1)
        self.row_ids = []
        if not items:
            self.row_ids.append("")
            set_cell(self.table, 0, 0, "No detections yet")
            set_cell(self.table, 0, 1, "Run a scan and analyze one or more apps")
            set_cell(self.table, 0, 2, "--")
            set_cell(self.table, 0, 3, "--")
            return
        for row, (app, assessment, detection) in enumerate(items):
            self.row_ids.append(app.record_id)
            set_cell(self.table, row, 0, app.name)
            set_cell(self.table, row, 1, app.install_location)
            set_cell(self.table, row, 2, detection)
            color = QColor("#fca5a5" if assessment.risk_level == "high" else "#fde68a")
            set_cell(self.table, row, 3, assessment.risk_level.title(), color)

    def _open_detection(self, row: int, _column: int) -> None:
        if 0 <= row < len(self.row_ids) and self.row_ids[row]:
            self.detection_requested.emit(self.row_ids[row])


class AnalysisPage(QWidget):
    analyze_requested = Signal(list)
    focus_requested = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.apps: list[AppRecord] = []
        self.results: dict[str, RiskAssessment] = {}
        self.filtered_ids: list[str] = []
        self.record_lookup: dict[str, AppRecord] = {}
        self.checked_record_ids: set[str] = set()
        self._focused_record_id: str | None = None

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(18)

        left = QFrame()
        left.setObjectName("Card")
        left.setMinimumWidth(470)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(22, 20, 22, 20)
        left_layout.setSpacing(14)
        row = QHBoxLayout()
        title = QLabel("Application Inventory")
        title.setObjectName("SectionTitle")
        row.addWidget(title)
        row.addStretch(1)
        self.clear_selection_button = QPushButton("Clear selection")
        row.addWidget(self.clear_selection_button)
        self.analyze_selected_button = QPushButton("Analyze selected")
        self.analyze_selected_button.setObjectName("PrimaryButton")
        row.addWidget(self.analyze_selected_button)
        left_layout.addLayout(row)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search apps, paths, or publishers...")
        left_layout.addWidget(self.search)
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["", "App", "Source", "Version", "Status"])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setColumnWidth(0, 36)
        left_layout.addWidget(self.table, 1)
        self.selection_hint = QLabel("Mark suspicious apps with the checkboxes, then click Analyze selected.")
        self.selection_hint.setObjectName("Muted")
        left_layout.addWidget(self.selection_hint)
        root.addWidget(left, 5)

        right = QFrame()
        right.setObjectName("Card")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(22, 20, 22, 20)
        right_layout.setSpacing(14)
        header = QHBoxLayout()
        header_title = QLabel("Risk Detail")
        header_title.setObjectName("SectionTitle")
        header.addWidget(header_title)
        header.addStretch(1)
        self.badge = QLabel("Not analyzed")
        self.badge.setStyleSheet(chip_style("#1e293b", "#cbd5e1"))
        header.addWidget(self.badge)
        right_layout.addLayout(header)
        self.detail_title = QLabel("Select an application")
        self.detail_title.setObjectName("Title")
        right_layout.addWidget(self.detail_title)
        self.detail_meta = QLabel("App metadata and AI findings will appear here.")
        self.detail_meta.setObjectName("Muted")
        self.detail_meta.setWordWrap(True)
        right_layout.addWidget(self.detail_meta)

        self.capability_labels: list[QLabel] = []
        capability_grid = QGridLayout()
        capability_grid.setHorizontalSpacing(10)
        capability_grid.setVerticalSpacing(10)
        for index, name in enumerate(CAPABILITY_LABELS):
            label = QLabel(f"{name}: Unknown")
            label.setWordWrap(True)
            label.setStyleSheet("background: #0f172a; border-radius: 12px; padding: 12px; border: 1px solid #243045;")
            self.capability_labels.append(label)
            capability_grid.addWidget(label, index // 2, index % 2)
        right_layout.addLayout(capability_grid)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(12)

        self.overview = self._detail_box("Overview", container_layout, 90)
        self.evidence = self._detail_box("Capability Evidence", container_layout, 120)
        self.impact = self._detail_box("Why This Matters", container_layout, 90)
        self.guidance = self._detail_box("User Guidance", container_layout, 90)
        container_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        scroll.setWidget(container)
        right_layout.addWidget(scroll, 1)

        action_row = QHBoxLayout()
        self.analyze_current_button = QPushButton("Analyze focused app")
        self.analyze_current_button.setObjectName("PrimaryButton")
        action_row.addWidget(self.analyze_current_button)
        right_layout.addLayout(action_row)
        root.addWidget(right, 6)

        self.search.textChanged.connect(lambda _text: self._apply_filter())
        self.table.itemSelectionChanged.connect(self._emit_focus)
        self.table.itemChanged.connect(self._handle_item_changed)
        self.clear_selection_button.clicked.connect(self._clear_selection)
        self.analyze_selected_button.clicked.connect(self._emit_analyze_selected)
        self.analyze_current_button.clicked.connect(self._emit_analyze_current)
        self._update_selection_state()

    def _detail_box(self, title: str, parent_layout: QVBoxLayout, min_height: int) -> QTextEdit:
        label = QLabel(title)
        label.setStyleSheet("font-size: 12pt; font-weight: 700; color: #f8fafc;")
        parent_layout.addWidget(label)
        box = QTextEdit()
        box.setReadOnly(True)
        box.setMinimumHeight(min_height)
        parent_layout.addWidget(box)
        return box

    def set_apps(self, apps: list[AppRecord], results: dict[str, RiskAssessment]) -> None:
        previous_checked = list(self.checked_record_ids)
        previous_focus = self._focused_record_id
        self.apps = apps
        self.results = results
        self.record_lookup = {app.record_id: app for app in apps}
        self.checked_record_ids = {record_id for record_id in previous_checked if record_id in self.record_lookup}
        self._apply_filter(previous_focus)

    def set_search_text(self, text: str) -> None:
        if self.search.text() != text:
            self.search.setText(text)

    def selected_ids(self) -> list[str]:
        return [app.record_id for app in self.apps if app.record_id in self.checked_record_ids]

    def select_record(self, record_id: str) -> None:
        if not record_id:
            return
        if record_id not in self.filtered_ids:
            self.search.clear()
            self._apply_filter()
        if record_id not in self.filtered_ids:
            return
        row = self.filtered_ids.index(record_id)
        self.table.setCurrentCell(row, 1)
        self.table.selectRow(row)
        self._focused_record_id = record_id
        self.show_detail(record_id)
        self.focus_requested.emit(record_id)

    def show_empty_detail(self) -> None:
        self.badge.setText("Not analyzed")
        self.badge.setStyleSheet(chip_style("#1e293b", "#cbd5e1"))
        self.detail_title.setText("Select an application")
        self.detail_meta.setText("App metadata and AI findings will appear here.")
        self.overview.setText("No AI analysis has been run for this application yet.")
        self.evidence.setText("Click a row to inspect it, or mark suspicious apps with the checkboxes for batch analysis.")
        self.impact.setText("Potential impact details will appear after analysis.")
        self.guidance.setText("Use Analyze selected to analyze only the apps you explicitly checked.")
        for widget, name in zip(self.capability_labels, CAPABILITY_LABELS):
            widget.setText(f"{name}: Unknown")
            widget.setStyleSheet("background: #0f172a; border-radius: 12px; padding: 12px; border: 1px solid #243045;")

    def show_detail(self, record_id: str) -> None:
        app = self.record_lookup.get(record_id)
        if not app:
            self.show_empty_detail()
            return
        assessment = self.results.get(record_id)
        self.detail_title.setText(app.name)
        self.detail_meta.setText(
            f"{app.source_kind} source | Version: {app.version} | Publisher: {app.publisher}\n"
            f"Location: {app.install_location}"
        )
        if assessment:
            bg, fg = risk_colors(assessment.risk_level)
            self.badge.setText(f"{assessment.risk_level.title()} risk")
            self.badge.setStyleSheet(chip_style(bg, fg))
            self.overview.setText(assessment.overview)
            self.evidence.setText("\n".join(f"{name}: {assessment.evidence.get(name, 'No evidence captured.')}" for name in CAPABILITY_LABELS))
            self.impact.setText(assessment.why_this_matters)
            self.guidance.setText(f"Warning: {assessment.user_warning}\n\nRecommended action: {assessment.recommended_action}")
            for widget, name, enabled in zip(self.capability_labels, CAPABILITY_LABELS, assessment.risk_flags):
                state = "Detected" if enabled else "Not detected"
                widget.setText(f"{name}: {state}")
                widget.setStyleSheet(
                    (
                        "background: #450a0a; border-radius: 12px; padding: 12px; border: 1px solid #7f1d1d;"
                        if enabled
                        else "background: #052e16; border-radius: 12px; padding: 12px; border: 1px solid #14532d;"
                    )
                )
        else:
            self.badge.setText("Not analyzed")
            self.badge.setStyleSheet(chip_style("#1e293b", "#cbd5e1"))
            self.overview.setText("No AI analysis has been run for this application yet.")
            self.evidence.setText("Use Analyze focused app for this row, or Analyze selected for the checked apps.")
            self.impact.setText("Potential impact details will appear after analysis.")
            self.guidance.setText("Use the analysis actions to generate a risk assessment.")
            for widget, name in zip(self.capability_labels, CAPABILITY_LABELS):
                widget.setText(f"{name}: Unknown")
                widget.setStyleSheet("background: #0f172a; border-radius: 12px; padding: 12px; border: 1px solid #243045;")

    def _apply_filter(self, focus_record_id: str | None = None) -> None:
        query = self.search.text().strip().lower()
        visible = [
            app for app in self.apps
            if not query
            or query in app.name.lower()
            or query in app.install_location.lower()
            or query in app.publisher.lower()
            or query in app.source_kind.lower()
        ]
        self.filtered_ids = [app.record_id for app in visible]
        self.table.blockSignals(True)
        self.table.setRowCount(len(visible))
        for row, app in enumerate(visible):
            checkbox_item = QTableWidgetItem()
            checkbox_item.setFlags(
                Qt.ItemFlag.ItemIsEnabled
                | Qt.ItemFlag.ItemIsUserCheckable
                | Qt.ItemFlag.ItemIsSelectable
            )
            checkbox_item.setCheckState(
                Qt.CheckState.Checked if app.record_id in self.checked_record_ids else Qt.CheckState.Unchecked
            )
            self.table.setItem(row, 0, checkbox_item)
            assessment = self.results.get(app.record_id)
            set_cell(self.table, row, 1, app.name)
            set_cell(self.table, row, 2, app.source_kind)
            set_cell(self.table, row, 3, app.version)
            status = "Not analyzed" if not assessment else assessment.risk_level.title()
            color = None if not assessment else QColor("#fca5a5" if assessment.risk_level == "high" else "#fde68a" if assessment.risk_level == "medium" else "#86efac")
            set_cell(self.table, row, 4, status, color)
        self.table.blockSignals(False)
        if not visible:
            self._focused_record_id = None
            self._update_selection_state()
            self.show_empty_detail()
            return
        if focus_record_id and focus_record_id in self.filtered_ids:
            row = self.filtered_ids.index(focus_record_id)
            self.table.setCurrentCell(row, 1)
            self.table.selectRow(row)
            self._focused_record_id = focus_record_id
            self.show_detail(focus_record_id)
        elif self._focused_record_id and self._focused_record_id in self.filtered_ids:
            row = self.filtered_ids.index(self._focused_record_id)
            self.table.setCurrentCell(row, 1)
            self.table.selectRow(row)
            self.show_detail(self._focused_record_id)
        else:
            self.table.clearSelection()
            self._focused_record_id = None
            self.show_empty_detail()
        self._update_selection_state()

    def _emit_focus(self) -> None:
        current_row = self.table.currentRow()
        if current_row < 0 or current_row >= len(self.filtered_ids):
            self._focused_record_id = None
            self._update_selection_state()
            self.show_empty_detail()
            return
        self._focused_record_id = self.filtered_ids[current_row]
        self._update_selection_state()
        self.show_detail(self._focused_record_id)
        self.focus_requested.emit(self._focused_record_id)

    def _emit_analyze_selected(self) -> None:
        selected = self.selected_ids()
        if selected:
            self.analyze_requested.emit(selected)

    def _emit_analyze_current(self) -> None:
        if self._focused_record_id:
            self.analyze_requested.emit([self._focused_record_id])

    def _clear_selection(self) -> None:
        self.checked_record_ids.clear()
        self.table.blockSignals(True)
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item is not None:
                item.setCheckState(Qt.CheckState.Unchecked)
        self.table.blockSignals(False)
        self._update_selection_state()

    def _handle_item_changed(self, item: QTableWidgetItem) -> None:
        if item.column() != 0:
            return
        if not (0 <= item.row() < len(self.filtered_ids)):
            return
        record_id = self.filtered_ids[item.row()]
        if item.checkState() == Qt.CheckState.Checked:
            self.checked_record_ids.add(record_id)
        else:
            self.checked_record_ids.discard(record_id)
        self._update_selection_state()

    def _update_selection_state(self) -> None:
        visible_count = len(self.filtered_ids)
        selected_count = len(self.selected_ids())
        has_selection = selected_count > 0
        self.clear_selection_button.setEnabled(has_selection)
        self.analyze_selected_button.setEnabled(has_selection)
        self.analyze_current_button.setEnabled(self._focused_record_id is not None)
        self.analyze_selected_button.setText(
            f"Analyze selected ({selected_count})" if selected_count > 1 else "Analyze selected"
        )
        if not visible_count:
            self.selection_hint.setText(
                "No applications match the current search"
                if not selected_count
                else f"No applications match the current search | {selected_count} checked for analysis"
            )
            return
        if selected_count:
            self.selection_hint.setText(
                f"{visible_count} applications shown | {selected_count} checked for analysis"
            )
            return
        self.selection_hint.setText(
            f"{visible_count} applications shown | Mark suspicious apps with the checkboxes, then click Analyze selected"
        )


class ReportPage(QWidget):
    export_pdf_requested = Signal(object)
    export_csv_requested = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self.range_buttons: dict[str, QPushButton] = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(18)

        card = QFrame()
        card.setObjectName("Card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(18)
        title = QLabel("Generate Security Report")
        title.setObjectName("Title")
        layout.addWidget(title)
        subtitle = QLabel("Choose the level of detail to include in the report and export the analyzed findings.")
        subtitle.setObjectName("Muted")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        range_title = QLabel("Select time range")
        range_title.setObjectName("SectionTitle")
        layout.addWidget(range_title)
        row = QHBoxLayout()
        self.range_group = QButtonGroup(self)
        self.range_group.setExclusive(True)
        for name in ["Last 24h", "Last 7 days", "All results"]:
            button = QPushButton(name)
            button.setCheckable(True)
            if name == "All results":
                button.setChecked(True)
            self.range_buttons[name] = button
            self.range_group.addButton(button)
            row.addWidget(button)
        row.addStretch(1)
        layout.addLayout(row)

        sections = QLabel("Report sections")
        sections.setObjectName("SectionTitle")
        layout.addWidget(sections)
        self.summary_check = QCheckBox("Executive summary")
        self.summary_check.setChecked(True)
        self.detailed_check = QCheckBox("Detailed risks")
        self.detailed_check.setChecked(True)
        self.system_log_check = QCheckBox("Export metadata")
        for checkbox in (self.summary_check, self.detailed_check, self.system_log_check):
            layout.addWidget(checkbox)

        preview = QFrame()
        preview.setObjectName("Card")
        preview_layout = QVBoxLayout(preview)
        preview_layout.setContentsMargins(18, 16, 18, 16)
        preview_layout.setSpacing(10)
        preview_title = QLabel("Preview")
        preview_title.setObjectName("SectionTitle")
        preview_layout.addWidget(preview_title)
        self.preview_label = QLabel("No analyzed results available yet.")
        self.preview_label.setObjectName("Muted")
        self.preview_label.setWordWrap(True)
        preview_layout.addWidget(self.preview_label)
        layout.addWidget(preview)

        action_row = QHBoxLayout()
        self.pdf_button = QPushButton("Export PDF")
        self.pdf_button.setObjectName("PrimaryButton")
        self.csv_button = QPushButton("Export CSV")
        action_row.addWidget(self.pdf_button)
        action_row.addWidget(self.csv_button)
        action_row.addStretch(1)
        layout.addLayout(action_row)
        root.addWidget(card)
        root.addStretch(1)

        self.pdf_button.clicked.connect(lambda: self.export_pdf_requested.emit(self.options("pdf")))
        self.csv_button.clicked.connect(lambda: self.export_csv_requested.emit(self.options("csv")))
        self.set_summary(0, 0, 0, 0)

    def options(self, export_format: str) -> ExportOptions:
        selected_range = next((name for name, button in self.range_buttons.items() if button.isChecked()), "All results")
        return ExportOptions(
            time_range=selected_range,
            include_summary=self.summary_check.isChecked(),
            include_detailed_risks=self.detailed_check.isChecked(),
            include_system_log=self.system_log_check.isChecked(),
            format=export_format,
        )

    def set_summary(self, total: int, analyzed: int, high: int, medium: int) -> None:
        self.preview_label.setText(
            f"{analyzed} analyzed results out of {total} discovered apps.\n"
            f"High risk: {high} | Medium risk: {medium} | Remaining analyzed apps: {max(analyzed - high - medium, 0)}"
        )
        enabled = analyzed > 0
        self.pdf_button.setEnabled(enabled)
        self.csv_button.setEnabled(enabled)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.apps: list[AppRecord] = []
        self.app_lookup: dict[str, AppRecord] = {}
        self.assessments: dict[str, RiskAssessment] = {}
        self.last_scan_at: datetime | None = None
        self.scan_thread: QThread | None = None
        self.scan_worker: ScanWorker | None = None
        self.analysis_thread: QThread | None = None
        self.analysis_worker: AnalysisWorker | None = None

        self.setWindowTitle("Apps-Analyst")
        self.resize(1480, 920)
        self.setMinimumSize(1180, 760)
        self._build_ui()
        self._refresh_state()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        shell = QHBoxLayout(central)
        shell.setContentsMargins(0, 0, 0, 0)
        shell.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(240)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(18, 20, 18, 20)
        sidebar_layout.setSpacing(12)
        brand = QLabel("Apps-Analyst")
        brand.setStyleSheet("font-size: 18pt; font-weight: 700; color: #f8fafc;")
        sidebar_layout.addWidget(brand)
        subtitle = QLabel("Security Suite")
        subtitle.setObjectName("Muted")
        sidebar_layout.addWidget(subtitle)
        sidebar_layout.addSpacing(10)
        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        self.nav_buttons: dict[str, QPushButton] = {}
        for key, label in [("dashboard", "Dashboard"), ("analysis", "Apps"), ("reports", "Reports")]:
            button = QPushButton(label)
            button.setObjectName("NavButton")
            button.setCheckable(True)
            button.clicked.connect(lambda checked=False, name=key: self.switch_page(name))
            self.nav_group.addButton(button)
            self.nav_buttons[key] = button
            sidebar_layout.addWidget(button)
        sidebar_layout.addStretch(1)
        account = QFrame()
        account.setObjectName("Card")
        account_layout = QVBoxLayout(account)
        account_layout.setContentsMargins(14, 14, 14, 14)
        account_layout.setSpacing(6)
        account_layout.addWidget(QLabel("Admin User"))
        plan = QLabel("Enterprise plan")
        plan.setObjectName("Muted")
        account_layout.addWidget(plan)
        sidebar_layout.addWidget(account)
        shell.addWidget(sidebar)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(26, 18, 26, 18)
        content_layout.setSpacing(18)
        shell.addWidget(content, 1)

        topbar = QFrame()
        topbar.setObjectName("Card")
        topbar_layout = QHBoxLayout(topbar)
        topbar_layout.setContentsMargins(20, 16, 20, 16)
        topbar_layout.setSpacing(12)
        self.system_badge = QLabel("System status: Ready")
        self.system_badge.setStyleSheet(chip_style("#052e16", "#bbf7d0"))
        topbar_layout.addWidget(self.system_badge)
        self.global_search = QLineEdit()
        self.global_search.setPlaceholderText("Search files, paths, publishers, or apps...")
        topbar_layout.addWidget(self.global_search, 1)
        self.registry_scan_check = QCheckBox("Registry")
        self.registry_scan_check.setChecked(True)
        topbar_layout.addWidget(self.registry_scan_check)
        self.exe_scan_check = QCheckBox("EXE files")
        self.exe_scan_check.setChecked(True)
        topbar_layout.addWidget(self.exe_scan_check)
        self.scan_button = QPushButton("Scan system")
        self.scan_button.setObjectName("PrimaryButton")
        topbar_layout.addWidget(self.scan_button)
        self.report_button = QPushButton("Open reports")
        topbar_layout.addWidget(self.report_button)
        content_layout.addWidget(topbar)

        self.stack = QStackedWidget()
        self.dashboard_page = DashboardPage()
        self.analysis_page = AnalysisPage()
        self.report_page = ReportPage()
        self.stack.addWidget(self.dashboard_page)
        self.stack.addWidget(self.analysis_page)
        self.stack.addWidget(self.report_page)
        content_layout.addWidget(self.stack, 1)

        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Ready")

        self.nav_buttons["dashboard"].setChecked(True)
        self.scan_button.clicked.connect(self.start_scan)
        self.report_button.clicked.connect(lambda: self.switch_page("reports"))
        self.global_search.textChanged.connect(lambda text: self.analysis_page.set_search_text(text))
        self.dashboard_page.detection_requested.connect(self.open_detection)
        self.analysis_page.analyze_requested.connect(self.start_analysis)
        self.analysis_page.focus_requested.connect(self._focus_changed)
        self.report_page.export_pdf_requested.connect(self.export_results)
        self.report_page.export_csv_requested.connect(self.export_results)

    def switch_page(self, page: str) -> None:
        index_map = {"dashboard": 0, "analysis": 1, "reports": 2}
        self.stack.setCurrentIndex(index_map[page])
        self.nav_buttons[page].setChecked(True)

    def start_scan(self) -> None:
        if self.scan_thread is not None:
            return
        include_registry = self.registry_scan_check.isChecked()
        include_filesystem = self.exe_scan_check.isChecked()
        if not include_registry and not include_filesystem:
            QMessageBox.warning(self, "No scan source", "Select Registry, EXE files, or both before starting a scan.")
            return

        selected_sources = []
        if include_registry:
            selected_sources.append("registry")
        if include_filesystem:
            selected_sources.append("EXE files")
        selection_label = " and ".join(selected_sources)

        self.dashboard_page.set_scan_state(True, "Running", f"Scanning {selection_label}...")
        self.scan_button.setEnabled(False)
        self.registry_scan_check.setEnabled(False)
        self.exe_scan_check.setEnabled(False)
        self.system_badge.setText("System status: Scanning")
        self.system_badge.setStyleSheet(chip_style("#172554", "#bfdbfe"))
        self.statusBar().showMessage(f"System scan started: {selection_label}")

        self.scan_thread = QThread(self)
        self.scan_worker = ScanWorker(include_registry, include_filesystem)
        self.scan_worker.moveToThread(self.scan_thread)
        self.scan_thread.started.connect(self.scan_worker.run)
        self.scan_worker.progress.connect(self._scan_progress)
        self.scan_worker.finished.connect(self._scan_complete)
        self.scan_worker.error.connect(self._worker_error)
        self.scan_worker.finished.connect(self.scan_thread.quit)
        self.scan_worker.error.connect(self.scan_thread.quit)
        self.scan_thread.finished.connect(self.scan_worker.deleteLater)
        self.scan_thread.finished.connect(self._cleanup_scan_thread)
        self.scan_thread.start()

    def start_analysis(self, record_ids: list[str]) -> None:
        if self.analysis_thread is not None:
            return
        apps = [self.app_lookup[record_id] for record_id in record_ids if record_id in self.app_lookup]
        if not apps:
            QMessageBox.warning(self, "No selection", "Select at least one application to analyze.")
            return
        self.analysis_page.analyze_selected_button.setEnabled(False)
        self.analysis_page.analyze_current_button.setEnabled(False)
        self.system_badge.setText("System status: Analysis running")
        self.system_badge.setStyleSheet(chip_style("#3f2d07", "#fde68a"))
        self.statusBar().showMessage(f"Analyzing {len(apps)} application(s)...")

        self.analysis_thread = QThread(self)
        self.analysis_worker = AnalysisWorker(apps)
        self.analysis_worker.moveToThread(self.analysis_thread)
        self.analysis_thread.started.connect(self.analysis_worker.run)
        self.analysis_worker.model_status.connect(self.statusBar().showMessage)
        self.analysis_worker.progress.connect(self._analysis_progress)
        self.analysis_worker.result_ready.connect(self._analysis_result)
        self.analysis_worker.finished.connect(self._analysis_complete)
        self.analysis_worker.error.connect(self._worker_error)
        self.analysis_worker.finished.connect(self.analysis_thread.quit)
        self.analysis_worker.error.connect(self.analysis_thread.quit)
        self.analysis_thread.finished.connect(self.analysis_worker.deleteLater)
        self.analysis_thread.finished.connect(self._cleanup_analysis_thread)
        self.analysis_thread.start()

    def export_results(self, options: ExportOptions) -> None:
        apps = [app for app in self.apps if app.record_id in self.assessments]
        if not apps:
            QMessageBox.warning(self, "No data", "Analyze at least one app before exporting.")
            return
        if options.format == "pdf":
            default_pdf_name = f"Apps-Analyst_Report_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.pdf"
            path, _ = QFileDialog.getSaveFileName(self, "Export PDF", default_pdf_name, "PDF files (*.pdf)")
            if not path:
                return
            exporter = ExportService.export_pdf
        else:
            path, _ = QFileDialog.getSaveFileName(self, "Export CSV", "apps_analyst_report.csv", "CSV files (*.csv)")
            if not path:
                return
            exporter = ExportService.export_csv
        try:
            exporter(path, apps, self.assessments, options)
        except Exception as exc:
            QMessageBox.critical(self, "Export failed", str(exc))
            self.statusBar().showMessage(f"Export failed: {exc}")
            return
        QMessageBox.information(self, "Export complete", f"Report saved to:\n{path}")
        self.statusBar().showMessage(f"Exported report to {path}")

    def open_detection(self, record_id: str) -> None:
        self.switch_page("analysis")
        self.analysis_page.select_record(record_id)

    def _scan_progress(self, message: str) -> None:
        self.dashboard_page.set_scan_state(True, "Running", message)
        self.statusBar().showMessage(message)

    def _scan_complete(self, apps: list[AppRecord]) -> None:
        self.apps = apps
        self.app_lookup = {app.record_id: app for app in apps}
        self.last_scan_at = datetime.now()
        self.dashboard_page.set_scan_state(False, "Complete", f"Discovered {len(apps)} apps across the system.")
        self.statusBar().showMessage(f"Scan complete: {len(apps)} apps discovered")
        self._refresh_state()

    def _analysis_progress(self, index: int, total: int, message: str) -> None:
        self.statusBar().showMessage(f"{message} ({index}/{total})")

    def _analysis_result(self, assessment: RiskAssessment) -> None:
        self.assessments[assessment.app_id] = assessment
        self._refresh_state()

    def _analysis_complete(self) -> None:
        self.statusBar().showMessage("Analysis complete")
        self._refresh_state()

    def _focus_changed(self, record_id: str) -> None:
        if record_id in self.app_lookup:
            self.statusBar().showMessage(f"Focused app: {self.app_lookup[record_id].name}")

    def _worker_error(self, message: str) -> None:
        QMessageBox.critical(self, "Operation failed", message)
        self.dashboard_page.set_scan_state(False, "Failed", message)
        self.analysis_page.analyze_selected_button.setEnabled(True)
        self.analysis_page.analyze_current_button.setEnabled(True)
        self.statusBar().showMessage(message)
        self._refresh_state()

    def _cleanup_scan_thread(self) -> None:
        self.scan_thread = None
        self.scan_worker = None
        self.scan_button.setEnabled(True)
        self.registry_scan_check.setEnabled(True)
        self.exe_scan_check.setEnabled(True)
        self._refresh_state()

    def _cleanup_analysis_thread(self) -> None:
        self.analysis_thread = None
        self.analysis_worker = None
        self.analysis_page.analyze_selected_button.setEnabled(True)
        self.analysis_page.analyze_current_button.setEnabled(True)
        self._refresh_state()

    def _refresh_state(self) -> None:
        high = sum(1 for assessment in self.assessments.values() if assessment.risk_level == "high")
        medium = sum(1 for assessment in self.assessments.values() if assessment.risk_level == "medium")
        last_scan = self.last_scan_at.strftime("%H:%M") if self.last_scan_at else "--"
        self.dashboard_page.set_metrics(len(self.apps), high, medium, last_scan)
        self.dashboard_page.set_detections(self.apps, self.assessments)
        self.analysis_page.set_apps(self.apps, self.assessments)
        self.report_page.set_summary(len(self.apps), len(self.assessments), high, medium)
        if self.scan_thread is not None:
            self.system_badge.setText("System status: Scanning")
            self.system_badge.setStyleSheet(chip_style("#172554", "#bfdbfe"))
        elif self.analysis_thread is not None:
            self.system_badge.setText("System status: Analysis running")
            self.system_badge.setStyleSheet(chip_style("#3f2d07", "#fde68a"))
        elif high > 0:
            self.system_badge.setText(f"System status: {high} high-risk app(s)")
            self.system_badge.setStyleSheet(chip_style("#450a0a", "#fecaca"))
        else:
            self.system_badge.setText("System status: Secure posture")
            self.system_badge.setStyleSheet(chip_style("#052e16", "#bbf7d0"))


def run_gui() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Apps-Analyst")
    app.setStyleSheet(APP_STYLESHEET)
    app.setFont(QFont("Segoe UI", 10))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run_gui()
