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
        collective_state=None,
        travel_dna=None,
    ) -> LocalIntelligenceState:
        """
        Phase 7 enhancement: accepts collective_state and travel_dna
        for personalized collective intelligence insights.
        """
        text = incoming_text.lower()
        insights: list[str] = []

        # === Time-based local insights ===
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

        # === Phase 7: Collective Intelligence insights ===
        if collective_state is not None:
            # Collective mood-based routing
            if collective_state.collective_mood == "tired":
                insights.append("Nhóm đang mệt — ưu tiên phương án nhẹ, gần, ít di chuyển.")
            elif collective_state.collective_mood == "cautious":
                insights.append("Nhóm đang cẩn thận — mình sẽ chọn option đã được confirm tốt.")
            elif collective_state.energy_trend == "dipping":
                insights.append("Năng lượng nhóm đang giảm — nên giảm activity tiếp theo.")

            # Top experiences from collective feedback
            if collective_state.top_experiences:
                top = collective_state.top_experiences[0]
                insights.append(f"Top trải nghiệm tốt nhất hôm nay: {top}")

        # === Phase 7: Travel DNA personalization ===
        if travel_dna is not None:
            if travel_dna.prefers_beach >= 0.7 and any(t in text for t in ["đi đâu", "ở đâu", "gợi ý", "nên"]):
                insights.append("Bạn thường thích biển — ưu tiên bãi có sóng nhỏ, yên.")
            if travel_dna.prefers_food >= 0.7 and any(t in text for t in ["quán", "ăn", "đặc sản"]):
                insights.append("Bạn đam mê ẩm thực — mình sẽ chọn quán có món đặc trưng Phú Yên.")
            if travel_dna.prefers_slow_pace >= 0.7 and any(t in text for t in ["kế hoạch", "nên đi", "thời gian"]):
                insights.append("Bạn thích nhịp chậm — mình sẽ giữ schedule thoải mái, không gấp.")
            if travel_dna.fatigue_threshold <= 0.4 and any(t in text for t in ["sáng sớm", "5h", "dậy", "sớm"]):
                insights.append("Bạn dễ mệt — nếu phải dậy sớm, mình sẽ nhắc chuẩn bị từ tối.")

        deduped: list[str] = []
        for insight in insights:
            if insight and insight not in deduped:
                deduped.append(insight)
        return LocalIntelligenceState(insights=deduped[:2])