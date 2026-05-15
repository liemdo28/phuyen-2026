from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from app.fatigue.energy_engine import TravelEnergyState
from app.realtime.world_model import RealtimeWorldModel

# Environmental trend thresholds
_HIGH_HEAT = 0.65
_HIGH_TRAFFIC = 0.55
_HIGH_WEATHER_RISK = 0.45
_HIGH_TOURIST_DENSITY = 0.55
_HIGH_SAFETY_RISK = 0.45


@dataclass
class EnvironmentSignal:
    signal_type: str
    intensity: float
    trend: str = "stable"    # rising | falling | stable | spike
    action_required: str = "none"  # none | reroute | rebalance | reprioritize | slow_down | accelerate


@dataclass
class EnvironmentState:
    weather_evolution: float = 0.0
    sea_conditions: float = 0.5
    tourist_movement: float = 0.0
    traffic_patterns: float = 0.0
    local_event_activity: float = 0.0
    business_occupancy: float = 0.5
    reroute_needed: bool = False
    rebalance_needed: bool = False
    reprioritize_needed: bool = False
    slow_down_signal: bool = False
    accelerate_signal: bool = False
    signals: list[EnvironmentSignal] = field(default_factory=list)
    alerts: list[str] = field(default_factory=list)
    environment_summary: str = ""


class EnvironmentMonitor:
    """
    Continuously monitors environmental conditions and dynamically adjusts:
    rerouting, rebalancing, reprioritizing, and pacing based on real-time
    weather, traffic, sea conditions, tourist movement, and event activity.
    """

    def assess(
        self,
        world: RealtimeWorldModel,
        now: datetime,
        energy: TravelEnergyState,
    ) -> EnvironmentState:
        state = EnvironmentState()
        hour = now.hour

        # --- Weather evolution ---
        state.weather_evolution = world.weather_risk
        if world.weather_risk > _HIGH_WEATHER_RISK:
            state.signals.append(EnvironmentSignal(
                signal_type="weather",
                intensity=world.weather_risk,
                trend="spike" if world.weather_risk > 0.65 else "rising",
                action_required="reprioritize",
            ))
            state.reprioritize_needed = True
            state.alerts.append(
                "Thời tiết đang xấu đi. Gợi ý ưu tiên các hoạt động trong nhà hoặc có mái che."
            )

        # --- Sea conditions (beach quality as proxy) ---
        state.sea_conditions = world.beach_quality
        if world.beach_quality < 0.3:
            state.signals.append(EnvironmentSignal(
                signal_type="sea",
                intensity=1.0 - world.beach_quality,
                trend="falling",
                action_required="reprioritize",
            ))
            state.alerts.append("Điều kiện biển không tốt lúc này. Có thể chọn địa điểm khác hoặc đợi chiều mát hơn.")

        # --- Tourist movement / density ---
        state.tourist_movement = world.tourist_density
        if world.tourist_density > _HIGH_TOURIST_DENSITY:
            state.signals.append(EnvironmentSignal(
                signal_type="tourist_density",
                intensity=world.tourist_density,
                trend="rising" if "evening_peak_window" in world.signals else "stable",
                action_required="reroute",
            ))
            state.reroute_needed = True
            state.alerts.append(
                "Khu vực này đang đông khách. Mình có thể gợi ý điểm tương tự nhưng ít người hơn."
            )

        # --- Traffic patterns ---
        state.traffic_patterns = world.traffic_pressure
        if world.traffic_pressure > _HIGH_TRAFFIC:
            state.signals.append(EnvironmentSignal(
                signal_type="traffic",
                intensity=world.traffic_pressure,
                trend="spike" if "evening_peak_window" in world.signals else "rising",
                action_required="slow_down",
            ))
            state.slow_down_signal = True
            state.alerts.append(
                "Giao thông đang tắc nghẽn. Nên nghỉ tại chỗ thêm 30–45 phút hoặc chọn tuyến đường khác."
            )

        # --- Local event activity ---
        state.local_event_activity = world.event_intensity
        if world.event_intensity > 0.4:
            state.signals.append(EnvironmentSignal(
                signal_type="local_events",
                intensity=world.event_intensity,
                trend="rising",
                action_required="rebalance",
            ))
            state.rebalance_needed = True

        # --- Heat / energy compound ---
        if world.heat_pressure > _HIGH_HEAT and energy.physical_energy < 0.45:
            state.slow_down_signal = True
            state.signals.append(EnvironmentSignal(
                signal_type="heat_energy_compound",
                intensity=world.heat_pressure,
                trend="stable",
                action_required="slow_down",
            ))
            state.alerts.append(
                "Trời nắng nóng và bạn đang khá mệt. Đây là thời điểm tốt để tìm nơi mát và nghỉ ngơi."
            )

        # --- Low risk window (accelerate opportunity) ---
        is_optimal_window = (
            "local_breakfast_window" in world.signals
            or (6 <= hour <= 9)
            or (16 <= hour <= 18 and world.traffic_pressure < 0.3)
        )
        if is_optimal_window and energy.exploration_readiness > 0.5:
            state.accelerate_signal = True
            state.signals.append(EnvironmentSignal(
                signal_type="optimal_window",
                intensity=energy.exploration_readiness,
                trend="rising",
                action_required="accelerate",
            ))

        # --- Business occupancy estimate ---
        if "midday_heat_window" in world.signals:
            state.business_occupancy = min(1.0, 0.5 + world.tourist_density * 0.4)
        elif "evening_peak_window" in world.signals:
            state.business_occupancy = min(1.0, 0.6 + world.tourist_density * 0.35)
        else:
            state.business_occupancy = max(0.1, 0.4 - world.tourist_density * 0.2)

        # --- Environment summary ---
        state.environment_summary = self._build_summary(state, world)
        return state

    def _build_summary(self, state: EnvironmentState, world: RealtimeWorldModel) -> str:
        parts: list[str] = []
        if state.reroute_needed:
            parts.append("khu vực đông đúc")
        if state.slow_down_signal:
            parts.append("nên di chuyển chậm lại")
        if state.reprioritize_needed:
            parts.append("ưu tiên lại lịch trình")
        if state.accelerate_signal:
            parts.append("đây là khung giờ lý tưởng để khám phá")
        if not parts:
            return "Môi trường ổn định — lịch trình hiện tại phù hợp."
        return "Môi trường: " + ", ".join(parts) + "."
