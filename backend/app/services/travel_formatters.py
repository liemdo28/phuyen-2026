from __future__ import annotations

from typing import Any

from app.services.sheet_query import row_matches_filter


def format_travel_reply(
    intent: str,
    rows: list[dict[str, Any]],
    query_params: dict[str, Any],
    *,
    spreadsheet_url: str = "",
    sheet_gid: str | None = None,
) -> str:
    formatter = TRAVEL_FORMATTERS[intent]
    return formatter(
        rows,
        query_params,
        spreadsheet_url=spreadsheet_url,
        sheet_gid=sheet_gid,
    )


def format_budget_reply(
    rows: list[dict[str, Any]],
    query_params: dict[str, Any],
    *,
    spreadsheet_url: str = "",
    sheet_gid: str | None = None,
) -> str:
    metadata = next((row for row in rows if row.get("_kind") == "metadata"), {})
    items = [row for row in rows if row.get("_kind") == "item"]
    if not items and not metadata:
        return "💰 Chưa có dữ liệu ngân sách trong tab Tổng Chi phí."

    total_budget = _parse_vnd(metadata.get("Ngân sách", ""))
    spent = _parse_vnd(metadata.get("Tổng", ""))
    remaining = _parse_vnd(metadata.get("Còn", ""))
    lines = ["💰 Ngân sách chuyến đi:"]
    if total_budget:
        lines.append(f"- Tổng dự kiến: {_format_money(total_budget)} VND")
    if spent:
        lines.append(f"- Đã chi/đặt cọc: {_format_money(spent)} VND")
    if remaining:
        lines.append(f"- Còn lại: {_format_money(remaining)} VND")

    lines.extend(["", "📋 Chi tiết:"])
    for idx, row in enumerate(items, 1):
        detail = row.get("Chi tiết", "")
        note = row.get("Ghi chú", "")
        advance = row.get("Ứng trước", "")
        amount = _parse_vnd(row.get("Thực tính") or row.get("Tạm tính"))
        line = f"{idx}. {row.get('Nội dung', row.get('Mục', 'Khoản mục'))}"
        if amount:
            line += f": {_format_money(amount)}đ"
        if advance:
            line += f" — {advance} ứng trước"
        lines.append(line)
        extras = [part for part in [detail, note] if part]
        if extras:
            lines.append(f"   {' | '.join(extras[:2])}")

    link = _sheet_link(spreadsheet_url, sheet_gid)
    if link:
        lines.extend(["", f"Xem chi tiết: {link}"])
    return "\n".join(lines)


def format_itinerary_reply(
    rows: list[dict[str, Any]],
    query_params: dict[str, Any],
    *,
    spreadsheet_url: str = "",
    sheet_gid: str | None = None,
) -> str:
    if not rows:
        return "🗓 Chưa có dữ liệu lịch trình trong sheet."
    date_filter = query_params.get("date_filter")
    filtered = rows
    if date_filter:
        target = _normalize_date_fragment(date_filter)
        filtered = [
            row
            for row in rows
            if _normalize_date_fragment(str(row.get("Date", ""))) == target
        ]
    if not filtered:
        return "🗓 Không thấy hoạt động nào khớp ngày bạn hỏi trong tab Lịch trình."

    title = "🗓 Lịch trình"
    if date_filter:
        title += f" {date_filter}:"
    else:
        title += ":"
    lines = [title, ""]
    for row in filtered[:12]:
        start = row.get("From", "").strip()
        end = row.get("To", "").strip()
        window = " — ".join(part for part in [start, end] if part)
        activity = row.get("Activity", "").strip() or "Hoạt động"
        destination = row.get("Destination", "").strip()
        note = row.get("Note", "").strip()
        line = f"• {window} — {activity}" if window else f"• {activity}"
        if destination:
            line += f" @ {destination}"
        lines.append(line)
        if note:
            lines.append(f"  {note}")
    return "\n".join(lines)


def format_food_reply(
    rows: list[dict[str, Any]],
    query_params: dict[str, Any],
    *,
    spreadsheet_url: str = "",
    sheet_gid: str | None = None,
) -> str:
    if not rows:
        return "🍜 Chưa có dữ liệu quán ăn trong sheet."
    area_filter = query_params.get("area_filter")
    filtered = rows
    if area_filter:
        filtered = [row for row in rows if row_matches_filter(row, area_filter)]
    if not filtered:
        filtered = rows[:5]

    lines = ["🍜 Gợi ý từ tab Quán ăn:", ""]
    for row in filtered[:5]:
        name = row.get("Tên quán") or row.get("col_1") or "Quán ăn"
        values = [value for key, value in row.items() if key != "Tên quán" and value]
        url = next((value for value in values if str(value).startswith("http")), "")
        details = [value for value in values if value != url][:3]
        lines.append(f"• {name}")
        if details:
            lines.append(f"  {' — '.join(str(v) for v in details)}")
        if url:
            lines.append(f"  📍 {url}")
    return "\n".join(lines)


def format_suggestion_reply(
    rows: list[dict[str, Any]],
    query_params: dict[str, Any],
    *,
    spreadsheet_url: str = "",
    sheet_gid: str | None = None,
) -> str:
    if not rows:
        return "💡 Tab Gợi Ý Lịch Trình đang trống."
    keywords = query_params.get("keywords") or []
    filtered = rows
    for keyword in keywords[:2]:
        matched = [row for row in filtered if row_matches_filter(row, keyword)]
        if matched:
            filtered = matched
    lines = ["💡 Gợi ý owner đã lưu trong sheet:", ""]
    for row in filtered[:8]:
        lines.append(f"• {row.get('line', '').strip()}")
    return "\n".join(lines)


def format_weather_reply(
    rows: list[dict[str, Any]],
    query_params: dict[str, Any],
    *,
    spreadsheet_url: str = "",
    sheet_gid: str | None = None,
) -> str:
    if not rows:
        return "🌤 Chưa có dữ liệu thời tiết trong sheet."
    date_filter = query_params.get("date_filter")
    filtered = rows
    if date_filter:
        target = _normalize_date_fragment(date_filter)
        filtered = [
            row
            for row in rows
            if target in _normalize_date_fragment(str(row.get("Ngày", "")))
        ]
    if not filtered:
        filtered = rows[:3]
    lines = ["🌤 Thời tiết theo sheet:", ""]
    for row in filtered[:5]:
        lines.append(
            f"• {row.get('Ngày', '—')}: {row.get('Thời tiết', '—')} | {row.get('Tmax', '—')} / {row.get('Tmin', '—')} | Mưa {row.get('Mưa (mm)', '—')}"
        )
    return "\n".join(lines)


def format_packing_reply(
    rows: list[dict[str, Any]],
    query_params: dict[str, Any],
    *,
    spreadsheet_url: str = "",
    sheet_gid: str | None = None,
) -> str:
    if not rows:
        return "📦 Chưa có checklist đồ mang theo trong sheet."
    lines = ["📦 Checklist cần mang:", ""]
    for row in rows[:12]:
        checked = "✅" if str(row.get("Đã đem", "")).upper() == "TRUE" else "⬜"
        item = row.get("Đồ vật", "Món đồ")
        owner = row.get("Nhóm phụ trách", "")
        qty = row.get("Số lượng", "")
        note = row.get("Ghi chú", "")
        line = f"{checked} {item}"
        if qty:
            line += f" ({qty})"
        if owner:
            line += f" — {owner}"
        lines.append(line)
        if note:
            lines.append(f"  {note}")
    return "\n".join(lines)


def format_contribution_reply(
    rows: list[dict[str, Any]],
    query_params: dict[str, Any],
    *,
    spreadsheet_url: str = "",
    sheet_gid: str | None = None,
) -> str:
    if not rows:
        return "💵 Chưa có dữ liệu góp tiền trong sheet."
    lines = ["💵 Tình hình góp tiền:", ""]
    for row in rows:
        group = row.get("Nhóm", "Nhóm")
        amount = row.get("Đã góp (VNĐ)", "0")
        status = row.get("Trạng thái", "")
        note = row.get("Ghi chú", "")
        line = f"• {group}: {amount}"
        if status:
            line += f" — {status}"
        if note:
            line += f" ({note})"
        lines.append(line)
    return "\n".join(lines)


def format_expense_reply(
    rows: list[dict[str, Any]],
    query_params: dict[str, Any],
    *,
    spreadsheet_url: str = "",
    sheet_gid: str | None = None,
) -> str:
    if not rows:
        return "💸 Chưa có khoản chi nào trong tab Chi Tiêu."
    entity_filter = query_params.get("entity_filter")
    filtered = rows
    if entity_filter:
        filtered = [row for row in rows if row_matches_filter(row, entity_filter)]
    if not filtered:
        filtered = rows[-5:]
    lines = ["💸 Chi tiêu trong sheet:", ""]
    for row in filtered[:8]:
        lines.append(
            f"• {row.get('Ngày', '—')} — {row.get('Khoản Chi', '—')}: {row.get('Số Tiền (VNĐ)', '—')} [{row.get('Nhóm Trả', '—')}]"
        )
    return "\n".join(lines)


def format_summary_reply(
    rows: list[dict[str, Any]],
    query_params: dict[str, Any],
    *,
    spreadsheet_url: str = "",
    sheet_gid: str | None = None,
) -> str:
    if not rows:
        return "📊 Tab Tổng Hợp đang trống."
    lines = ["📊 Tổng hợp từ sheet:", ""]
    for row in rows[:8]:
        lines.append(f"• {row.get('line', '').strip()}")
    return "\n".join(lines)


TRAVEL_FORMATTERS = {
    "budget": format_budget_reply,
    "itinerary": format_itinerary_reply,
    "food": format_food_reply,
    "suggestion": format_suggestion_reply,
    "weather": format_weather_reply,
    "packing": format_packing_reply,
    "contribution": format_contribution_reply,
    "expense_query": format_expense_reply,
    "summary": format_summary_reply,
}


def _parse_vnd(value: Any) -> int:
    text = str(value or "").strip()
    digits = "".join(ch for ch in text if ch.isdigit())
    return int(digits) if digits else 0


def _format_money(amount: int) -> str:
    return f"{amount:,}"


def _sheet_link(spreadsheet_url: str, sheet_gid: str | None) -> str:
    if not spreadsheet_url:
        return ""
    if sheet_gid:
        return f"{spreadsheet_url.split('#')[0].split('?')[0]}?gid={sheet_gid}#gid={sheet_gid}"
    return spreadsheet_url


def _normalize_date_fragment(value: str) -> str:
    parts = value.strip().split()
    date_part = parts[0] if parts else value.strip()
    date_part = date_part.replace("-", "/")
    chunks = date_part.split("/")
    if len(chunks) >= 2 and chunks[0].isdigit() and chunks[1].isdigit():
        return f"{int(chunks[0]):02d}/{int(chunks[1]):02d}"
    return date_part
