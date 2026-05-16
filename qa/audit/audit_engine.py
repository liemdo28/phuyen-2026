"""
Audit Engine — Detects violations in AI responses across all quality dimensions.
This is the core quality gate that generates structured audit reports.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from enum import Enum


class AuditSeverity(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AuditResult(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"


@dataclass
class AuditViolation:
    rule: str
    severity: AuditSeverity
    reason: str
    fix_suggestion: str
    dimension: str


@dataclass
class AuditReport:
    session_id: str
    user_message: str
    detected_intent: str
    expected_behavior: str
    actual_response: str
    audit_result: AuditResult
    severity: AuditSeverity
    violations: List[AuditViolation] = field(default_factory=list)
    passed_checks: List[str] = field(default_factory=list)
    dimension_scores: Dict[str, float] = field(default_factory=dict)
    replayable: bool = True
    persona_type: Optional[str] = None
    emotional_state: Optional[str] = None
    metadata: Dict = field(default_factory=dict)


# ── Audit Rules ─────────────────────────────────────────────

class AuditEngine:
    """Multi-dimensional AI response auditor."""

    def audit(
        self,
        session_id: str,
        user_message: str,
        ai_response: str,
        persona=None,
        emotional_state: str = None,
        scenario: str = None,
        context: dict = None,
    ) -> AuditReport:
        """Run all audit checks and return structured report."""

        violations = []
        passed = []
        context = context or {}

        # Run all audit dimensions
        violations += self._check_robotic_tone(user_message, ai_response, passed)
        violations += self._check_corporate_language(ai_response, passed)
        violations += self._check_emotional_mismatch(user_message, ai_response, emotional_state, passed)
        violations += self._check_slang_understanding(user_message, ai_response, passed)
        violations += self._check_intent_miss(user_message, ai_response, scenario, passed)
        violations += self._check_response_length(user_message, ai_response, persona, passed)
        violations += self._check_hallucination_risk(ai_response, passed)
        violations += self._check_tourist_trap(ai_response, passed)
        violations += self._check_overload(ai_response, passed)
        violations += self._check_contextual_continuity(user_message, ai_response, context, passed)
        violations += self._check_child_safety(user_message, ai_response, passed)
        violations += self._check_cultural_accuracy(ai_response, passed)
        violations += self._check_no_response(ai_response, passed)
        violations += self._check_language_match(user_message, ai_response, passed)

        # Determine overall result
        critical = [v for v in violations if v.severity == AuditSeverity.CRITICAL]
        high = [v for v in violations if v.severity == AuditSeverity.HIGH]

        if critical:
            result = AuditResult.FAIL
            severity = AuditSeverity.CRITICAL
        elif high:
            result = AuditResult.FAIL
            severity = AuditSeverity.HIGH
        elif violations:
            result = AuditResult.WARNING
            severity = AuditSeverity.MEDIUM
        else:
            result = AuditResult.PASS
            severity = AuditSeverity.LOW

        # Build dimension scores
        dimension_scores = self._compute_dimension_scores(violations, passed)

        return AuditReport(
            session_id=session_id,
            user_message=user_message,
            detected_intent=scenario or "unknown",
            expected_behavior=self._get_expected_behavior(scenario),
            actual_response=ai_response[:500],  # truncate for report
            audit_result=result,
            severity=severity,
            violations=violations,
            passed_checks=passed,
            dimension_scores=dimension_scores,
            replayable=True,
            persona_type=persona.type.value if persona else None,
            emotional_state=emotional_state,
        )

    # ── Individual Audit Checks ────────────────────────────

    def _check_robotic_tone(self, user_msg: str, response: str, passed: list) -> list:
        violations = []
        response_lower = response.lower()

        robotic_phrases = [
            "i am an ai", "as an ai", "i'm an ai",
            "tôi là một AI", "tôi là AI",
            "i cannot provide", "i am unable to",
            "tôi không thể cung cấp",
            "please note that", "it is important to note",
            "furthermore", "additionally", "in conclusion",
            "as per your request", "regarding your query",
            "i hope this helps", "please let me know if",
            "feel free to ask",
        ]

        found = [p for p in robotic_phrases if p in response_lower]
        if found:
            violations.append(AuditViolation(
                rule="robotic_corporate_tone",
                severity=AuditSeverity.HIGH,
                reason=f"AI used robotic/corporate phrases: {found[:3]}",
                fix_suggestion="Replace with natural, conversational Vietnamese. Drop formal AI disclaimers.",
                dimension="human_naturalness",
            ))
        else:
            passed.append("no_robotic_tone")

        return violations

    def _check_corporate_language(self, response: str, passed: list) -> list:
        violations = []
        response_lower = response.lower()

        corporate_patterns = [
            "thank you for your feedback",
            "we apologize for the inconvenience",
            "our team will",
            "please contact support",
            "for more information, please",
            "kindly note",
            "as per",
            "cảm ơn bạn đã phản hồi",
            "chúng tôi xin lỗi vì sự bất tiện",
            "vui lòng liên hệ",
        ]

        found = [p for p in corporate_patterns if p in response_lower]
        if found:
            violations.append(AuditViolation(
                rule="corporate_support_language",
                severity=AuditSeverity.HIGH,
                reason=f"AI sounds like corporate support bot: {found[:2]}",
                fix_suggestion="Use natural, human language. This is a travel companion, not a support ticket system.",
                dimension="human_naturalness",
            ))
        else:
            passed.append("no_corporate_language")

        return violations

    def _check_emotional_mismatch(
        self, user_msg: str, response: str, emotional_state: str, passed: list
    ) -> list:
        violations = []
        response_lower = response.lower()
        user_lower = user_msg.lower()

        # Angry user getting dismissive response
        anger_signals = ["tức", "sao lại", "không chấp nhận", "???", "!!!", "lần cuối"]
        if any(s in user_lower for s in anger_signals):
            dismissive = ["cảm ơn bạn", "rất tiếc", "bình thường thôi"]
            if any(d in response_lower for d in dismissive):
                violations.append(AuditViolation(
                    rule="dismissive_to_angry_user",
                    severity=AuditSeverity.HIGH,
                    reason="User is angry but AI gives dismissive/formal response",
                    fix_suggestion="Acknowledge frustration first, then provide immediate solution",
                    dimension="emotional_awareness",
                ))
            else:
                passed.append("anger_handled_appropriately")

        # Exhausted user getting energetic response
        exhaustion_signals = ["mệt vl", "không đi nổi", "kiệt sức", "chỉ muốn nằm"]
        if any(s in user_lower for s in exhaustion_signals):
            energetic = ["đi tiếp", "tiếp theo", "một địa điểm nữa", "còn nhiều chỗ"]
            if any(e in response_lower for e in energetic):
                violations.append(AuditViolation(
                    rule="energetic_suggestion_to_exhausted_user",
                    severity=AuditSeverity.HIGH,
                    reason="User is exhausted but AI suggests more activities",
                    fix_suggestion="Suggest immediate rest, quiet spot, or nearby food. No more sightseeing.",
                    dimension="emotional_awareness",
                ))
            else:
                passed.append("exhaustion_recognized")

        # Excited user getting flat response
        excitement_signals = ["đỉnh quá", "wow", "đẹp quá", "thích lắm"]
        if any(s in user_lower for s in excitement_signals):
            flat_response = len(response) < 50 or not any(
                emoji in response for emoji in ["!", "✨", "🌟", "😊", "🎉"]
            )
            if flat_response:
                violations.append(AuditViolation(
                    rule="flat_response_to_excited_user",
                    severity=AuditSeverity.LOW,
                    reason="User is excited but AI response is flat/unresponsive",
                    fix_suggestion="Match user's energy with enthusiasm",
                    dimension="emotional_awareness",
                ))
            else:
                passed.append("excitement_matched")

        return violations

    def _check_slang_understanding(self, user_msg: str, response: str, passed: list) -> list:
        violations = []
        user_lower = user_msg.lower()

        # Detect if user used slang — AI should not respond formally
        slang_used = any(s in user_lower for s in [
            "vl", "vcl", "ez", "oke", "chill", "flex", "dc", "ko", "gần gần",
            "local local", "chill chill", "doi qua", "mệt vl",
        ])

        if slang_used:
            overly_formal = any(f in response.lower() for f in [
                "kính gửi", "trân trọng", "xin thưa", "theo như",
                "dear", "sincerely", "please be advised",
            ])
            if overly_formal:
                violations.append(AuditViolation(
                    rule="formal_response_to_slang_user",
                    severity=AuditSeverity.HIGH,
                    reason="User used casual slang but AI responded formally",
                    fix_suggestion="Match user's casual register. Use informal Vietnamese.",
                    dimension="slang_understanding",
                ))
            else:
                passed.append("register_matched")

        # Check if AI understood 'doi qua' / 'chang' type expressions
        if "doi qua" in user_lower or "đói quá" in user_lower:
            if not any(f in response.lower() for f in ["ăn", "quán", "food", "cơm", "bún", "hải sản"]):
                violations.append(AuditViolation(
                    rule="missed_hunger_signal",
                    severity=AuditSeverity.HIGH,
                    reason="User said they're hungry but AI didn't suggest food",
                    fix_suggestion="When user says 'đói quá', immediately suggest nearby food options",
                    dimension="slang_understanding",
                ))
            else:
                passed.append("hunger_signal_understood")

        return violations

    def _check_intent_miss(self, user_msg: str, response: str, scenario: str, passed: list) -> list:
        violations = []
        user_lower = user_msg.lower()
        response_lower = response.lower()

        intent_checks = {
            "food": (
                ["ăn", "quán", "đói", "hải sản", "cơm", "bún"],
                ["ăn", "quán", "gợi ý", "địa chỉ", "giá", "ngon"],
                "User asking about food but AI didn't provide food recommendations",
            ),
            "location": (
                ["ở đâu", "cách đây", "đường đến", "chỗ nào"],
                ["km", "phút", "đường", "hướng", "google maps", "địa chỉ"],
                "User asking for directions/location but AI didn't provide navigation help",
            ),
            "weather": (
                ["thời tiết", "mưa", "nắng", "trời"],
                ["độ", "mưa", "nắng", "thời tiết", "forecast"],
                "User asking about weather but AI didn't provide weather info",
            ),
        }

        for intent, (user_signals, response_signals, fail_reason) in intent_checks.items():
            if any(s in user_lower for s in user_signals):
                if not any(s in response_lower for s in response_signals):
                    violations.append(AuditViolation(
                        rule=f"missed_{intent}_intent",
                        severity=AuditSeverity.HIGH,
                        reason=fail_reason,
                        fix_suggestion=f"Detect {intent} intent and provide {intent} information directly",
                        dimension="intent_understanding",
                    ))
                else:
                    passed.append(f"{intent}_intent_addressed")

        return violations

    def _check_response_length(self, user_msg: str, response: str, persona, passed: list) -> list:
        violations = []

        # Very short user messages usually want short answers
        if len(user_msg) < 15:
            if len(response) > 600:
                violations.append(AuditViolation(
                    rule="response_too_long_for_short_query",
                    severity=AuditSeverity.MEDIUM,
                    reason=f"User sent {len(user_msg)} char message, AI responded with {len(response)} chars",
                    fix_suggestion="Match response length to query complexity. Short question = short answer.",
                    dimension="conversation_continuity",
                ))
            else:
                passed.append("response_length_proportionate")

        # Empty-ish response
        if len(response.strip()) < 20:
            violations.append(AuditViolation(
                rule="response_too_short",
                severity=AuditSeverity.HIGH,
                reason="AI response is too brief to be helpful",
                fix_suggestion="Provide meaningful, actionable response",
                dimension="recommendation_quality",
            ))

        return violations

    def _check_hallucination_risk(self, response: str, passed: list) -> list:
        violations = []
        response_lower = response.lower()

        # AI claiming certainty about things it can't know
        uncertain_claims = [
            "chắc chắn là", "definitely", "100% ",
            "tôi biết chắc", "guaranteed",
        ]
        context_uncertain = [
            "đang mở cửa", "hiện đang", "hiện tại đang",
        ]

        if any(uc in response_lower for uc in uncertain_claims):
            if any(cu in response_lower for cu in context_uncertain):
                violations.append(AuditViolation(
                    rule="hallucination_certainty_risk",
                    severity=AuditSeverity.HIGH,
                    reason="AI claimed certainty about real-time info it cannot verify",
                    fix_suggestion="Add qualifiers like 'thường' or 'kiểm tra trước' for real-time claims",
                    dimension="hallucination_risk",
                ))
            else:
                passed.append("certainty_appropriate")

        # Specific numbers without basis
        if re.search(r'\d{10,}', response):  # very long numbers = likely wrong
            violations.append(AuditViolation(
                rule="suspicious_specific_numbers",
                severity=AuditSeverity.MEDIUM,
                reason="AI gave very specific numbers that may be hallucinated",
                fix_suggestion="Use approximate ranges rather than exact unverifiable numbers",
                dimension="hallucination_risk",
            ))
        else:
            passed.append("numbers_reasonable")

        return violations

    def _check_tourist_trap(self, response: str, passed: list) -> list:
        violations = []
        response_lower = response.lower()

        # Known tourist-trap indicators
        tourist_trap_signals = [
            "tourist", "famous for", "world-renowned",
            "must-visit", "top-rated on tripadvisor",
            "popular with tourists",
        ]

        # Red flags in Vietnamese
        vn_trap_signals = [
            "bẫy khách du lịch", "chặt chém",
            "only for tourists", "tây hay đến",
        ]

        # We want AI to avoid explicitly recommending these
        if any(s in response_lower for s in tourist_trap_signals):
            if not any(w in response_lower for w in ["địa phương", "local", "người dân", "thật sự"]):
                violations.append(AuditViolation(
                    rule="potential_tourist_trap_recommendation",
                    severity=AuditSeverity.MEDIUM,
                    reason="AI may be recommending tourist-oriented rather than local-authentic spots",
                    fix_suggestion="Prioritize local favorites over tourist-famous spots",
                    dimension="recommendation_quality",
                ))
            else:
                passed.append("local_perspective_included")
        else:
            passed.append("no_tourist_trap_signals")

        return violations

    def _check_overload(self, response: str, passed: list) -> list:
        violations = []

        # Count bullet points / numbered items
        bullet_count = len(re.findall(r'^\s*[\-\*\d]+\.?\s+', response, re.MULTILINE))
        if bullet_count > 8:
            violations.append(AuditViolation(
                rule="choice_overload",
                severity=AuditSeverity.MEDIUM,
                reason=f"AI listed {bullet_count} options — too many choices overwhelm users",
                fix_suggestion="Limit to 2-3 best options. Make a recommendation instead of listing everything.",
                dimension="recommendation_quality",
            ))
        else:
            passed.append("option_count_appropriate")

        return violations

    def _check_contextual_continuity(
        self, user_msg: str, response: str, context: dict, passed: list
    ) -> list:
        violations = []

        # Check if AI forgot group context (7 people + 1 child)
        if context.get("group_size") and "7" not in response and "nhóm" not in response.lower():
            if any(w in user_msg.lower() for w in ["cả nhà", "cả nhóm", "7 người", "tất cả"]):
                violations.append(AuditViolation(
                    rule="forgot_group_context",
                    severity=AuditSeverity.MEDIUM,
                    reason="User mentioned group but AI gave individual-scale recommendation",
                    fix_suggestion="Always scale recommendations to group size in context",
                    dimension="context_understanding",
                ))
            else:
                passed.append("group_context_considered")

        return violations

    def _check_child_safety(self, user_msg: str, response: str, passed: list) -> list:
        violations = []
        user_lower = user_msg.lower()
        response_lower = response.lower()

        child_signals = ["bé", "con", "4 tuổi", "trẻ em", "baby", "child", "kid"]

        if any(s in user_lower for s in child_signals):
            # If user mentions child near beach, AI must address safety
            if any(b in user_lower for b in ["biển", "bơi", "tắm", "sóng"]):
                safety_words = ["an toàn", "cẩn thận", "an toan", "safe", "safety", "shallow"]
                if not any(s in response_lower for s in safety_words):
                    violations.append(AuditViolation(
                        rule="missed_child_beach_safety",
                        severity=AuditSeverity.CRITICAL,
                        reason="User mentioned child near beach/water but AI didn't address safety",
                        fix_suggestion="Always address child water safety proactively when relevant",
                        dimension="cultural_understanding",
                    ))
                else:
                    passed.append("child_safety_addressed")

        return violations

    def _check_cultural_accuracy(self, response: str, passed: list) -> list:
        violations = []
        response_lower = response.lower()

        # Check for obviously wrong cultural info
        wrong_culture = [
            ("phú yên", "phú quốc"),  # confusing islands
            ("tôm hùm sông cầu", "tôm hùm phú quốc"),  # wrong lobster origin
        ]

        for correct_mention, wrong_mention in wrong_culture:
            if correct_mention in response_lower and wrong_mention in response_lower:
                violations.append(AuditViolation(
                    rule="cultural_accuracy_error",
                    severity=AuditSeverity.HIGH,
                    reason=f"AI confused {wrong_mention} with {correct_mention}",
                    fix_suggestion="Verify geographic/cultural facts specific to Phú Yên",
                    dimension="cultural_understanding",
                ))

        return violations

    def _check_no_response(self, response: str, passed: list) -> list:
        violations = []

        non_answers = [
            "i don't know", "i'm not sure", "không biết", "không có thông tin",
            "unable to help", "cannot assist",
        ]

        if any(n in response.lower() for n in non_answers):
            violations.append(AuditViolation(
                rule="unhelpful_non_answer",
                severity=AuditSeverity.HIGH,
                reason="AI admitted it doesn't know without attempting to help",
                fix_suggestion="Always try to give partial help or refer to a reliable source",
                dimension="recommendation_quality",
            ))
        else:
            passed.append("response_is_helpful")

        return violations

    def _check_language_match(self, user_msg: str, response: str, passed: list) -> list:
        violations = []

        # Detect Vietnamese input but English-only response
        has_vietnamese = bool(re.search(
            r'[àáảãạăắằẳẵặâấầẩẫậđèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵ]',
            user_msg
        ))
        has_english_response = bool(re.search(r'\b(the|is|are|have|has|this|that|for)\b', response))
        has_vietnamese_response = bool(re.search(
            r'[àáảãạăắằẳẵặâấầẩẫậđèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵ]',
            response
        ))

        if has_vietnamese and has_english_response and not has_vietnamese_response:
            violations.append(AuditViolation(
                rule="language_mismatch",
                severity=AuditSeverity.HIGH,
                reason="User wrote in Vietnamese but AI responded in English",
                fix_suggestion="Always respond in the same language as the user",
                dimension="cultural_understanding",
            ))
        else:
            passed.append("language_matched")

        return violations

    def _get_expected_behavior(self, scenario: str) -> str:
        behaviors = {
            "food_search": "Provide 2-3 specific nearby food recommendations with names, addresses, price range",
            "location_query": "Provide navigation info with distance, time, and route options",
            "weather_check": "Give current weather context and travel impact advice",
            "nightlife": "Suggest appropriate venues with hours, atmosphere, price range",
            "recovery_needed": "Suggest quiet, nearby, low-effort options for exhausted user",
            "emergency": "Provide immediate emergency numbers and nearest help",
            "fragmented_order": "Merge fragments into coherent request and respond holistically",
        }
        return behaviors.get(scenario, "Provide helpful, contextually appropriate response")

    def _compute_dimension_scores(self, violations: list, passed: list) -> dict:
        dimensions = {
            "human_naturalness": 1.0,
            "slang_understanding": 1.0,
            "emotional_awareness": 1.0,
            "intent_understanding": 1.0,
            "recommendation_quality": 1.0,
            "cultural_understanding": 1.0,
            "hallucination_risk": 1.0,
            "conversation_continuity": 1.0,
            "context_understanding": 1.0,
        }

        severity_penalties = {
            AuditSeverity.LOW: 0.1,
            AuditSeverity.MEDIUM: 0.2,
            AuditSeverity.HIGH: 0.35,
            AuditSeverity.CRITICAL: 0.5,
        }

        for v in violations:
            dim = v.dimension
            if dim in dimensions:
                penalty = severity_penalties.get(v.severity, 0.2)
                dimensions[dim] = max(0.0, dimensions[dim] - penalty)

        return {k: round(v, 2) for k, v in dimensions.items()}
