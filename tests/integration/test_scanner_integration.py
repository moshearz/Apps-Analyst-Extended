from __future__ import annotations

from pathlib import Path
import sys

import pytest

if not sys.platform.startswith("win"):
    pytest.skip("Windows-specific integration test.", allow_module_level=True)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from collectors.win_apps_scanner import WinAppsScanner


pytestmark = [pytest.mark.integration, pytest.mark.windows_only]


def test_filesystem_scan_finds_executables_in_real_temp_directory(tmp_path: Path) -> None:
    exe_path = tmp_path / "Downloads" / "tool.exe"
    exe_path.parent.mkdir(parents=True)
    exe_path.write_text("not a real executable", encoding="utf-8")

    scanner = WinAppsScanner()
    scanner.file_scan_paths = [str(tmp_path)]
    scanner.max_filesystem_depth = 5

    registry_apps, exe_apps = scanner.scan(include_registry=False, include_filesystem=True)

    assert registry_apps == []
    assert len(exe_apps) == 1
    assert exe_apps[0]["name"] == "tool"
    assert exe_apps[0]["install_location"] == str(exe_path)


def test_filesystem_scan_skips_ignored_directories(tmp_path: Path) -> None:
    ignored_exe = tmp_path / ".git" / "ignored.exe"
    allowed_exe = tmp_path / "Apps" / "allowed.exe"
    ignored_exe.parent.mkdir(parents=True)
    allowed_exe.parent.mkdir(parents=True)
    ignored_exe.write_text("ignored", encoding="utf-8")
    allowed_exe.write_text("allowed", encoding="utf-8")

    scanner = WinAppsScanner()
    scanner.file_scan_paths = [str(tmp_path)]
    scanner.max_filesystem_depth = 5

    _registry_apps, exe_apps = scanner.scan(include_registry=False, include_filesystem=True)
    discovered_paths = {app["install_location"] for app in exe_apps}

    assert str(allowed_exe) in discovered_paths
    assert str(ignored_exe) not in discovered_paths
