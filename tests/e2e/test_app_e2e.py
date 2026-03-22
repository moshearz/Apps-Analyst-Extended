from __future__ import annotations

from pathlib import Path
import re
import socket
import subprocess
import sys
import os
import time

import pytest

if not sys.platform.startswith("win"):
    pytest.skip("E2E tests are intended for Windows environments.", allow_module_level=True)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from collectors.win_apps_scanner import WinAppsScanner


MAIN_PY = PROJECT_ROOT / "main.py"


def _subprocess_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def _skip_if_no_internet() -> None:
    try:
        with socket.create_connection(("duckduckgo.com", 443), timeout=3):
            return
    except OSError as exc:
        pytest.skip(f"No outbound internet connectivity for E2E test: {exc}")


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
    model_names = []
    for model in raw_models:
        if isinstance(model, dict):
            model_names.append(model.get("name") or model.get("model") or "")
        else:
            model_names.append(getattr(model, "name", "") or getattr(model, "model", ""))
    if not any(model_name in name for name in model_names):
        pytest.skip(f"Required model '{model_name}' is not installed.")


def _terminate_process(proc: subprocess.Popen[str]) -> None:
    if proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=10)


def _assert_process_stays_alive(args: list[str], timeout_seconds: int = 5) -> tuple[str, str]:
    proc = subprocess.Popen(
        [sys.executable, "-u", str(MAIN_PY), *args],
        cwd=str(PROJECT_ROOT),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=_subprocess_env(),
    )
    try:
        time.sleep(timeout_seconds)
        if proc.poll() is not None:
            stdout, stderr = proc.communicate(timeout=10)
            raise AssertionError(
                f"Process exited too quickly with return code {proc.returncode}.\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}"
            )
        _terminate_process(proc)
        stdout, stderr = proc.communicate(timeout=10)
        return stdout, stderr
    finally:
        _terminate_process(proc)


def _choose_cli_selection() -> str:
    try:
        registry_apps, exe_apps = WinAppsScanner().scan()
    except Exception as exc:
        pytest.skip(f"Could not pre-scan local machine to prepare CLI selection: {exc}")

    if registry_apps:
        return "r\n1\n"
    if exe_apps:
        return "e\n1\n"
    pytest.skip("No applications were discovered on the local machine for CLI E2E selection.")


@pytest.mark.e2e
@pytest.mark.cli
@pytest.mark.windows_only
def test_cli_startup_smoke() -> None:
    stdout, stderr = _assert_process_stays_alive([])

    combined_output = f"{stdout}\n{stderr}"
    assert "Starting AppsAnalyst" in combined_output


@pytest.mark.e2e
@pytest.mark.gui
@pytest.mark.windows_only
def test_gui_startup_smoke() -> None:
    stdout, stderr = _assert_process_stays_alive(["--gui"])

    combined_output = f"{stdout}\n{stderr}"
    assert "Traceback" not in combined_output


@pytest.mark.e2e
@pytest.mark.cli
@pytest.mark.full_flow
@pytest.mark.windows_only
@pytest.mark.web
@pytest.mark.ollama
def test_cli_full_flow_reaches_structured_risk_vector() -> None:
    _skip_if_no_internet()
    _skip_if_ollama_not_running()
    _skip_if_model_missing()

    selection_input = _choose_cli_selection()

    result = subprocess.run(
        [sys.executable, "-u", str(MAIN_PY)],
        cwd=str(PROJECT_ROOT),
        input=selection_input,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=240,
        env=_subprocess_env(),
    )

    combined_output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode == 0, combined_output
    assert "Starting AppsAnalyst" in combined_output
    assert "Researching web for" in combined_output
    assert "Web info collected for" in combined_output
    assert "Risk Assessment Vector:" in combined_output
    assert "LLM analysis completed." in combined_output

    match = re.search(r"Risk Assessment Vector:\s*\[([^\]]+)\]", combined_output)
    assert match is not None, combined_output
    values = [value.strip() for value in match.group(1).split(",")]
    assert len(values) == 4
    assert all(value in {"True", "False"} for value in values)
