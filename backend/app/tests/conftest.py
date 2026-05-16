"""Pytest configuration for corpus tests — loads ALL_CASES once."""
from __future__ import annotations
from pathlib import Path
import yaml

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "user_queries.yaml"

def _load_fixture():
    with open(FIXTURE_PATH, encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)
    entries = []
    for group_name, cases in raw.items():
        if group_name.startswith("_"):
            continue
        for case in cases:
            entries.append({**case, "_group": group_name})
    return entries

ALL_CASES = _load_fixture()

def pytest_addoption(parser):
    parser.addoption("--intent-only", action="store_true", default=False,
                     help="Skip slow e2e tests")
    parser.addoption("--crash-only", action="store_true", default=False,
                     help="Run only crash_expected entries")
    parser.addoption("--known-fail", action="store_true", default=False,
                     help="Run only known_fail entries")

def pytest_configure(config):
    config.addinivalue_line("markers", "e2e: end-to-end integration tests (slow)")
    config.addinivalue_line("markers", "crash_only: run only crash_expected entries")
    config.addinivalue_line("markers", "known_fail: run only known_fail entries")

def pytest_runtest_setup(item):
    if item.config.getoption("--intent-only", default=False):
        if "TestE2ECrashResistance" in item.nodeid:
            import pytest
            pytest.skip("--intent-only: skipping e2e tests")

def pytest_terminal_summary(terminalreporter, exitstatus, config):
    passed = len(terminalreporter.stats.get("passed", []))
    failed = len(terminalreporter.stats.get("failed", []))
    skipped = len(terminalreporter.stats.get("skipped", []))
    total = passed + failed
    terminalreporter.section("Phú Yên Test Corpus Summary")
    terminalreporter.write_line(f"  Total cases  : {len(ALL_CASES)}")
    terminalreporter.write_line(f"  Passed      : {passed}")
    terminalreporter.write_line(f"  Failed      : {failed}")
    terminalreporter.write_line(f"  Skipped     : {skipped}")
    if total > 0:
        terminalreporter.write_line(f"  Accuracy    : {passed/total*100:.1f}%")
    terminalreporter.write_line("")
    terminalreporter.write_line("  Known gaps:")
    for case in ALL_CASES:
        if case.get("status") in ("crash_expected", "known_fail"):
            terminalreporter.write_line(
                f"    #{case['id']:03d} [{case.get('status')}] {case['text'][:50]}"
            )