import asyncio

from app.services.command_handlers import CommandHandlers
from app.schemas.telegram import TelegramMessage


class FakeSheets:
    async def expenses_recent(self, limit: int = 5) -> dict:
        return {
            "items": [
                {
                    "date": "24/05/2026",
                    "note": "Ăn tối",
                    "amount": 500_000,
                    "category": "🍜 Ăn uống",
                    "group": "Nhóm LV",
                }
            ],
            "total_rows": 1,
        }

    async def expenses_total(self) -> dict:
        return {"total": 1_500_000, "count": 2, "by_group": {"Nhóm LV": 1_000_000, "Nhóm LH": 500_000}}

    async def expenses_by_category(self) -> dict:
        return {"by_category": {"🍜 Ăn uống": 500_000, "🏨 Lưu trú": 1_000_000}}

    async def expenses_by_day(self) -> dict:
        return {"by_day": {"24/05/2026": 1_500_000}}

    async def report_full(self) -> dict:
        return {
            "total": {"total": 1_500_000, "count": 2, "by_group": {"Nhóm LV": 1_000_000}},
            "by_category": {"by_category": {"🍜 Ăn uống": 500_000}},
            "contributions": {"total_contributed": 5_000_000, "items": [{"group": "Nhóm LV", "amount": 5_000_000, "status": "Đã chuyển"}]},
            "debts": {"balance": {"Nhóm LV": 100_000}},
        }

    async def debts(self) -> dict:
        return {"spent": {"Nhóm LV": 1_000_000, "total": 1_000_000}, "balance": {"Nhóm LV": 100_000}}

    async def contributions(self) -> dict:
        return {"total_contributed": 5_000_000, "items": [{"group": "Nhóm LV", "amount": 5_000_000, "status": "Đã chuyển", "note": ""}]}

    async def packing_status(self, filter: str = "") -> dict:
        if filter == "packed":
            return {"packed": 1, "total": 2, "items": [{"name": "Ô", "quantity": "1"}]}
        return {"not_packed": 1, "total": 2, "mandatory_left": ["Kem chống nắng"], "items": [{"group": "Chung", "name": "Kem chống nắng", "quantity": "1"}]}

    async def restaurants(self, area: str = "") -> dict:
        return {"items": [{"name": "Bún cá", "area": "Tuy Hòa", "type": "Bún", "price_k": 50, "on_route": True, "note": "local ngon"}]}

    async def members(self) -> dict:
        return {"items": [{"name": "Liem", "username": "", "group": "Nhóm LV", "note": "admin"}]}


def build_message(text: str) -> TelegramMessage:
    return TelegramMessage.model_validate(
        {
            "message_id": 1,
            "date": 1_778_000_000,
            "chat": {"id": 8654136346, "type": "private"},
            "from": {
                "id": 8654136346,
                "is_bot": False,
                "first_name": "Liem",
                "username": None,
            },
            "text": text,
        }
    )


def test_start_command_has_welcome_reply() -> None:
    handler = CommandHandlers(sheets=FakeSheets())
    reply = asyncio.run(handler.handle("/start", build_message("/start")))
    assert reply is not None
    assert "Xin chào Liem" in reply
    assert "/tong" in reply


def test_id_command_returns_user_info() -> None:
    handler = CommandHandlers(sheets=FakeSheets())
    reply = asyncio.run(handler.handle("/id", build_message("/id")))
    assert reply is not None
    assert "User ID: 8654136346" in reply


def test_unknown_command_does_not_fall_back_to_ai() -> None:
    handler = CommandHandlers(sheets=FakeSheets())
    reply = asyncio.run(handler.handle("/abcxyz", build_message("/abcxyz")))
    assert reply == "Mình chưa có lệnh /abcxyz. Gõ /menu để xem các lệnh đang hỗ trợ nhé."


def test_expense_commands_return_sheet_data() -> None:
    handler = CommandHandlers(sheets=FakeSheets())
    recent = asyncio.run(handler.handle("/xem", build_message("/xem")))
    total = asyncio.run(handler.handle("/tong", build_message("/tong")))
    report = asyncio.run(handler.handle("/baocao", build_message("/baocao")))
    assert "Ăn tối" in recent
    assert "Tổng đã chi" in total
    assert "BÁO CÁO CHUYẾN PHÚ YÊN 2026" in report
