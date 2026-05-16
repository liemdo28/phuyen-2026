"""
QA Orchestrator — The master conductor of the Human QA Civilization System.
Coordinates all modules into a unified stress-testing pipeline.
"""

import random
import time
from typing import Callable, Optional, List
from dataclasses import dataclass

from ..simulation.persona_engine import get_weighted_persona, PersonaType
from ..simulation.conversation_generator import ConversationGenerator, ScenarioType
from ..emotional.emotion_engine import EmotionEngine
from ..audit.audit_engine import AuditEngine
from ..scoring.scoring_engine import ScoringEngine, SessionAggregator
from ..reporting.report_generator import ReportGenerator
from ..contextual.context_merger import ContextMerger
from ..fatigue.fatigue_engine import FatigueEngine
from ..sarcasm.sarcasm_engine import SarcasmEngine
from ..nightlife.nightlife_engine import NightlifeEngine
from ..replay.replay_engine import ReplayEngine
from ..travel.travel_chaos import TravelChaosEngine


class QAOrchestrator:
    """Master QA orchestrator — runs the full human simulation pipeline."""

    def __init__(self):
        self.conv_gen = ConversationGenerator()
        self.emotion_engine = EmotionEngine()
        self.audit_engine = AuditEngine()
        self.scoring_engine = ScoringEngine()
        self.context_merger = ContextMerger()
        self.fatigue_engine = FatigueEngine()
        self.sarcasm_engine = SarcasmEngine()
        self.nightlife_engine = NightlifeEngine()
        self.replay_engine = ReplayEngine()
        self.travel_chaos = TravelChaosEngine()

    def run_batch(
        self,
        ai_handler: Callable[[str], str],
        num_sessions: int = 20,
        verbose: bool = True,
    ) -> SessionAggregator:
        """Run a full QA batch and return aggregated results."""
        aggregator = SessionAggregator()
        reporter = ReportGenerator()

        for i in range(num_sessions):
            # Select random scenario type with weighted distribution
            scenario_choice = self._pick_scenario()
            report = self._run_scenario(ai_handler, scenario_choice, verbose)

            if report:
                score = aggregator.add_result(report)
                if verbose:
                    reporter.print_live_report(score, report)

                # Save for replay if failed
                if report.violations:
                    self.replay_engine.save_for_replay(report)

        return aggregator

    def _pick_scenario(self) -> str:
        """Weighted scenario selection."""
        scenarios = [
            ("fragmented_food", 20),
            ("emotional_exhaustion", 15),
            ("slang_casual", 15),
            ("travel_chaos", 12),
            ("nightlife", 8),
            ("sarcasm", 8),
            ("child_safety", 7),
            ("no_accent", 10),
            ("regional_dialect", 5),
        ]
        names = [s[0] for s in scenarios]
        weights = [s[1] for s in scenarios]
        total = sum(weights)
        probs = [w / total for w in weights]
        return random.choices(names, weights=probs, k=1)[0]

    def _run_scenario(
        self,
        ai_handler: Callable[[str], str],
        scenario_type: str,
        verbose: bool,
    ):
        """Run a specific scenario type."""
        try:
            handlers = {
                "fragmented_food": self._run_fragmented_scenario,
                "emotional_exhaustion": self._run_emotional_scenario,
                "slang_casual": self._run_slang_scenario,
                "travel_chaos": self._run_travel_chaos_scenario,
                "nightlife": self._run_nightlife_scenario,
                "sarcasm": self._run_sarcasm_scenario,
                "child_safety": self._run_child_safety_scenario,
                "no_accent": self._run_no_accent_scenario,
                "regional_dialect": self._run_regional_scenario,
            }
            handler = handlers.get(scenario_type, self._run_general_scenario)
            return handler(ai_handler)
        except Exception as e:
            if verbose:
                print(f"   ⚠️ Scenario error ({scenario_type}): {e}")
            return None

    def _run_fragmented_scenario(self, ai_handler):
        """Run fragmented multi-message scenario."""
        from ..fragmented.fragment_engine import FragmentEngine
        fragment_engine = FragmentEngine()

        fragments, merged_intent, intent_type = fragment_engine.build_context_test()

        # Send all fragments and get response to the last one
        # (simulating a real conversation where AI sees all context)
        full_message = " | ".join(fragments)

        try:
            response = ai_handler(full_message)
        except Exception:
            response = ""

        # Audit the response
        persona = get_weighted_persona()
        report = self.audit_engine.audit(
            session_id=self._make_id(),
            user_message=full_message,
            ai_response=response,
            persona=persona,
            scenario="fragmented_order",
            context={"fragments": fragments, "merged_intent": merged_intent},
        )

        # Also do context merge audit
        merge_result = self.context_merger.audit_context_merge(fragments, response)
        for v in merge_result.get("violations", []):
            from ..audit.audit_engine import AuditViolation, AuditSeverity
            report.violations.append(AuditViolation(
                rule=v["rule"],
                severity=AuditSeverity.HIGH,
                reason=v["detail"],
                fix_suggestion="Merge all message fragments into one coherent intent before responding",
                dimension="context_understanding",
            ))

        return report

    def _run_emotional_scenario(self, ai_handler):
        """Run emotional/exhaustion scenario."""
        from ..emotional.emotion_engine import EmotionalState
        from ..fatigue.fatigue_engine import FatigueLevel

        persona = get_weighted_persona()
        state = self.emotion_engine.get_state_from_baseline(persona.emotional_baseline)
        fatigue_level = self.fatigue_engine.detect_fatigue_level(
            random.choice([
                "mệt vl không đi nổi nữa",
                "kiệt sức rồi bé cũng mệt",
                "hết sức rồi về thôi",
                "mệt lắm gần thôi nha",
            ])
        )

        messages = {
            EmotionalState.EXHAUSTED: "mệt vl không đi nổi gần thôi nha",
            EmotionalState.ANGRY: "Sao cứ gợi ý sai vậy??? Lần này cuối cùng",
            EmotionalState.STRESSED: "trời mưa rồi kế hoạch hủy hết giờ đi đâu với bé",
            EmotionalState.HUNGRY_IRRITABLE: "đói LẮMM nhanh gợi ý đi không chịu nổi",
            EmotionalState.BURNOUT: "ừ thôi kệ gợi ý gì cũng được mệt rồi",
        }

        msg = messages.get(state, "mệt rồi đi đâu nghỉ đi")

        try:
            response = ai_handler(msg)
        except Exception:
            response = ""

        report = self.audit_engine.audit(
            session_id=self._make_id(),
            user_message=msg,
            ai_response=response,
            persona=persona,
            emotional_state=state.value,
            scenario="emotional_exhaustion",
        )

        # Add emotional audit
        emotional_result = self.emotion_engine.audit_emotional_response(state, response)
        for v in emotional_result.get("violations", []):
            from ..audit.audit_engine import AuditViolation, AuditSeverity
            report.violations.append(AuditViolation(
                rule=v["rule"],
                severity=AuditSeverity(v["severity"]),
                reason=v["detail"],
                fix_suggestion=f"Respond appropriately for {state.value} emotional state",
                dimension="emotional_awareness",
            ))

        # Add fatigue audit
        fatigue_result = self.fatigue_engine.audit_fatigue_response(fatigue_level, response)
        for v in fatigue_result.get("violations", []):
            from ..audit.audit_engine import AuditViolation, AuditSeverity
            report.violations.append(AuditViolation(
                rule=v["rule"],
                severity=AuditSeverity(v.get("severity", "MEDIUM")),
                reason=v["detail"],
                fix_suggestion="Adjust response for user's fatigue level",
                dimension="emotional_awareness",
            ))

        return report

    def _run_slang_scenario(self, ai_handler):
        """Run slang/Gen Z scenario."""
        slang_messages = [
            "quan chill chill nao local local",
            "doi qua oke goi y di",
            "ez ez ăn gì đỉnh đỉnh thôi",
            "vl ngon không bro",
            "mệt vl cần chill spot",
            "flex một cái đi npc mode off",
            "lowkey đói highkey muốn hải sản",
        ]

        msg = random.choice(slang_messages)
        persona = get_weighted_persona()

        try:
            response = ai_handler(msg)
        except Exception:
            response = ""

        return self.audit_engine.audit(
            session_id=self._make_id(),
            user_message=msg,
            ai_response=response,
            persona=persona,
            scenario="slang_casual",
        )

    def _run_travel_chaos_scenario(self, ai_handler):
        """Run travel disruption scenario."""
        scenario = self.travel_chaos.get_random_scenario()
        msg = random.choice(scenario.user_messages)
        persona = get_weighted_persona()

        try:
            response = ai_handler(msg)
        except Exception:
            response = ""

        report = self.audit_engine.audit(
            session_id=self._make_id(),
            user_message=msg,
            ai_response=response,
            persona=persona,
            scenario="travel_chaos",
        )

        # Check scenario-specific failures
        from ..audit.audit_engine import AuditViolation, AuditSeverity
        for fail_condition in scenario.fail_conditions:
            if self._check_fail_condition(fail_condition, response):
                report.violations.append(AuditViolation(
                    rule=f"travel_chaos_{scenario.chaos_type.value}",
                    severity=AuditSeverity.HIGH if scenario.urgency == "high" else AuditSeverity.CRITICAL,
                    reason=f"Failed: {fail_condition}",
                    fix_suggestion=f"Expected: {scenario.expected_ai_behavior}",
                    dimension="travel_orchestration",
                ))

        return report

    def _run_nightlife_scenario(self, ai_handler):
        """Run nightlife/late-night scenario."""
        state = self.nightlife_engine.get_random_state()
        msg = self.nightlife_engine.get_message(state)
        transformed = self.nightlife_engine.apply_drunk_transform(msg, state)
        persona = get_weighted_persona()

        try:
            response = ai_handler(transformed)
        except Exception:
            response = ""

        report = self.audit_engine.audit(
            session_id=self._make_id(),
            user_message=transformed,
            ai_response=response,
            persona=persona,
            emotional_state=state.value,
            scenario="nightlife",
        )

        # Nightlife-specific audit
        nightlife_result = self.nightlife_engine.audit_nightlife_response(state, response)
        for v in nightlife_result.get("violations", []):
            from ..audit.audit_engine import AuditViolation, AuditSeverity
            report.violations.append(AuditViolation(
                rule=v["rule"],
                severity=AuditSeverity(v.get("severity", "MEDIUM")),
                reason=v["detail"],
                fix_suggestion="Adjust response for nightlife context",
                dimension="emotional_awareness",
            ))

        return report

    def _run_sarcasm_scenario(self, ai_handler):
        """Run sarcasm detection scenario."""
        case = self.sarcasm_engine.get_random_case()
        persona = get_weighted_persona()

        try:
            response = ai_handler(case.message)
        except Exception:
            response = ""

        report = self.audit_engine.audit(
            session_id=self._make_id(),
            user_message=case.message,
            ai_response=response,
            persona=persona,
            scenario="sarcasm",
        )

        sarcasm_result = self.sarcasm_engine.audit_sarcasm_response(case, response)
        for v in sarcasm_result.get("violations", []):
            from ..audit.audit_engine import AuditViolation, AuditSeverity
            report.violations.append(AuditViolation(
                rule=v["rule"],
                severity=AuditSeverity(v.get("severity", "HIGH")),
                reason=v["detail"],
                fix_suggestion="Detect sarcasm and respond to underlying intent",
                dimension="emotional_awareness",
            ))

        return report

    def _run_child_safety_scenario(self, ai_handler):
        """Run child safety critical scenario."""
        messages = [
            "bé 4 tuổi có tắm biển được không sóng lớn",
            "con muốn xuống biển lá cờ đỏ là sao",
            "bé bơi ở đây có an toàn không",
            "cho bé ra biển có sứa không",
            "trẻ em 4 tuổi leo Gành Đá Đĩa được không",
        ]

        msg = random.choice(messages)
        persona = get_weighted_persona()

        try:
            response = ai_handler(msg)
        except Exception:
            response = ""

        return self.audit_engine.audit(
            session_id=self._make_id(),
            user_message=msg,
            ai_response=response,
            persona=persona,
            scenario="child_safety",
        )

    def _run_no_accent_scenario(self, ai_handler):
        """Run no-accent Vietnamese scenario."""
        from ..no_accent.no_accent_engine import NoAccentEngine
        no_accent = NoAccentEngine()

        original_messages = [
            "quán hải sản ngon ở đâu",
            "ăn gì bây giờ gần đây",
            "không biết đường đi Gành Đá Đĩa",
            "gần đây có quán cafe nào yên tĩnh không",
            "muốn ăn hải sản tươi được không",
        ]

        original = random.choice(original_messages)
        no_accent_msg = no_accent.generate_no_accent_message(original)
        persona = get_weighted_persona()

        try:
            response = ai_handler(no_accent_msg)
        except Exception:
            response = ""

        return self.audit_engine.audit(
            session_id=self._make_id(),
            user_message=no_accent_msg,
            ai_response=response,
            persona=persona,
            scenario="slang_casual",
        )

    def _run_regional_scenario(self, ai_handler):
        """Run regional dialect scenario."""
        from ..regional.dialect_engine import DialectEngine
        dialect = DialectEngine()

        region = dialect.get_random_region()
        msg = dialect.get_sample_phrase(region)
        persona = get_weighted_persona()

        try:
            response = ai_handler(msg)
        except Exception:
            response = ""

        return self.audit_engine.audit(
            session_id=self._make_id(),
            user_message=msg,
            ai_response=response,
            persona=persona,
            scenario="slang_casual",
        )

    def _run_general_scenario(self, ai_handler):
        """Run a general random scenario."""
        persona = get_weighted_persona()
        session = self.conv_gen.generate_session(persona)

        msg = session.turns[0].message if session.turns else "ăn gì bây giờ"

        try:
            response = ai_handler(msg)
        except Exception:
            response = ""

        return self.audit_engine.audit(
            session_id=self._make_id(),
            user_message=msg,
            ai_response=response,
            persona=persona,
            scenario=session.scenario.value,
        )

    def _check_fail_condition(self, condition: str, response: str) -> bool:
        """Check if a fail condition is present in the response."""
        condition_lower = condition.lower()
        response_lower = response.lower()

        # Map natural language conditions to detection logic
        if "too long" in condition_lower or "too verbose" in condition_lower:
            return len(response) > 500
        if "outdoor activities" in condition_lower:
            return any(w in response_lower for w in ["biển", "leo", "đi bộ", "ngoài trời"])
        if "ignores" in condition_lower:
            return len(response) < 30
        return False

    def _make_id(self) -> str:
        import uuid
        return str(uuid.uuid4())[:8]
