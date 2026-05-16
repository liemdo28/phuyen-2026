"""
Regression Engine — Ensures previously fixed violations do not return.
Maintains a test suite of fixed cases and re-runs them on every QA cycle.
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, field


@dataclass
class RegressionTest:
    test_id: str
    rule: str
    user_message: str
    expected_pass: bool
    description: str
    fixed_at: str
    dimension: str
    tags: List[str] = field(default_factory=list)


@dataclass
class RegressionResult:
    test_id: str
    rule: str
    passed: bool
    regressed: bool
    violations_found: List[str]
    timestamp: str


class RegressionEngine:
    """Manages and runs regression tests for fixed violations."""

    BASELINE_TESTS = [
        RegressionTest(
            test_id="reg_001",
            rule="robotic_corporate_tone",
            user_message="đói quá ăn gì bây giờ",
            expected_pass=True,
            description="Casual hunger query should get natural, friendly response",
            fixed_at="v1.0",
            dimension="human_naturalness",
            tags=["tone", "casual", "food"],
        ),
        RegressionTest(
            test_id="reg_002",
            rule="missed_hunger_signal",
            user_message="đói vl luôn",
            expected_pass=True,
            description="Hunger slang should trigger food recommendation",
            fixed_at="v1.0",
            dimension="slang_understanding",
            tags=["slang", "food", "gen_z"],
        ),
        RegressionTest(
            test_id="reg_003",
            rule="energetic_suggestion_to_exhausted_user",
            user_message="mệt vl không đi nổi rồi",
            expected_pass=True,
            description="Exhausted user should get rest suggestion not more activities",
            fixed_at="v1.0",
            dimension="emotional_awareness",
            tags=["fatigue", "emotional", "recovery"],
        ),
        RegressionTest(
            test_id="reg_004",
            rule="missed_child_beach_safety",
            user_message="bé 4 tuổi có tắm biển được không",
            expected_pass=True,
            description="Child beach query must get safety assessment",
            fixed_at="v1.0",
            dimension="cultural_correctness",
            tags=["child_safety", "beach", "critical"],
        ),
        RegressionTest(
            test_id="reg_005",
            rule="formal_response_to_slang_user",
            user_message="quan chill chill nao local local",
            expected_pass=True,
            description="No-accent slang query should get casual response",
            fixed_at="v1.0",
            dimension="slang_understanding",
            tags=["no_accent", "slang", "local"],
        ),
        RegressionTest(
            test_id="reg_006",
            rule="response_too_long_for_drunk_user",
            user_message="di dau tiep theo",
            expected_pass=True,
            description="Late-night/drunk query should get brief response",
            fixed_at="v1.0",
            dimension="emotional_awareness",
            tags=["nightlife", "drunk", "length"],
        ),
        RegressionTest(
            test_id="reg_007",
            rule="language_mismatch",
            user_message="ăn gì bây giờ vậy",
            expected_pass=True,
            description="Vietnamese message should get Vietnamese response",
            fixed_at="v1.0",
            dimension="cultural_understanding",
            tags=["language", "vietnamese"],
        ),
        RegressionTest(
            test_id="reg_008",
            rule="choice_overload",
            user_message="quán hải sản ngon đâu",
            expected_pass=True,
            description="Simple food query should get max 3 recommendations",
            fixed_at="v1.0",
            dimension="recommendation_quality",
            tags=["overload", "food", "recommendations"],
        ),
        RegressionTest(
            test_id="reg_009",
            rule="dismissive_to_angry_user",
            user_message="Quán đó bị chặt chém rồi sao còn gợi ý???",
            expected_pass=True,
            description="Angry complaint should get empathetic response",
            fixed_at="v1.0",
            dimension="emotional_awareness",
            tags=["anger", "complaint", "emotional"],
        ),
        RegressionTest(
            test_id="reg_010",
            rule="ai_took_sarcasm_literally",
            user_message="Hay thật đấy, gợi ý chỗ tourist trap 🙄",
            expected_pass=True,
            description="Sarcasm should be detected, not taken literally",
            fixed_at="v1.0",
            dimension="emotional_awareness",
            tags=["sarcasm", "emotional", "detection"],
        ),
        RegressionTest(
            test_id="reg_011",
            rule="distant_recommendation_for_exhausted",
            user_message="mệt vl gần đây thôi nha",
            expected_pass=True,
            description="Exhausted user should only get nearby suggestions",
            fixed_at="v1.0",
            dimension="fatigue_awareness",
            tags=["fatigue", "distance", "recovery"],
        ),
        RegressionTest(
            test_id="reg_012",
            rule="unhelpful_non_answer",
            user_message="tôm hùm Sông Cầu giá bao nhiêu",
            expected_pass=True,
            description="Lobster price query should get approximate price info",
            fixed_at="v1.0",
            dimension="recommendation_quality",
            tags=["food", "pricing", "local"],
        ),
    ]

    def __init__(self, results_dir: str = "qa/regression/results"):
        self.results_dir = results_dir
        os.makedirs(results_dir, exist_ok=True)
        self.tests = self.BASELINE_TESTS.copy()

    def add_test(self, test: RegressionTest):
        """Add a new regression test from a fixed violation."""
        if not any(t.test_id == test.test_id for t in self.tests):
            self.tests.append(test)

    def from_fixed_violation(
        self,
        rule: str,
        user_message: str,
        dimension: str,
        description: str,
    ) -> RegressionTest:
        """Create a regression test from a just-fixed violation."""
        test_id = f"reg_{len(self.tests) + 1:03d}_auto"
        test = RegressionTest(
            test_id=test_id,
            rule=rule,
            user_message=user_message,
            expected_pass=True,
            description=description,
            fixed_at=datetime.now().isoformat(),
            dimension=dimension,
            tags=["auto_generated"],
        )
        self.add_test(test)
        return test

    def run_all(self, ai_handler: Callable[[str], str]) -> dict:
        """Run all regression tests and return results."""
        from ..audit.audit_engine import AuditEngine
        engine = AuditEngine()
        results = []
        regressions = []

        for test in self.tests:
            try:
                response = ai_handler(test.user_message)
            except Exception as e:
                response = f"[ERROR: {e}]"

            report = engine.audit(
                session_id=test.test_id,
                user_message=test.user_message,
                ai_response=response,
                scenario=test.dimension,
            )

            violation_rules = [v.rule for v in report.violations]
            passed = test.rule not in violation_rules

            if not passed and test.expected_pass:
                regressions.append({
                    "test_id": test.test_id,
                    "rule": test.rule,
                    "description": test.description,
                    "tags": test.tags,
                })

            result = RegressionResult(
                test_id=test.test_id,
                rule=test.rule,
                passed=passed,
                regressed=not passed and test.expected_pass,
                violations_found=violation_rules,
                timestamp=datetime.now().isoformat(),
            )
            results.append(result)

        total = len(results)
        passed_count = sum(1 for r in results if r.passed)

        run_report = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": total,
            "passed": passed_count,
            "failed": total - passed_count,
            "regressions": regressions,
            "pass_rate": round(passed_count / max(1, total) * 100, 1),
            "regression_free": len(regressions) == 0,
        }

        self._save_run(run_report)
        return run_report

    def _save_run(self, report: dict):
        fname = f"regression_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        path = os.path.join(self.results_dir, fname)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

    def get_tagged_tests(self, tag: str) -> List[RegressionTest]:
        """Get all tests with a specific tag."""
        return [t for t in self.tests if tag in t.tags]

    def get_critical_tests(self) -> List[RegressionTest]:
        """Get tests tagged as critical."""
        return self.get_tagged_tests("critical")
