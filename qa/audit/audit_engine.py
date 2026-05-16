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
        # Mi persona checks
        violations += self._check_mi_identity(ai_response, passed)
        violations += self._check_pronoun_consistency(user_message, ai_response, passed)
        violations += self._check_emotional_warmth(user_message, ai_response, passed)
        violations += self._check_mien_tay_understanding(user_message, ai_response, passed)

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
            "tôi là một ai", "tôi là ai",
            "i cannot provide", "i am unable to",
            "tôi không thể cung cấp",
            "please note that", "it is important to note",
            "furthermore,", "in conclusion,",
            "as per your request", "regarding your query",
            "i hope this helps", "please let me know if",
            "feel free to ask", "feel free to reach",
            "certainly!", "of course!", "i'd be happy to",
            "is there anything else", "anything else i can help",
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

        # Phrases that LOOK like weather/location/food but are NOT queries
        false_positive_exclusions = {
            "weather": [
                "trời ơi", "ôi trời", "trời đất", "thôi chết", "ối dồi",
                "trời xong rồi", "hết hy vọng",
                "mặt trời lặn",   # sunset = timing, not weather
                "mặt trời mọc",
                "đông quá trời",  # "crowded" not "cold/winter"
                "sao mà đông",    # same — crowded
            ],
            "food": ["ăn năn", "ăn mừng", "ăn hiếp"],
        }

        intent_checks = {
            "food": (
                ["ăn gì", "quán", "đói", "hải sản", "cơm", "bún", "đồ ăn",
                 "doi qua", "an gi", "muon an"],
                ["ăn", "quán", "gợi ý", "địa chỉ", "giá", "ngon", "món", "cơm", "bún"],
                "User asking about food but AI didn't provide food recommendations",
            ),
            "location": (
                ["ở đâu", "cách đây", "đường đến", "chỗ nào cụ thể"],
                ["km", "phút", "đường", "hướng", "google maps", "địa chỉ"],
                "User asking for directions/location but AI didn't provide navigation help",
            ),
            "weather": (
                ["thời tiết hôm nay", "trời có mưa không", "dự báo thời tiết", "nhiệt độ",
                 "trời mưa rồi", "mưa rồi", "troi mua"],
                ["mưa", "nắng", "thời tiết", "forecast", "trong nhà", "trú mưa", "indoor",
                 "bảo tàng", "trung tâm thương mại", "mall", "quán"],
                "User mentioned rain/weather but AI didn't acknowledge weather or suggest alternatives",
            ),
        }

        for intent, (user_signals, response_signals, fail_reason) in intent_checks.items():
            exclusions = false_positive_exclusions.get(intent, [])
            is_excluded = any(exc in user_lower for exc in exclusions)
            if not is_excluded and any(s in user_lower for s in user_signals):
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
            if any(b in user_lower for b in ["biển", "bơi", "tắm", "sóng", "sứa", "nước"]):
                safety_words = [
                    "an toàn", "cẩn thận", "an toan", "safe", "safety", "shallow",
                    "nước nông", "sóng nhỏ", "áo phao", "nguy hiểm", "cờ đỏ",
                    "không tắm", "tránh", "phao", "chú ý",
                ]
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

    def _check_mi_identity(self, response: str, passed: list) -> list:
        """Mi must never reveal she's an AI or sound robotic/corporate."""
        violations = []
        response_lower = response.lower()

        ai_identity_phrases = [
            "tôi là ai", "tôi là một ai", "i am an ai", "as an ai",
            "language model", "large language model", "llm",
            "được lập trình", "được thiết kế để", "hệ thống ai",
            "trợ lý ảo", "trợ lý ai", "ai assistant",
        ]
        found = [p for p in ai_identity_phrases if p in response_lower]
        if found:
            violations.append(AuditViolation(
                rule="mi_broke_persona",
                severity=AuditSeverity.CRITICAL,
                reason=f"Mi revealed AI identity: {found[:2]}",
                fix_suggestion="Mi is a human companion. Never break persona or admit to being AI.",
                dimension="human_naturalness",
            ))
        else:
            passed.append("mi_persona_maintained")
        return violations

    def _check_pronoun_consistency(self, user_msg: str, response: str, passed: list) -> list:
        """Mi should use correct pronouns based on what user signals."""
        violations = []
        user_lower = user_msg.lower()
        response_lower = response.lower()

        # User signals older-person relationship → Mi should use "em"
        older_signals = [
            r'\banh\b', r'\bchị\b', r'\bchú\b', r'\bcô\b', r'\bdì\b',
            r'\bbác\b', r'\bông\b', r'\bbà\b',
        ]
        user_signals_elder = any(re.search(p, user_lower) for p in older_signals)
        if user_signals_elder:
            uses_em = "em" in response_lower
            uses_ban = re.search(r'\bbạn\b', response_lower)
            # "bạn" when user signals elder is wrong pronoun usage
            if uses_ban and not uses_em:
                violations.append(AuditViolation(
                    rule="wrong_pronoun_with_elder",
                    severity=AuditSeverity.MEDIUM,
                    reason="User signaled older relationship (anh/chị/chú/cô) but Mi used 'bạn' instead of 'em'",
                    fix_suggestion="When user uses anh/chị/chú/cô, Mi should use 'em' to refer to herself",
                    dimension="human_naturalness",
                ))
            else:
                passed.append("elder_pronoun_correct")

        # User uses peer/Gen Z signals → Mi should NOT be overly formal
        peer_signals = ["mày", "tao", "bro", "ní", "tụi mày", "tụi tao"]
        user_signals_peer = any(s in user_lower for s in peer_signals)
        if user_signals_peer:
            formal_phrases = ["kính gửi", "xin thưa", "trân trọng", "thưa bạn"]
            if any(f in response_lower for f in formal_phrases):
                violations.append(AuditViolation(
                    rule="overly_formal_with_peer",
                    severity=AuditSeverity.HIGH,
                    reason="User used peer-level pronouns (mày/tao/bro/ní) but Mi responded formally",
                    fix_suggestion="Match peer energy — use tui/mình, casual tone",
                    dimension="human_naturalness",
                ))
            else:
                passed.append("peer_register_matched")

        return violations

    def _check_emotional_warmth(self, user_msg: str, response: str, passed: list) -> list:
        """Mi should be warm and emotionally supportive for lonely/sad users."""
        violations = []
        user_lower = user_msg.lower()
        response_lower = response.lower()

        lonely_signals = ["chán", "buồn", "cô đơn", "không ai", "nhớ nhà", "chan ghe", "buon qua"]
        if any(s in user_lower for s in lonely_signals):
            # Response should show empathy before pushing recommendations
            empathy_words = [
                "hiểu", "thông cảm", "ừ", "vậy à", "nghe", "cảm giác", "nhẹ",
                "thôi nha", "đi nhẹ", "chill", "không sao",
            ]
            has_empathy = any(w in response_lower for w in empathy_words)
            # Pushes hard recommendations without empathy first
            hard_push = response_lower.count("nên đi") + response_lower.count("phải đến") >= 2
            if not has_empathy or hard_push:
                violations.append(AuditViolation(
                    rule="missing_emotional_warmth_for_lonely_user",
                    severity=AuditSeverity.HIGH,
                    reason="User expressed loneliness/sadness but Mi skipped empathy and pushed recommendations",
                    fix_suggestion="Acknowledge the emotion first ('Chán thì mình đi nhẹ nhẹ thôi nha...'), then gently suggest",
                    dimension="emotional_awareness",
                ))
            else:
                passed.append("emotional_warmth_present")

        return violations

    def _check_mien_tay_understanding(self, user_msg: str, response: str, passed: list) -> list:
        """Mi should understand and respond naturally to Mekong Delta speech."""
        violations = []
        user_lower = user_msg.lower()
        response_lower = response.lower()

        mien_tay_signals = [
            "ní", "hổng", "hông", "nhen", "nghen", "dữ thần", "quá trời",
            "chèn ơi", "mà nghen", "vậy nha", "đi ní", "ăn ní",
        ]
        uses_mien_tay = any(s in user_lower for s in mien_tay_signals)

        if uses_mien_tay:
            # Response should not be robotic or ignore the regional warmth
            cold_indicators = [
                "furthermore", "please note", "i recommend", "i suggest",
                "certainly", "of course", "i'd be happy",
            ]
            is_cold = any(c in response_lower for c in cold_indicators)
            # Also check response length — miền Tây users get short warm replies
            too_long = len(response) > 400
            if is_cold:
                violations.append(AuditViolation(
                    rule="cold_response_to_mien_tay_user",
                    severity=AuditSeverity.HIGH,
                    reason="User used Mekong Delta dialect but Mi responded with cold/corporate language",
                    fix_suggestion="Miền Tây users need warm, soft, natural Southern tone. Use 'nha/nhen/nghen'.",
                    dimension="human_naturalness",
                ))
            elif too_long:
                violations.append(AuditViolation(
                    rule="response_too_long_for_casual_mien_tay",
                    severity=AuditSeverity.LOW,
                    reason="Miền Tây users tend to chat casually — response is too long/formal",
                    fix_suggestion="Keep it short, warm, and natural like a friend chatting",
                    dimension="human_naturalness",
                ))
            else:
                passed.append("mien_tay_handled_warmly")

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
