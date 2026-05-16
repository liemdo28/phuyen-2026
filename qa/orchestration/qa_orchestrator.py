"""
QAOrchestrator — single-batch QA runner.

Picks random Vietnamese test messages from a curated scenario pool,
sends each through the AI handler, audits the response, and returns
a SessionAggregator that run_qa.py can report on.
"""

from __future__ import annotations

import random
import uuid
from typing import Callable

from ..audit.audit_engine import AuditEngine
from ..scoring.scoring_engine import SessionAggregator


# ── Scenario pool ─────────────────────────────────────────────────────────────
# (user_message, category)
_SCENARIOS: list[tuple[str, str]] = [
    # Fatigue
    ("mệt quá không muốn đi đâu cả", "fatigue"),
    ("met xiu roi nghi thoi", "fatigue"),
    ("ơi mệt lắm chân không bước nổi", "fatigue"),
    ("kiệt sức rồi cho nghỉ tí", "fatigue"),
    ("mệt muốn chết đi đâu cũng lười", "fatigue"),
    # Food / hunger
    ("muốn ăn hải sản tươi ở đây", "food"),
    ("doi qua an gi day", "food"),
    ("t thèm bánh căn ơi", "food"),
    ("ăn gì ngon đây", "food"),
    ("có chỗ ăn chè ngon không", "food"),
    ("muốn ăn cơm gà", "food"),
    ("bun ca o day ngon khong", "food"),
    ("tìm quán ăn gần đây", "food"),
    # Movement resistance
    ("gần thôi nha đừng xa", "movement"),
    ("lười đi xa lắm", "movement"),
    ("gan thoi ngai di", "movement"),
    ("không muốn đi xe lâu", "movement"),
    ("đi bộ thôi không muốn lấy xe", "movement"),
    # Chill
    ("kiếm chỗ chill chill đi", "chill"),
    ("muốn đi cafe gì đó ngắm biển", "chill"),
    ("tìm chỗ view đẹp chụp hình", "chill"),
    ("kiem cho ngoi mat me", "chill"),
    ("cần chỗ ngồi thư giãn không ồn", "chill"),
    # Weather / environment
    ("trời nóng quá làm gì bây giờ", "weather"),
    ("trời mưa thì đi đâu được", "weather"),
    ("nắng gắt quá vào trong không", "weather"),
    # Location / nearby
    ("ở đây có gì hay", "location"),
    ("chỗ nào gần đây ngon", "location"),
    ("quanh khu này có gì vui không", "location"),
    # Evening / nightlife
    ("tối nay đi đâu", "nightlife"),
    ("đi nhậu đi mọi người", "nightlife"),
    ("toi nay co gi vui khong", "nightlife"),
    ("muốn nhậu tối nay chỗ nào", "nightlife"),
    # Child safety
    ("bé có thể xuống biển không", "child_safety"),
    ("sóng có to không cho bé xuống được không", "child_safety"),
    ("có sứa ở bãi biển không", "child_safety"),
    ("bé 4 tuổi tắm biển được không", "child_safety"),
    # Social group
    ("đi cả gia đình 5 người", "social"),
    ("cả nhóm 8 người cần chỗ rộng", "social"),
    ("có chỗ đủ chỗ ngồi cho nhóm không", "social"),
    # No accent / typo
    ("co cho nao an ngon khong", "no_accent"),
    ("di bien duoc khong", "no_accent"),
    ("thoi tiet hom nay the nao", "no_accent"),
    ("tim cho nghi mat", "no_accent"),
    # Sarcasm / indirect
    ("ừ đúng rồi biết rồi", "sarcasm"),
    ("thôi kệ đi đâu cũng được", "sarcasm"),
    ("ờ thì cũng được", "sarcasm"),
    # Fragmented / short
    ("đi", "fragmented"),
    ("ăn gì", "fragmented"),
    ("hmm", "fragmented"),
    ("ok", "fragmented"),
    ("?", "fragmented"),
    # Expenses / money
    ("ăn hết 150k", "expense"),
    ("tiêu hôm nay bao nhiêu", "expense"),
    ("đổ xăng 80k", "expense"),
    ("cafe 2 ly 60k", "expense"),
    # General travel
    ("lịch trình hôm nay thế nào", "travel"),
    ("đi Gành Đá Đĩa lúc nào tốt nhất", "travel"),
    ("Bãi Xép cách đây bao xa", "travel"),
    ("mấy giờ thì mặt trời lặn", "travel"),
    ("có cần đặt trước không", "travel"),
    # Regional slang
    ("chèn ơi nóng ghê", "regional"),
    ("ăn sáng rồi đi mô", "regional"),
    ("hết hồn sóng to vậy", "regional"),
    # Memory / continuity
    ("hồi nãy mình ăn rồi giờ làm gì", "memory"),
    ("sáng đã đi Gành rồi chiều đi đâu", "memory"),
    ("bé đói rồi", "memory"),
]


class QAOrchestrator:
    """Run a single QA batch: sample N sessions → audit → return aggregator."""

    def __init__(self) -> None:
        self.audit_engine = AuditEngine()

    def run_batch(
        self,
        ai_handler: Callable[[str], str],
        num_sessions: int = 20,
        verbose: bool = False,
    ) -> SessionAggregator:
        aggregator = SessionAggregator()
        pool = list(_SCENARIOS)
        random.shuffle(pool)
        selected = pool[:num_sessions]

        for user_message, category in selected:
            session_id = uuid.uuid4().hex[:8]
            try:
                ai_response = ai_handler(user_message)
            except Exception as exc:
                ai_response = f"[ERROR: {exc}]"

            report = self.audit_engine.audit(
                session_id=session_id,
                user_message=user_message,
                ai_response=ai_response,
                scenario=category,
                context={"category": category},
            )
            aggregator.add_result(report)

            if verbose:
                status = "✅ PASS" if not report.violations else f"❌ {len(report.violations)} violations"
                print(f"  [{category}] {user_message[:40]!r:42s} → {status}")
                for v in report.violations:
                    print(f"      ⚠️  {v.rule}: {v.reason[:60]}")

        return aggregator
