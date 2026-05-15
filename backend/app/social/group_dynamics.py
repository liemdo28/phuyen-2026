from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class GroupDynamicsState:
    complexity: float = 0.0
    child_present: bool = False
    family_mode: bool = False
    needs_balance: bool = False
    signals: list[str] = field(default_factory=list)


class GroupDynamicsEngine:
    def assess(self, incoming_text: str) -> GroupDynamicsState:
        text = incoming_text.lower()
        state = GroupDynamicsState()
        if any(token in text for token in ["bé", "trẻ", "em bé", "con nít"]):
            state.child_present = True
            state.family_mode = True
            state.complexity += 0.24
            state.signals.append("child_present")
        if any(token in text for token in ["cả nhà", "gia đình", "bố mẹ", "ông bà", "couple", "vợ", "chồng"]):
            state.family_mode = True
            state.complexity += 0.18
            state.signals.append("family_group")
        if any(token in text for token in ["cả nhóm", "mọi người", "tụi mình", "team", "nhóm"]):
            state.needs_balance = True
            state.complexity += 0.18
            state.signals.append("group_balance")
        state.complexity = min(state.complexity, 1.0)
        return state
