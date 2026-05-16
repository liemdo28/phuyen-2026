"""
Sarcasm Engine — Detects and generates sarcastic, passive-aggressive,
and ironic messages to test AI emotional intelligence.
"""

import random
from typing import List, Tuple
from dataclasses import dataclass
from enum import Enum


class SarcasmType(Enum):
    MILD_IRONY = "mild_irony"
    PASSIVE_AGGRESSIVE = "passive_aggressive"
    BACKHANDED_COMPLIMENT = "backhanded_compliment"
    DRAMATIC_OVERREACTION = "dramatic_overreaction"
    FAKE_ENTHUSIASM = "fake_enthusiasm"
    RHETORICAL_COMPLAINT = "rhetorical_complaint"
    UNDERSTATED_DISASTER = "understated_disaster"


@dataclass
class SarcasmCase:
    sarcasm_type: SarcasmType
    message: str
    literal_meaning: str
    actual_intent: str
    expected_ai_response: str
    wrong_ai_response: str  # What a bad AI would do


SARCASM_CASES = [
    SarcasmCase(
        sarcasm_type=SarcasmType.FAKE_ENTHUSIASM,
        message="Ừ đúng rồi, quán đó tuyệt vời lắm 🙄",
        literal_meaning="Agreement",
        actual_intent="Complaining the restaurant was bad",
        expected_ai_response="Acknowledge the dissatisfaction, offer alternatives, ask what went wrong",
        wrong_ai_response="Great, glad you liked it! Enjoy your meal!",
    ),
    SarcasmCase(
        sarcasm_type=SarcasmType.PASSIVE_AGGRESSIVE,
        message="Không sao, tôi sẽ tự tìm vậy",
        literal_meaning="User is fine finding it themselves",
        actual_intent="User is frustrated and giving up on the AI",
        expected_ai_response="Apologize and immediately help better, ask what they're looking for",
        wrong_ai_response="Great! Good luck!",
    ),
    SarcasmCase(
        sarcasm_type=SarcasmType.BACKHANDED_COMPLIMENT,
        message="AI này thông minh thật, gợi ý đúng chỗ tourist trap",
        literal_meaning="Compliment on intelligence",
        actual_intent="Criticizing that AI recommended a tourist trap",
        expected_ai_response="Apologize for the tourist trap recommendation, offer genuine local alternatives",
        wrong_ai_response="Thank you! Here are more recommendations...",
    ),
    SarcasmCase(
        sarcasm_type=SarcasmType.DRAMATIC_OVERREACTION,
        message="Trời ơi xong rồi, hết hy vọng rồi",
        literal_meaning="Catastrophic situation",
        actual_intent="Minor inconvenience, user is dramatic",
        expected_ai_response="Gently acknowledge, ask what happened, offer to help",
        wrong_ai_response="That sounds terrible! Emergency services are...",
    ),
    SarcasmCase(
        sarcasm_type=SarcasmType.MILD_IRONY,
        message="Hay thật đấy, mưa đúng lúc ra biển",
        literal_meaning="Great timing",
        actual_intent="Frustrated about rain ruining beach plans",
        expected_ai_response="Sympathize with rain timing, offer indoor alternatives",
        wrong_ai_response="I'm glad you're having a great time!",
    ),
    SarcasmCase(
        sarcasm_type=SarcasmType.RHETORICAL_COMPLAINT,
        message="Sao mà đông thế này hả trời",
        literal_meaning="Question to the sky about crowds",
        actual_intent="Complaining about crowded location, wants alternative",
        expected_ai_response="Suggest less crowded alternatives or timing advice",
        wrong_ai_response="I don't know why it's crowded.",
    ),
    SarcasmCase(
        sarcasm_type=SarcasmType.UNDERSTATED_DISASTER,
        message="Ừ thì đang bị lạc một tí thôi",
        literal_meaning="Slightly lost",
        actual_intent="User is actually quite lost and stressed",
        expected_ai_response="Take it seriously, ask for current location, provide navigation help immediately",
        wrong_ai_response="No problem, just follow your GPS!",
    ),
    SarcasmCase(
        sarcasm_type=SarcasmType.FAKE_ENTHUSIASM,
        message="Wow AI giỏi quá, gợi ý chỗ đóng cửa 👏",
        literal_meaning="Praising AI",
        actual_intent="Sarcastic criticism — AI recommended a closed place",
        expected_ai_response="Apologize sincerely, give verified open alternatives immediately",
        wrong_ai_response="Thank you! I try my best!",
    ),
    SarcasmCase(
        sarcasm_type=SarcasmType.PASSIVE_AGGRESSIVE,
        message="Thôi được, dù sao cũng không tệ hơn lần trước",
        literal_meaning="Mild approval",
        actual_intent="Backhanded acceptance after previously bad recommendation",
        expected_ai_response="Acknowledge past failure, ensure this recommendation is genuinely better",
        wrong_ai_response="Great! I'm glad you like it!",
    ),
    SarcasmCase(
        sarcasm_type=SarcasmType.RHETORICAL_COMPLAINT,
        message="Bình thường thôi, chỉ bị chặt chém 200k có vậy",
        literal_meaning="No big deal",
        actual_intent="Actually very upset about being overcharged",
        expected_ai_response="Validate frustration, explain how to avoid tourist traps, suggest fair-priced alternatives",
        wrong_ai_response="That doesn't sound too bad!",
    ),
]


class SarcasmEngine:
    """Generates and detects sarcastic messages for QA testing."""

    def get_random_case(self) -> SarcasmCase:
        return random.choice(SARCASM_CASES)

    def get_cases_by_type(self, sarcasm_type: SarcasmType) -> List[SarcasmCase]:
        return [c for c in SARCASM_CASES if c.sarcasm_type == sarcasm_type]

    def generate_sarcastic_message(self, base_complaint: str) -> str:
        """Convert a complaint into a sarcastic version."""
        patterns = [
            lambda t: f"Ừ đúng rồi, {t} 🙄",
            lambda t: f"Hay thật đấy, {t}",
            lambda t: f"Tuyệt vời, {t} (không)",
            lambda t: f"Wow, {t} — thật ấn tượng",
            lambda t: f"Chắc chắn rồi, {t}",
            lambda t: f"{t}... thật sự đỉnh cao",
            lambda t: f"Không ngờ, {t} luôn",
        ]
        pattern = random.choice(patterns)
        return pattern(base_complaint)

    def detect_sarcasm(self, message: str) -> Tuple[bool, float, SarcasmType]:
        """Detect if a message is sarcastic and return type + confidence."""
        msg_lower = message.lower()
        score = 0.0
        detected_type = SarcasmType.MILD_IRONY

        # Sarcasm markers
        sarcasm_signals = {
            "🙄": (0.8, SarcasmType.FAKE_ENTHUSIASM),
            "hay thật đấy": (0.7, SarcasmType.BACKHANDED_COMPLIMENT),
            "tuyệt vời lắm": (0.5, SarcasmType.FAKE_ENTHUSIASM),
            "thông minh thật": (0.7, SarcasmType.BACKHANDED_COMPLIMENT),
            "không sao": (0.4, SarcasmType.PASSIVE_AGGRESSIVE),
            "tự tìm vậy": (0.6, SarcasmType.PASSIVE_AGGRESSIVE),
            "dù sao cũng": (0.5, SarcasmType.PASSIVE_AGGRESSIVE),
            "thật ấn tượng": (0.7, SarcasmType.BACKHANDED_COMPLIMENT),
            "(không)": (0.9, SarcasmType.MILD_IRONY),
            "chỉ... có vậy": (0.6, SarcasmType.UNDERSTATED_DISASTER),
            "một tí thôi": (0.4, SarcasmType.UNDERSTATED_DISASTER),
            "bình thường thôi": (0.5, SarcasmType.UNDERSTATED_DISASTER),
        }

        for signal, (weight, s_type) in sarcasm_signals.items():
            if signal in msg_lower or signal in message:
                score = max(score, weight)
                detected_type = s_type

        # Context-based detection
        # Positive words followed by negative context
        pos_then_neg = [
            ("tuyệt vời", "tourist trap"),
            ("hay", "bị chặt chém"),
            ("giỏi", "đóng cửa"),
            ("đúng rồi", "sai"),
        ]
        for pos, neg in pos_then_neg:
            if pos in msg_lower and neg in msg_lower:
                score = max(score, 0.8)
                detected_type = SarcasmType.BACKHANDED_COMPLIMENT

        is_sarcastic = score > 0.4
        return is_sarcastic, score, detected_type

    def audit_sarcasm_response(self, case: SarcasmCase, ai_response: str) -> dict:
        """Check if AI correctly interpreted sarcastic message."""
        violations = []
        passed = []

        response_lower = ai_response.lower()

        # Check if AI fell for literal meaning
        wrong_patterns = case.wrong_ai_response.lower().split()
        wrong_key_words = [w for w in wrong_patterns if len(w) > 4]

        literal_trap_count = sum(
            1 for word in wrong_key_words if word in response_lower
        )
        if literal_trap_count > len(wrong_key_words) * 0.5:
            violations.append({
                "rule": "ai_took_sarcasm_literally",
                "severity": "HIGH",
                "detail": f"AI interpreted sarcasm as literal. Type: {case.sarcasm_type.value}",
                "message": case.message,
                "actual_intent": case.actual_intent,
            })
        else:
            passed.append("sarcasm_detected_correctly")

        # Check for empathy
        empathy_words = [
            "xin lỗi", "hiểu", "sorry", "tiếc", "thay thế", "thay vì",
            "bù đắp", "thử chỗ khác", "gợi ý khác",
        ]
        if not any(e in response_lower for e in empathy_words):
            violations.append({
                "rule": "no_empathy_for_sarcastic_user",
                "severity": "MEDIUM",
                "detail": "AI didn't show empathy when user was being sarcastic (disguised complaint)",
            })
        else:
            passed.append("empathy_shown")

        return {
            "sarcasm_type": case.sarcasm_type.value,
            "message": case.message,
            "actual_intent": case.actual_intent,
            "violations": violations,
            "passed": passed,
            "sarcasm_score": max(0.0, 1.0 - len(violations) * 0.35),
        }
