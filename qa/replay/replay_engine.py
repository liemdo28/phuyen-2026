"""
Replay Engine — Replays failed conversation scenarios to verify fixes.
Supports replayable audit records and regression test replays.
"""

import json
import os
from typing import List, Optional, Callable
from dataclasses import dataclass

from ..audit.audit_engine import AuditReport, AuditResult
from ..simulation.conversation_generator import ConversationSession


@dataclass
class ReplayResult:
    original_session_id: str
    replay_attempt: int
    original_audit: AuditResult
    replay_audit: AuditResult
    violations_before: List[str]
    violations_after: List[str]
    fixed: List[str]
    regressed: List[str]
    improvement: float


class ReplayEngine:
    """Replays failed sessions to verify AI improvements."""

    def __init__(self, replay_dir: str = "qa/replays"):
        self.replay_dir = replay_dir
        os.makedirs(replay_dir, exist_ok=True)
        self._replays: List[dict] = []

    def save_for_replay(self, report: AuditReport):
        """Save a failed session for future replay."""
        if not report.violations:
            return

        record = {
            "session_id": report.session_id,
            "user_message": report.user_message,
            "detected_intent": report.detected_intent,
            "audit_result": report.audit_result.value,
            "severity": report.severity.value,
            "violations": [
                {
                    "rule": v.rule,
                    "severity": v.severity.value,
                    "reason": v.reason,
                    "fix_suggestion": v.fix_suggestion,
                    "dimension": v.dimension,
                }
                for v in report.violations
            ],
            "persona_type": report.persona_type,
            "emotional_state": report.emotional_state,
            "replayable": report.replayable,
        }

        path = os.path.join(self.replay_dir, f"{report.session_id}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False, indent=2)

        self._replays.append(record)

    def load_replays(self) -> List[dict]:
        """Load all saved replay records."""
        replays = []
        for fname in os.listdir(self.replay_dir):
            if fname.endswith(".json"):
                path = os.path.join(self.replay_dir, fname)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        replays.append(json.load(f))
                except Exception:
                    continue
        return replays

    def replay_session(
        self,
        record: dict,
        ai_handler: Callable[[str], str],
        attempt: int = 1,
    ) -> ReplayResult:
        """Replay a failed session against the current AI."""
        from ..audit.audit_engine import AuditEngine

        engine = AuditEngine()
        user_message = record["user_message"]

        # Get fresh AI response
        try:
            new_response = ai_handler(user_message)
        except Exception as e:
            new_response = f"[ERROR: {str(e)}]"

        # Re-audit
        new_report = engine.audit(
            session_id=f"{record['session_id']}_replay_{attempt}",
            user_message=user_message,
            ai_response=new_response,
            scenario=record.get("detected_intent"),
        )

        violations_before = [v["rule"] for v in record.get("violations", [])]
        violations_after = [v.rule for v in new_report.violations]

        fixed = [v for v in violations_before if v not in violations_after]
        regressed = [v for v in violations_after if v not in violations_before]

        original_count = len(violations_before)
        new_count = len(violations_after)
        improvement = max(0.0, (original_count - new_count) / max(1, original_count))

        return ReplayResult(
            original_session_id=record["session_id"],
            replay_attempt=attempt,
            original_audit=AuditResult(record["audit_result"]),
            replay_audit=new_report.audit_result,
            violations_before=violations_before,
            violations_after=violations_after,
            fixed=fixed,
            regressed=regressed,
            improvement=improvement,
        )

    def run_replay_batch(
        self,
        ai_handler: Callable[[str], str],
        max_replays: int = 50,
    ) -> dict:
        """Run all saved replays and return summary."""
        replays = self.load_replays()[:max_replays]
        results = []

        for record in replays:
            if not record.get("replayable", True):
                continue
            result = self.replay_session(record, ai_handler)
            results.append(result)

        total = len(results)
        fully_fixed = sum(1 for r in results if not r.violations_after)
        improved = sum(1 for r in results if r.improvement > 0)
        regressed = sum(1 for r in results if r.regressed)

        return {
            "total_replays": total,
            "fully_fixed": fully_fixed,
            "improved": improved,
            "regressed": regressed,
            "fix_rate": round(fully_fixed / max(1, total) * 100, 1),
            "improvement_rate": round(improved / max(1, total) * 100, 1),
            "results": results,
        }

    def get_replay_scenarios(self) -> dict:
        """Get categorized replay scenarios."""
        replays = self.load_replays()

        categories = {
            "emotional": [],
            "slang": [],
            "fragmented": [],
            "nightlife": [],
            "child_safety": [],
            "routing": [],
            "other": [],
        }

        for r in replays:
            intent = r.get("detected_intent", "")
            persona = r.get("persona_type", "")

            if "emotional" in intent or persona in ["angry_customer", "exhausted_traveler"]:
                categories["emotional"].append(r)
            elif persona in ["gen_z", "no_accent", "meme_user"]:
                categories["slang"].append(r)
            elif "fragmented" in intent:
                categories["fragmented"].append(r)
            elif "nightlife" in intent or persona == "drunk_user":
                categories["nightlife"].append(r)
            elif "child" in str(r.get("violations", "")).lower():
                categories["child_safety"].append(r)
            elif "routing" in intent or "location" in intent:
                categories["routing"].append(r)
            else:
                categories["other"].append(r)

        return {k: v for k, v in categories.items() if v}
