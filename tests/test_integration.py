import pytest
import json
import subprocess
import sys
import os

SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scripts")

PYTHON = r"C:\Users\unicom\AppData\Local\Programs\Python\Python312\python.exe"


def test_engine_runs_end_to_end():
    """Verify engine produces valid JSON output with expected sections."""
    result = subprocess.run(
        [PYTHON, "engine.py",
         "--topic", "few-shot image classification",
         "--categories", "cs.CV",
         "--years", "2025", "2026",
         "--max-results", "10"],
        capture_output=True, text=True, timeout=120,
        cwd=SCRIPTS_DIR
    )
    assert result.returncode == 0, f"Engine failed: {result.stderr}"

    # Parse JSON output
    output = json.loads(result.stdout)
    assert "meta" in output
    assert "papers" in output
    assert "method_categories" in output
    assert "yearly_stats" in output
    assert "keyword_trends" in output
    assert output["meta"]["total_papers"] > 0


def test_engine_with_gibberish_topic():
    """Verify engine handles non-existent topics gracefully."""
    result = subprocess.run(
        [PYTHON, "engine.py",
         "--topic", "zxzxjqkwkqlmcnv",
         "--categories", "cs.CV",
         "--years", "2025", "2026",
         "--max-results", "10"],
        capture_output=True, text=True, timeout=60,
        cwd=SCRIPTS_DIR
    )
    output = json.loads(result.stdout)
    assert output["meta"]["total_papers"] == 0
    assert "warnings" in output["meta"]
