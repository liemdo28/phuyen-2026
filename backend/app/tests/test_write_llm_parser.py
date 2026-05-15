import asyncio

from app.services.write_llm_parser import parse_write_message


def test_parse_write_message_short_circuits_long_expense_without_llm(monkeypatch) -> None:
    async def fake_call_openai(text: str, rule) -> dict:
        raise AssertionError("LLM should not be called for high-confidence rule expense")

    monkeypatch.setattr("app.services.write_llm_parser._call_openai", fake_call_openai)

    text = (
        "Khách sạn\n"
        "Sun Village Resort - Phú Yên\n"
        "https://www.agoda.com/vi-vn/sun-village/hotel/phuong-sau-vn.htm?checkIn=2026-05-23\n"
        "2 Superior và 1 Deluxe Có ăn sáng\n"
        "8,675,000\n"
        "Liêm"
    )

    parsed = asyncio.run(parse_write_message(text))

    assert parsed.write_intent == "expense"
    assert parsed.items
    assert parsed.items[0]["so_tien"] == 8_675_000
    assert parsed.items[0]["danh_muc"] == "🏨 Lưu trú"
    assert parsed.items[0]["nhom"] == "Nhóm LV"
    assert parsed.parse_source == "rule"
