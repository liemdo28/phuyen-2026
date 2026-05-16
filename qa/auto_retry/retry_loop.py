"""
Auto Retry Loop — Runs QA continuously until Zero Audit is achieved.
The loop generates sessions, audits them, and reports until all pass.
"""

import time
import random
from datetime import datetime
from typing import Callable, Optional
from dataclasses import dataclass, field
from typing import List


@dataclass
class LoopConfig:
    max_iterations: int = 100
    sessions_per_iteration: int = 20
    target_pass_rate: float = 100.0  # 100% = zero audit
    min_score_threshold: float = 8.5
    sleep_between_iterations: float = 0.5
    verbose: bool = True
    save_reports: bool = True
    run_regression: bool = True
    early_stop_on_zero: bool = True


@dataclass
class IterationResult:
    iteration: int
    sessions_run: int
    violations: int
    passes: int
    pass_rate: float
    overall_score: float
    zero_audit: bool
    timestamp: str
    regressions: List[str] = field(default_factory=list)


class AutoRetryLoop:
    """Continuously runs QA until zero audit violations remain."""

    def __init__(self, config: Optional[LoopConfig] = None):
        self.config = config or LoopConfig()
        self.history: List[IterationResult] = []
        self._running = False

    def run(
        self,
        ai_handler: Callable[[str], str],
        on_iteration_complete: Optional[Callable] = None,
    ) -> dict:
        """
        Run the auto-retry loop until zero audit is achieved.

        Args:
            ai_handler: Function that takes user message and returns AI response
            on_iteration_complete: Optional callback called after each iteration
        """
        from ..orchestration.qa_orchestrator import QAOrchestrator
        from ..memory.conversation_memory import ConversationMemory
        from ..regression.regression_engine import RegressionEngine
        from ..reporting.report_generator import ReportGenerator

        orchestrator = QAOrchestrator()
        memory = ConversationMemory()
        regression = RegressionEngine()
        reporter = ReportGenerator()
        self._running = True

        print(f"\n{'='*60}")
        print(f"🚀 QA CIVILIZATION LOOP STARTED")
        print(f"{'='*60}")
        print(f"Target: Zero Audit ({self.config.target_pass_rate:.0f}% pass rate)")
        print(f"Sessions per iteration: {self.config.sessions_per_iteration}")
        print(f"Max iterations: {self.config.max_iterations}")
        print(f"{'='*60}\n")

        for iteration in range(1, self.config.max_iterations + 1):
            if not self._running:
                break

            print(f"\n🔄 Iteration {iteration}/{self.config.max_iterations}")
            iter_start = time.time()

            # Run QA batch
            aggregator = orchestrator.run_batch(
                ai_handler=ai_handler,
                num_sessions=self.config.sessions_per_iteration,
                verbose=self.config.verbose,
            )

            summary = aggregator.get_summary()
            violations = summary.get("total_violations", 0)
            passes = summary.get("total_sessions", 0) - summary.get("fail_count", 0)
            pass_rate = summary.get("pass_rate", 0.0)
            score = summary.get("overall_score", 0.0)
            zero = aggregator.zero_audit_achieved()

            # Run regression tests
            regressions = []
            if self.config.run_regression:
                reg_result = regression.run_all(ai_handler)
                regressions = [r["rule"] for r in reg_result.get("regressions", [])]
                if regressions:
                    print(f"⚠️  REGRESSION DETECTED: {regressions}")

            # Record iteration
            result = IterationResult(
                iteration=iteration,
                sessions_run=summary.get("total_sessions", 0),
                violations=violations,
                passes=passes,
                pass_rate=pass_rate,
                overall_score=score,
                zero_audit=zero and not regressions,
                timestamp=datetime.now().isoformat(),
                regressions=regressions,
            )
            self.history.append(result)

            # Record in memory
            violation_rules = list(set(
                v.rule
                for r in aggregator.reports
                for v in r.violations
            ))
            memory.record_run(
                run_id=f"iter_{iteration}",
                score=score,
                violations=violation_rules,
                passes=[],
            )

            # Generate report
            if self.config.save_reports:
                run_report = reporter.generate_run_report(
                    aggregator,
                    run_id=f"iter_{iteration:03d}_{datetime.now().strftime('%H%M%S')}",
                )
                reporter.save_json_report(run_report)
                if iteration % 5 == 0:
                    reporter.save_markdown_report(run_report)

            # Print iteration summary
            elapsed = time.time() - iter_start
            status_icon = "✅" if zero else "❌"
            print(f"\n{status_icon} Iteration {iteration} Summary:")
            print(f"   Score: {score:.1f}/10 | Pass Rate: {pass_rate:.1f}%")
            print(f"   Violations: {violations} | Elapsed: {elapsed:.1f}s")
            if regressions:
                print(f"   ⚠️  Regressions: {len(regressions)}")

            # Trend analysis
            if len(self.history) >= 3:
                trend = self._compute_trend()
                print(f"   Trend: {trend}")

            if on_iteration_complete:
                on_iteration_complete(result, aggregator)

            # Check if we've achieved zero audit
            if zero and not regressions and self.config.early_stop_on_zero:
                print(f"\n{'='*60}")
                print("🏆 ZERO AUDIT ACHIEVED!")
                print(f"   Iterations: {iteration}")
                print(f"   Final Score: {score:.1f}/10")
                print(f"   All sessions passed with zero violations")
                print(f"{'='*60}")

                memory.mark_zero_audit()
                cert_path = reporter.generate_zero_audit_certificate(
                    f"zero_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                )
                print(f"\n🎓 Certificate saved: {cert_path}")
                break

            if iteration < self.config.max_iterations:
                time.sleep(self.config.sleep_between_iterations)

        self._running = False
        return self._final_summary()

    def stop(self):
        """Signal the loop to stop after current iteration."""
        self._running = False

    def _compute_trend(self) -> str:
        """Compute score trend over last 3 iterations."""
        recent = self.history[-3:]
        scores = [r.overall_score for r in recent]
        if scores[-1] > scores[0] + 0.5:
            return "📈 Improving"
        elif scores[-1] < scores[0] - 0.5:
            return "📉 Declining — check for regressions"
        return "➡️ Stable"

    def _final_summary(self) -> dict:
        """Build final loop summary."""
        if not self.history:
            return {"status": "no_iterations_run"}

        last = self.history[-1]
        best = max(self.history, key=lambda r: r.overall_score)
        zero_achieved = any(r.zero_audit for r in self.history)

        return {
            "total_iterations": len(self.history),
            "zero_audit_achieved": zero_achieved,
            "zero_audit_at_iteration": next(
                (r.iteration for r in self.history if r.zero_audit), None
            ),
            "final_score": last.overall_score,
            "best_score": best.overall_score,
            "best_iteration": best.iteration,
            "final_pass_rate": last.pass_rate,
            "total_violations_found": sum(r.violations for r in self.history),
            "score_improvement": round(
                last.overall_score - self.history[0].overall_score, 2
            ) if len(self.history) > 1 else 0,
            "iteration_history": [
                {
                    "iteration": r.iteration,
                    "score": r.overall_score,
                    "pass_rate": r.pass_rate,
                    "violations": r.violations,
                    "zero_audit": r.zero_audit,
                }
                for r in self.history
            ],
        }
