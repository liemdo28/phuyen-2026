import asyncio

from app.services.write_flow_handler import WriteFlowHandler


class FakeWriteSheets:
    async def write_expense(self, item: dict) -> dict:
        return {"ok": True, "written": item}

    async def write_packing(self, item: dict) -> dict:
        return {"ok": True, "written": {"item": item.get("ten_do")}}

    async def write_contribution(self, item: dict) -> dict:
        return {"ok": True, "written": {"group": item.get("nhom"), "trang_thai": item.get("trang_thai", "Đã chuyển")}}

    async def write_restaurant(self, item: dict) -> dict:
        return {"ok": True, "written": item}


def test_write_flow_preview_and_confirm(monkeypatch) -> None:
    async def fake_parse(text: str):
        from app.services.write_llm_parser import ParsedWrite
        return ParsedWrite(
            write_intent="expense",
            items=[{"khoan_chi": "Ăn tối", "so_tien": 500000, "danh_muc": "🍜 Ăn uống", "ngay": "", "nhom": "", "ghi_chu": ""}],
            parse_source="rule",
        )

    monkeypatch.setattr("app.services.write_flow_handler.parse_write_message", fake_parse)
    handler = WriteFlowHandler(sheets=FakeWriteSheets())

    preview = asyncio.run(handler.handle("500k ăn tối", 1, 2))
    confirmed = asyncio.run(handler.handle("có", 1, 2))

    assert "Mình hiểu đây là khoản chi tiêu" in preview
    assert "✅ Đã ghi: Ăn tối" in confirmed


def test_write_flow_cancel(monkeypatch) -> None:
    async def fake_parse(text: str):
        from app.services.write_llm_parser import ParsedWrite
        return ParsedWrite(
            write_intent="expense",
            items=[{"khoan_chi": "Ăn tối", "so_tien": 500000, "danh_muc": "🍜 Ăn uống"}],
        )

    monkeypatch.setattr("app.services.write_flow_handler.parse_write_message", fake_parse)
    handler = WriteFlowHandler(sheets=FakeWriteSheets())

    asyncio.run(handler.handle("500k ăn tối", 1, 2))
    cancelled = asyncio.run(handler.handle("không", 1, 2))

    assert cancelled == "Đã huỷ, không ghi gì cả. Bạn gửi lại khi cần nhé."


def test_write_flow_non_write_returns_none(monkeypatch) -> None:
    async def fake_parse(text: str):
        from app.services.write_llm_parser import ParsedWrite
        return ParsedWrite(write_intent="unknown")

    monkeypatch.setattr("app.services.write_flow_handler.parse_write_message", fake_parse)
    handler = WriteFlowHandler(sheets=FakeWriteSheets())

    result = asyncio.run(handler.handle("hôm nay trời đẹp", 1, 2))
    assert result is None
