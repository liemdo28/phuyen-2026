from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")

TRIP_START_DATE = datetime(2026, 5, 23, tzinfo=VN_TZ).date()

TRIP_DAYS: dict[int, dict] = {
    1: {
        "date": "23/05 (T7)",
        "theme": "Xuất phát → Đến Tuy Hòa",
        "is_travel_day": True,
        "morning": "Khởi hành từ TP.HCM (5h–6h sáng), ăn sáng dọc QL1A",
        "afternoon": "Check-in Tuy Hòa (14h), tắm biển nhẹ bãi biển Tuy Hòa",
        "evening": "Dạo phố Trần Phú, ăn hải sản: bún cá ngừ, gỏi cá mai",
        "key_locations": ["Tuy Hòa", "Bãi biển Tuy Hòa", "Phố Trần Phú"],
        "food_highlights": ["Bún cá ngừ", "Gỏi cá mai", "Bánh tráng nướng đường phố"],
    },
    2: {
        "date": "24/05 (CN)",
        "theme": "Gành Đá Đĩa + Vịnh Hòa",
        "morning": "Gành Đá Đĩa (7h–9h, xuất phát 5h30), Hòn Yến (san hô đẹp tháng 5)",
        "afternoon": "Vịnh Hòa — bãi biển ít người, nghỉ trưa",
        "evening": "Hải sản Sông Cầu: tôm hùm bông, mực nướng, sò huyết Ô Loan",
        "key_locations": ["Gành Đá Đĩa", "Hòn Yến", "Vịnh Hòa", "Sông Cầu"],
        "food_highlights": ["Sò huyết Ô Loan", "Cá ngừ đại dương câu tay", "Tôm hùm bông"],
        "child_note": "Đi giày đế cao su cho bé ở Gành Đá Đĩa, tránh đứng sát mép đá",
        "early_start": True,
    },
    3: {
        "date": "25/05 (T2)",
        "theme": "Mũi Điện + Bãi Xép",
        "morning": "Mũi Điện — bình minh cực Đông VN (xuất phát 4h30), Bãi Môn",
        "afternoon": "Bãi Xép — bãi trong phim Hoa Vàng Trên Cỏ Xanh (sóng nhỏ, an toàn bé)",
        "evening": "Tuy Hòa thư giãn: bún sứa, bánh hỏi, mua đặc sản",
        "key_locations": ["Mũi Điện", "Bãi Môn", "Bãi Xép", "Tuy Hòa"],
        "food_highlights": ["Bún sứa Phú Yên", "Bánh hỏi lòng heo"],
        "early_start": True,
        "child_note": "Mặc áo ấm buổi sáng tại Mũi Điện (lạnh), Bãi Xép sóng nhỏ an toàn cho bé",
    },
    4: {
        "date": "26/05 (T3)",
        "theme": "Đầm Ô Loan + Tháp Nhạn + Thư giãn",
        "morning": "Tháp Nhạn (7h–9h, view đẹp), Đầm Ô Loan (kayak ~50–100k/người)",
        "afternoon": "Tự do — hồ bơi khách sạn, Chợ Tuy Hòa mua đặc sản",
        "evening": "Tiệc hải sản đặc biệt: cá ngừ đại dương câu tay (sashimi/nướng/kho)",
        "key_locations": ["Đầm Ô Loan", "Tháp Nhạn", "Chợ Tuy Hòa"],
        "food_highlights": ["Cá ngừ đại dương câu tay", "Chè Phú Yên", "Cơm hến"],
        "relaxed_day": True,
        "child_note": "Ngày thư giãn phù hợp với bé — hồ bơi, mang phao bơi cho bé",
    },
    5: {
        "date": "27/05 (T4)",
        "theme": "Về nhà",
        "is_return_day": True,
        "morning": "Check-out (7h), chợ Tuy Hòa lần cuối, đổ đầy dầu",
        "afternoon": "Khởi hành TP.HCM (8h30), dừng ăn trưa Phan Rang/Phan Thiết",
        "evening": "Về nhà (17h–19h)",
        "key_locations": ["Tuy Hòa", "QL1A", "Phan Rang", "TP.HCM"],
        "food_highlights": ["Bún cá ngừ lần cuối (ăn sáng)"],
    },
}


class TripContextService:
    def get_state(self) -> dict:
        now = datetime.now(VN_TZ)
        today = now.date()
        days_diff = (today - TRIP_START_DATE).days

        base = {
            "current_time": now.strftime("%H:%M"),
            "current_date": now.strftime("%d/%m/%Y"),
            "day_of_week": now.strftime("%A"),
            "time_slot": _time_slot(now.hour),
        }

        if days_diff < 0:
            return {**base, "status": "pre_trip", "days_until_trip": -days_diff}

        if days_diff > 4:
            return {**base, "status": "post_trip"}

        day_num = days_diff + 1
        return {
            **base,
            "status": "ongoing",
            "day_number": day_num,
            "total_days": 5,
            "day_plan": TRIP_DAYS.get(day_num, {}),
        }

    def format_for_prompt(self, state: dict, companion_state=None) -> str:
        lines = [
            f"Current time (Vietnam): {state['current_time']} on {state['current_date']}",
            f"Time of day: {state['time_slot']}",
        ]
        status = state["status"]

        if status == "pre_trip":
            lines.append(f"Trip status: NOT STARTED — {state['days_until_trip']} days until departure (23/05/2026)")
            lines.append("Context: User is planning or preparing. Help with pre-trip questions.")
        elif status == "post_trip":
            lines.append("Trip status: COMPLETED — the Phú Yên trip has ended.")
        elif status == "ongoing":
            day = state["day_number"]
            plan = state["day_plan"]
            slot = state["time_slot"]

            lines.append(f"Trip status: ONGOING — Day {day} of 5")
            lines.append(f"Today's theme: {plan.get('theme', '')}")

            if slot == "morning":
                lines.append(f"Morning agenda: {plan.get('morning', '')}")
            elif slot in ("midday", "afternoon"):
                lines.append(f"Afternoon agenda: {plan.get('afternoon', '')}")
            else:
                lines.append(f"Evening agenda: {plan.get('evening', '')}")

            food = plan.get("food_highlights", [])
            if food:
                lines.append(f"Food highlights today: {', '.join(food)}")

            locs = plan.get("key_locations", [])
            if locs:
                lines.append(f"Key locations today: {', '.join(locs)}")

            child = plan.get("child_note", "")
            if child:
                lines.append(f"Child note: {child}")

            if plan.get("early_start"):
                lines.append("Note: Today has an early start — group may be tired by afternoon.")
            if plan.get("relaxed_day"):
                lines.append("Note: This is a relaxed day — lower activity intensity recommended.")
            if plan.get("is_return_day"):
                lines.append("Note: Today is the return drive day — group is heading home.")

        # Inject emotional companion state if available
        if companion_state is not None:
            if companion_state.fatigue > 0.5:
                lines.append(f"Detected user state: HIGH FATIGUE — simplify suggestions, reduce movement.")
            if companion_state.stress > 0.5:
                lines.append(f"Detected user state: STRESSED — use SIMPLIFIED MODE, one clear option only.")
            if companion_state.confusion > 0.5:
                lines.append(f"Detected user state: CONFUSED — give one direct answer, no options list.")
            if companion_state.excitement > 0.5:
                lines.append(f"Detected user state: EXCITED — match their energy, be enthusiastic.")
            if companion_state.response_mode == "simplified":
                lines.append("Response mode: SIMPLIFIED — short reply, 1 suggestion max, comfort tone.")

        return "\n".join(lines)


def _time_slot(hour: int) -> str:
    if hour < 10:
        return "morning"
    if hour < 14:
        return "midday"
    if hour < 18:
        return "afternoon"
    if hour < 21:
        return "evening"
    return "night"
