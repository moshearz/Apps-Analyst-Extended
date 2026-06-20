# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Apps-Analyst is a Windows security awareness tool that scans installed applications (via Windows Registry and filesystem), researches them on the web (DuckDuckGo), sends findings to a local LLM (Ollama with gemma3:1b), and produces a 4-category risk assessment: Remote Administration, Remote File Sharing, Keylogging, Server Hosting. It has both a CLI and a PySide6 GUI.

## Common Commands

```bash
# Activate virtual environment
.venv\Scripts\Activate.ps1          # PowerShell
source .venv/Scripts/activate       # Git Bash

# Install all dependencies
pip install -r requirements.txt -r requirements-dev.txt

# Run the app
python main.py          # CLI mode
python main.py --gui    # GUI mode

# Run unit tests (safe for CI, no external deps)
python -m pytest tests/unit/ -v

# Run a single test file or test function
python -m pytest tests/unit/test_ui_services.py -v
python -m pytest tests/unit/test_ui_services.py::test_build_assessment_parses_structured_llm_response -v

# Run only CI-safe tests (excludes integration/e2e needing Ollama, internet, GUI, registry)
python -m pytest tests/ -m "not (integration or ollama or web or windows_only or e2e or gui or cli or full_flow)" -v

# Run integration tests (requires Ollama running + internet)
python -m pytest tests/ -m integration -v

# Run with coverage
python -m pytest tests/unit/ --cov=. --cov-report=term-missing
```

## Architecture

### Data Flow

```
WinAppsScanner.scan() → ScanService → AppRecord[]
                                          ↓
                              search_web_info(app.name) → web text
                                          ↓
                              sendToOllama(web_text) → structured LLM response
                                          ↓
                              parseOllamaRes(response) → [bool, bool, bool, bool]
                                          ↓
                              AnalysisService._build_assessment() → RiskAssessment
```

### Key Design Patterns

**GUI uses worker threads for blocking operations.** `ScanWorker` and `AnalysisWorker` (in `gui.py`) run on `QThread` and communicate results back via Qt signals. The `MainWindow` owns the thread lifecycle and cleans up via `_cleanup_*_thread` methods.

**Service layer decouples GUI from business logic.** `ui_services.py` contains `ScanService`, `AnalysisService`, and `ExportService` — these are used by both the GUI workers and can be called directly in tests or CLI code. The GUI never calls `sendToOllama` or `WinAppsScanner` directly.

**`AnalysisService._build_assessment()` parses free-form LLM text into structured data.** It uses regex extraction (`_extract_single_line`, `_extract_block`, `_extract_bullets`, `_extract_evidence`) with fallback defaults when the LLM doesn't follow the expected format. This is the most fragile code path — changes to the LLM prompt in `llm_analyzer.py` must stay aligned with these parsers.

**`main.py` auto-installs missing packages at startup** via `install_missing_requirements()`. This function has a duplicated body (two sequential implementations) — this is a known quirk, not a pattern to follow.

### Windows-Only Constraint

`collectors/win_apps_scanner.py` imports `winreg` at module level. `ui_services.py` imports `WinAppsScanner` at module level. This means **any file that imports from `ui_services` cannot be loaded on Linux**. The integration tests handle this with `pytest.skip()` guards, but unit tests for `ui_services` run only on Windows (or `windows-latest` in CI).

### Test Markers (pytest.ini)

| Marker | Meaning |
|--------|---------|
| `integration` | Real component interactions |
| `ollama` | Requires running Ollama instance |
| `web` | Requires outbound internet |
| `windows_only` | Requires Windows registry/behavior |
| `e2e` | Full application entrypoint flows |
| `gui` / `cli` | GUI or CLI entrypoints |
| `full_flow` | End-to-end happy path across subsystems |

Unit tests have no markers and are always safe to run.

## LLM Prompt Contract

The system prompt in `llm_analyzer.py:sendToOllama()` instructs the model to return a specific text format. The response parser in `ui_services.py:AnalysisService._build_assessment()` expects these exact section headers:

- `App Overview:` — single line
- `Remote Administration:` / `Remote File Sharing:` / `Keylogging:` / `Server Hosting:` — yes/no lines
- `Capability Evidence:` — bullet list with `- <label>: <reason>`
- `Risk Level:` — low/medium/high
- `Detected Indicators:` — bullet list
- `Why This Matters:` / `User Warning:` / `Recommended Action:` — free text blocks

If modifying the prompt, keep these headers stable or update the parsers in `ui_services.py` accordingly.

## CI

GitHub Actions workflow at `.github/workflows/ci.yml` runs on `windows-latest` with Python 3.12 on push/PR to `main`. It runs only the marker-filtered safe tests (21 unit tests).
