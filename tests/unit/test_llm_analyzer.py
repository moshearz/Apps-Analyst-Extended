from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from analysis.llm_analyzer import parseOllamaRes


def test_parse_ollama_response_parses_all_capabilities() -> None:
    response = """Remote Administration: yes
Remote File Sharing: no
Keylogging: yes
Server Hosting: no
"""
    assert parseOllamaRes(response) == [True, False, True, False]


def test_parse_ollama_response_is_case_insensitive() -> None:
    response = """Remote Administration: YES
Remote File Sharing: No
Keylogging: yEs
Server Hosting: nO
"""
    assert parseOllamaRes(response) == [True, False, True, False]


def test_parse_ollama_response_ignores_text_inside_hash_markers() -> None:
    response = """Remote Administration: yes
## Remote File Sharing: yes ##
Remote File Sharing: no
Keylogging: no
Server Hosting: no
"""
    assert parseOllamaRes(response) == [True, False, False, False]


def test_parse_ollama_response_defaults_missing_lines_to_false() -> None:
    response = "Remote Administration: yes"
    assert parseOllamaRes(response) == [True, False, False, False]
