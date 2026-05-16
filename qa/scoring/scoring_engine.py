"""
Scoring Engine — Multi-dimensional QA scoring model.
Aggregates audit results into human-readable quality scores.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from ..audit.audit_engine import AuditReport, AuditResult, AuditSeverity


@dataclass
class QAScore:
    session_id: str
    human_naturalness: float
    slang_understanding: float
    emotional_awareness: float
    travel_orchestration: float
    fatigue_awareness: float
    cultural_understanding: float
    hallucination_risk_score: float  # higher = safer
    recommendation_quality: float
    conversation_continuity: float
    context_understanding: float
    overall_score: float
    grade: str
    pass_fail: str
    improvement_priority: List[str] = field(default_factory=list)
    raw_violations: int = 0
    raw_passes: int = 0


GRADE_THRESHOLDS = {
    "S": 9.5,
    "A+": 9.0,
    "A": 8.5,
    "B+": 8.0,
    "B": 7.5,
    "C+": 7.0,
    "C": 6.5,
    "D": 6.0,
    "F": 0.0,
}

DIMENSION_WEIGHTS = {
    "human_naturalness": 0.15,
    "slang_understanding": 0.10,
    "emotional_awareness": 0.15,
    "travel_orchestration": 0.12,
    "fatigue_awareness": 0.08,
    "cultural_understanding": 0.10,
    "hallucination_risk": 0.10,
    "recommendation_quality": 0.12,
    "conversation_continuity": 0.08,
}


class ScoringEngine:
    """Computes QA scores from audit reports."""

    def score_report(self, report: AuditReport) -> QAScore:
        """Compute dimensional scores from a single audit report."""
        dim = report.dimension_scores

        hn = dim.get("human_naturalness", 1.0) * 10
        su = dim.get("slang_understanding", 1.0) * 10
        ea = dim.get("emotional_awareness", 1.0) * 10
        cu = dim.get("cultural_understanding", 1.0) * 10
        hr = dim.get("hallucination_risk", 1.0) * 10
        rq = dim.get("recommendation_quality", 1.0) * 10
        cc = dim.get("conversation_continuity", 1.0) * 10
        ctx = dim.get("context_understanding", 1.0) * 10

        # Derived scores
        travel_orch = (rq + ctx + cc) / 3
        fatigue_aware = ea  # maps to emotional awareness for now

        overall = (
            hn * DIMENSION_WEIGHTS["human_naturalness"] +
            su * DIMENSION_WEIGHTS["slang_understanding"] +
            ea * DIMENSION_WEIGHTS["emotional_awareness"] +
            travel_orch * DIMENSION_WEIGHTS["travel_orchestration"] +
            fatigue_aware * DIMENSION_WEIGHTS["fatigue_awareness"] +
            cu * DIMENSION_WEIGHTS["cultural_understanding"] +
            hr * DIMENSION_WEIGHTS["hallucination_risk"] +
            rq * DIMENSION_WEIGHTS["recommendation_quality"] +
            cc * DIMENSION_WEIGHTS["conversation_continuity"]
        ) / sum(DIMENSION_WEIGHTS.values())

        # Scores are already 0-10; clamp for safety
        overall = min(10.0, max(0.0, overall))

        grade = self._compute_grade(overall)
        pass_fail = "PASS" if overall >= 7.0 and report.audit_result != AuditResult.FAIL else "FAIL"

        priorities = self._compute_priorities(dim, report)

        return QAScore(
            session_id=report.session_id,
            human_naturalness=round(hn, 1),
            slang_understanding=round(su, 1),
            emotional_awareness=round(ea, 1),
            travel_orchestration=round(travel_orch, 1),
            fatigue_awareness=round(fatigue_aware, 1),
            cultural_understanding=round(cu, 1),
            hallucination_risk_score=round(hr, 1),
            recommendation_quality=round(rq, 1),
            conversation_continuity=round(cc, 1),
            context_understanding=round(ctx, 1),
            overall_score=round(overall, 1),
            grade=grade,
            pass_fail=pass_fail,
            improvement_priority=priorities,
            raw_violations=len(report.violations),
            raw_passes=len(report.passed_checks),
        )

    def aggregate_scores(self, scores: List[QAScore]) -> dict:
        """Aggregate multiple scores into session-level statistics."""
        if not scores:
            return {}

        def avg(attr):
            return round(sum(getattr(s, attr) for s in scores) / len(scores), 2)

        overall_avg = avg("overall_score")
        pass_count = sum(1 for s in scores if s.pass_fail == "PASS")
        fail_count = len(scores) - pass_count

        grade_dist = {}
        for s in scores:
            grade_dist[s.grade] = grade_dist.get(s.grade, 0) + 1

        # Find worst dimensions
        dim_avgs = {
            "human_naturalness": avg("human_naturalness"),
            "slang_understanding": avg("slang_understanding"),
            "emotional_awareness": avg("emotional_awareness"),
            "travel_orchestration": avg("travel_orchestration"),
            "fatigue_awareness": avg("fatigue_awareness"),
            "cultural_understanding": avg("cultural_understanding"),
            "hallucination_risk_score": avg("hallucination_risk_score"),
            "recommendation_quality": avg("recommendation_quality"),
            "conversation_continuity": avg("conversation_continuity"),
        }

        worst_dims = sorted(dim_avgs.items(), key=lambda x: x[1])[:3]

        return {
            "total_sessions": len(scores),
            "pass_count": pass_count,
            "fail_count": fail_count,
            "pass_rate": round(pass_count / len(scores) * 100, 1),
            "overall_score": overall_avg,
            "grade": self._compute_grade(overall_avg),
            "dimension_averages": dim_avgs,
            "worst_dimensions": [d[0] for d in worst_dims],
            "grade_distribution": grade_dist,
            "total_violations": sum(s.raw_violations for s in scores),
            "total_passes": sum(s.raw_passes for s in scores),
        }

    def _compute_grade(self, score: float) -> str:
        for grade, threshold in GRADE_THRESHOLDS.items():
            if score >= threshold:
                return grade
        return "F"

    def _compute_priorities(self, dim: dict, report: AuditReport) -> list:
        """Compute improvement priorities from dimension scores."""
        priorities = []

        # Sort dimensions by score (lowest first)
        sorted_dims = sorted(dim.items(), key=lambda x: x[1])

        for d, score in sorted_dims[:3]:
            if score < 0.8:
                priorities.append(f"Improve {d.replace('_', ' ')}: {score * 10:.1f}/10")

        # Add specific violation-based priorities
        for v in report.violations[:2]:
            priority = f"Fix: {v.rule} ({v.severity.value})"
            if priority not in priorities:
                priorities.append(priority)

        return priorities


class SessionAggregator:
    """Aggregates QA results across a full test run."""

    def __init__(self):
        self.scores: List[QAScore] = []
        self.reports: List[AuditReport] = []
        self.engine = ScoringEngine()

    def add_result(self, report: AuditReport) -> QAScore:
        score = self.engine.score_report(report)
        self.scores.append(score)
        self.reports.append(report)
        return score

    def get_summary(self) -> dict:
        return self.engine.aggregate_scores(self.scores)

    def get_failing_sessions(self) -> List[QAScore]:
        return [s for s in self.scores if s.pass_fail == "FAIL"]

    def get_critical_violations(self) -> list:
        critical = []
        for r in self.reports:
            for v in r.violations:
                if v.severity == AuditSeverity.CRITICAL:
                    critical.append({
                        "session_id": r.session_id,
                        "rule": v.rule,
                        "message": r.user_message,
                        "reason": v.reason,
                        "fix": v.fix_suggestion,
                    })
        return critical

    def zero_audit_achieved(self) -> bool:
        """True when all sessions pass with zero violations."""
        return all(s.pass_fail == "PASS" for s in self.scores) and \
               all(len(r.violations) == 0 for r in self.reports)

    def violation_count(self) -> int:
        return sum(len(r.violations) for r in self.reports)
