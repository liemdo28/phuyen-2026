from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from app.behavior.profile_engine import TravelBehaviorProfile
from app.realtime.world_model import RealtimeWorldModel


@dataclass
class LocalIntelligenceState:
    insights: list[str] = field(default_factory=list)


class LocalIntelligenceEngine:
    def assess(
        self,
        incoming_text: str,
        now: datetime,
        world: RealtimeWorldModel,
        profile: TravelBehaviorProfile,
    ) -> LocalIntelligenceState:
        text = incoming_text.lower()
        insights: list[str] = []

        if any(token in text for token in ["ăn", "quán", "hải sản"]) and 6 <= now.hour <= 9:
            insights.append("Khung giờ này hợp ăn sáng kiểu local hơn, quán lên món nhanh và đỡ đông hơn buổi trưa.")
        if any(token in text for token in ["ăn", "quán", "nhà hàng", "hải sản"]) and 17 <= now.hour <= 19:
            insights.append("Khung này bắt đầu đông dần, mình sẽ ưu tiên 1-2 chỗ gần và vào được nhanh để đỡ mất decision energy.")
        if any(token in text for token in ["hải sản", "seafood"]) and 16 <= now.hour <= 19:
            insights.append("Khung này hợp seafood hơn vì quán bắt đầu đủ món và không bị muộn như tối khuya.")
        if any(token in text for token in ["cafe", "cà phê"]) and profile.crowd_tolerance < 0.5:
            insights.append("Nếu muốn yên hơn, mình sẽ ưu tiên cafe sau giờ cao điểm hoặc né các khung đông check-in.")
        if any(token in text for token in ["sunset", "hoàng hôn", "ảnh", "view"]) and 15 <= now.hour <= 18:
            insights.append("Đây là khung đẹp để ngắm biển hoặc chụp ảnh, nên đi sớm hơn giờ đông khoảng 30-45 phút.")
        if world.tourist_density >= 0.4:
            insights.append("Mình sẽ nghiêng về chỗ local hoặc khung giờ lệch peak để trải nghiệm đỡ touristy hơn.")

        deduped: list[str] = []
        for insight in insights:
            if insight not in deduped:
                deduped.append(insight)
        return LocalIntelligenceState(insights=deduped[:2])
