"""
Minimal regression runner for autonomous QA.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Callable


class RegressionEngine:
    def __init__(self, root_dir: str | Path = "qa/regression/results"):
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def run_all(self, ai_handler: Callable[[str], str]) -> dict[str, object]:
        scenarios = [
            ("doi chet roi", ("ăn", "quán", "hải sản", "bún", "chè", "bia")),
            ("met vl ko muon di xa", ("gần", "nghỉ", "cafe", "đỡ", "share")),
            ("co maps ko", ("maps", "địa điểm", "vị trí", "share")),
        ]
        failed: list[dict[str, object]] = []
        for message, expected_markers in scenarios:
            response = ai_handler(message)
            if not any(marker in response.casefold() for marker in expected_markers):
                failed.append({"message": message, "response": response})

        result = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": len(scenarios),
            "passed": len(scenarios) - len(failed),
            "failed": len(failed),
            "pass_rate": ((len(scenarios) - len(failed)) / len(scenarios) * 100.0) if scenarios else 100.0,
            "regressions": failed,
            "regression_free": not failed,
        }
        path = self.root_dir / f"regression_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        return result
