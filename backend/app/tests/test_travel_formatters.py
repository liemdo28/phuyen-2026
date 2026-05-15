from __future__ import annotations

from app.services.travel_formatters import format_budget_reply
from app.services.travel_formatters import format_food_reply
from app.services.travel_formatters import format_itinerary_reply


def test_format_budget_reply_with_real_data() -> None:
    rows = [
        {
            "_kind": "metadata",
            "Ngân sách": "30,000,000",
            "Tổng": "21,600,000",
            "Còn": "8,400,000",
        },
        {
            "_kind": "item",
            "Mục": "Khách sạn",
            "Nội dung": "Sun Village Resort - Phú Yên",
            "Tạm tính": "8,400,000",
            "Thực tính": "8,400,000",
            "Ứng trước": "Liêm",
        },
        {
            "_kind": "item",
            "Mục": "Khách sạn",
            "Nội dung": "Nắng Hạ Homestay",
            "Tạm tính": "1,600,000",
            "Thực tính": "1,600,000",
            "Ứng trước": "Linh",
        },
    ]
    reply = format_budget_reply(rows, {}, spreadsheet_url="https://docs.google.com/spreadsheets/d/demo/edit", sheet_gid="1005821825")
    assert "Sun Village" in reply
    assert "8,400,000" in reply
    assert "Liêm" in reply
    assert "(đã giảm giá)" not in reply
    assert "khoảng" not in reply


def test_format_itinerary_reply_filters_by_date() -> None:
    rows = [
        {"Date": "23/5", "From": "4:00", "To": "7:00", "Activity": "HCM → Phan Thiết", "Destination": "Phan Thiết"},
        {"Date": "24/5", "From": "7:00", "To": "8:00", "Activity": "Ăn sáng", "Destination": "Tuy Hòa"},
    ]
    reply = format_itinerary_reply(rows, {"date_filter": "23/05"})
    assert "HCM → Phan Thiết" in reply
    assert "Ăn sáng" not in reply


def test_format_food_reply_preserves_sheet_values() -> None:
    rows = [
        {
            "Tên quán": "Bánh canh hẹ",
            "Khu vực": "Thành Tâm",
            "Loại": "53 Điện Biên Phủ, Tuy Hòa",
            "Giá (k/ng)": "https://maps.app.goo.gl/demo",
            "Lat": "6h sáng tới 21h tối",
        }
    ]
    reply = format_food_reply(rows, {"area_filter": "tuy hòa"})
    assert "Bánh canh hẹ" in reply
    assert "https://maps.app.goo.gl/demo" in reply
