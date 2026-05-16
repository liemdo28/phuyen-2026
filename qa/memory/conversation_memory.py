"""
Conversation Memory — Tracks QA session state, past violations,
and learning evolution across test runs.
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class ViolationRecord:
    rule: str
    count: int
    first_seen: str
    last_seen: str
    fixed: bool = False
    fix_confirmed: bool = False


@dataclass
class SlangLearning:
    term: str
    discovered: str
    category: str  # gen_z, regional, meme, nightlife, etc.
    usage_count: int = 1


@dataclass
class QAMemory:
    """Persistent QA memory across test runs."""
    run_history: List[dict] = field(default_factory=list)
    known_violations: Dict[str, ViolationRecord] = field(default_factory=dict)
    slang_corpus: List[SlangLearning] = field(default_factory=list)
    fixed_rules: List[str] = field(default_factory=list)
    regression_failures: List[dict] = field(default_factory=list)
    best_score_ever: float = 0.0
    zero_audit_achieved: bool = False
    zero_audit_date: Optional[str] = None
    total_sessions_run: int = 0
    total_violations_found: int = 0
    total_violations_fixed: int = 0
    evolution_log: List[str] = field(default_factory=list)


class ConversationMemory:
    """Manages persistent QA memory and learning."""

    def __init__(self, memory_path: str = "qa/memory/qa_memory.json"):
        self.memory_path = memory_path
        os.makedirs(os.path.dirname(memory_path), exist_ok=True)
        self.memory = self._load()

    def _load(self) -> QAMemory:
        if os.path.exists(self.memory_path):
            try:
                with open(self.memory_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                memory = QAMemory()
                memory.run_history = data.get("run_history", [])
                memory.fixed_rules = data.get("fixed_rules", [])
                memory.regression_failures = data.get("regression_failures", [])
                memory.best_score_ever = data.get("best_score_ever", 0.0)
                memory.zero_audit_achieved = data.get("zero_audit_achieved", False)
                memory.zero_audit_date = data.get("zero_audit_date")
                memory.total_sessions_run = data.get("total_sessions_run", 0)
                memory.total_violations_found = data.get("total_violations_found", 0)
                memory.total_violations_fixed = data.get("total_violations_fixed", 0)
                memory.evolution_log = data.get("evolution_log", [])

                # Rebuild violation records
                for rule, vdata in data.get("known_violations", {}).items():
                    memory.known_violations[rule] = ViolationRecord(**vdata)

                # Rebuild slang corpus
                for sdata in data.get("slang_corpus", []):
                    memory.slang_corpus.append(SlangLearning(**sdata))

                return memory
            except Exception:
                pass
        return QAMemory()

    def save(self):
        data = {
            "run_history": self.memory.run_history,
            "fixed_rules": self.memory.fixed_rules,
            "regression_failures": self.memory.regression_failures,
            "best_score_ever": self.memory.best_score_ever,
            "zero_audit_achieved": self.memory.zero_audit_achieved,
            "zero_audit_date": self.memory.zero_audit_date,
            "total_sessions_run": self.memory.total_sessions_run,
            "total_violations_found": self.memory.total_violations_found,
            "total_violations_fixed": self.memory.total_violations_fixed,
            "evolution_log": self.memory.evolution_log,
            "known_violations": {
                rule: asdict(vr) for rule, vr in self.memory.known_violations.items()
            },
            "slang_corpus": [asdict(s) for s in self.memory.slang_corpus],
        }
        with open(self.memory_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def record_run(self, run_id: str, score: float, violations: List[str], passes: List[str]):
        """Record a QA run result."""
        self.memory.total_sessions_run += 1
        self.memory.total_violations_found += len(violations)

        if score > self.memory.best_score_ever:
            self.memory.best_score_ever = score
            self.memory.evolution_log.append(
                f"{datetime.now().isoformat()} — New best score: {score:.1f}"
            )

        self.memory.run_history.append({
            "run_id": run_id,
            "timestamp": datetime.now().isoformat(),
            "score": score,
            "violations": violations,
            "passes": passes,
        })

        # Track violations
        now = datetime.now().isoformat()
        for rule in violations:
            if rule in self.memory.known_violations:
                vr = self.memory.known_violations[rule]
                vr.count += 1
                vr.last_seen = now
            else:
                self.memory.known_violations[rule] = ViolationRecord(
                    rule=rule,
                    count=1,
                    first_seen=now,
                    last_seen=now,
                )

        self.save()

    def mark_fixed(self, rule: str):
        """Mark a violation rule as fixed."""
        if rule in self.memory.known_violations:
            self.memory.known_violations[rule].fixed = True
        if rule not in self.memory.fixed_rules:
            self.memory.fixed_rules.append(rule)
            self.memory.total_violations_fixed += 1
        self.save()

    def check_regression(self, violations: List[str]) -> List[str]:
        """Check if any fixed violations have regressed."""
        regressions = []
        for rule in violations:
            if rule in self.memory.fixed_rules:
                regressions.append(rule)
                self.memory.regression_failures.append({
                    "rule": rule,
                    "detected_at": datetime.now().isoformat(),
                })
        return regressions

    def learn_slang(self, term: str, category: str):
        """Add new slang term to corpus."""
        existing = next((s for s in self.memory.slang_corpus if s.term == term), None)
        if existing:
            existing.usage_count += 1
        else:
            self.memory.slang_corpus.append(SlangLearning(
                term=term,
                discovered=datetime.now().isoformat(),
                category=category,
            ))
        self.save()

    def get_persistent_violations(self) -> List[ViolationRecord]:
        """Get violations that have appeared multiple times without being fixed."""
        return [
            vr for vr in self.memory.known_violations.values()
            if vr.count >= 3 and not vr.fixed
        ]

    def mark_zero_audit(self):
        """Record that zero audit was achieved."""
        self.memory.zero_audit_achieved = True
        self.memory.zero_audit_date = datetime.now().isoformat()
        self.memory.evolution_log.append(
            f"{datetime.now().isoformat()} — 🏆 ZERO AUDIT ACHIEVED!"
        )
        self.save()

    def get_evolution_summary(self) -> dict:
        """Get the evolution summary of QA improvements over time."""
        recent_runs = self.memory.run_history[-10:] if self.memory.run_history else []
        scores = [r["score"] for r in recent_runs if r.get("score")]

        return {
            "total_runs": self.memory.total_sessions_run,
            "total_violations_found": self.memory.total_violations_found,
            "total_violations_fixed": self.memory.total_violations_fixed,
            "fix_rate": round(
                self.memory.total_violations_fixed / max(1, self.memory.total_violations_found) * 100, 1
            ),
            "best_score": self.memory.best_score_ever,
            "recent_scores": scores,
            "score_trend": "improving" if len(scores) >= 2 and scores[-1] > scores[0] else "stable",
            "zero_audit_achieved": self.memory.zero_audit_achieved,
            "zero_audit_date": self.memory.zero_audit_date,
            "persistent_violations": len(self.get_persistent_violations()),
            "slang_terms_learned": len(self.memory.slang_corpus),
            "recent_evolution": self.memory.evolution_log[-5:],
        }
