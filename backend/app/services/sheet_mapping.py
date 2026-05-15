from __future__ import annotations

from app.schemas.workflow import SheetMapping


DEFAULT_MAPPINGS: dict[str, SheetMapping] = {
    "expenses": SheetMapping(
        domain="expenses",
        sheet_name="Chi Tiêu",
        key_columns=["date", "note", "amount"],
        writable_columns=["date", "note", "amount", "category", "group"],
    ),
    "tasks": SheetMapping(
        domain="tasks",
        sheet_name="Tasks",
        key_columns=["entity_name", "deadline", "status"],
        writable_columns=["entity_name", "deadline", "status", "note"],
    ),
    "inventory": SheetMapping(
        domain="inventory",
        sheet_name="Inventory",
        key_columns=["entity_name", "date"],
        writable_columns=["entity_name", "date", "quantity", "note", "status"],
    ),
    "revenue": SheetMapping(
        domain="revenue",
        sheet_name="Revenue",
        key_columns=["date", "amount"],
        writable_columns=["date", "amount", "note", "category"],
    ),
}


TRAVEL_MAPPINGS: dict[str, SheetMapping] = {
    "itinerary": SheetMapping(
        domain="itinerary",
        sheet_name="Lịch trình",
        key_columns=["day", "date", "activity", "destination"],
        writable_columns=[],
    ),
    "food": SheetMapping(
        domain="food",
        sheet_name="Quán ăn",
        key_columns=["Tên quán", "Khu vực", "Loại"],
        writable_columns=[],
    ),
    "suggestion": SheetMapping(
        domain="suggestion",
        sheet_name="Gợi Ý Lịch Trình",
        key_columns=["line"],
        writable_columns=[],
    ),
    "weather": SheetMapping(
        domain="weather",
        sheet_name="Thời Tiết",
        key_columns=["Ngày", "Thời tiết"],
        writable_columns=[],
    ),
    "packing": SheetMapping(
        domain="packing",
        sheet_name="Phải đem",
        key_columns=["Đồ vật", "Nhóm phụ trách"],
        writable_columns=["Đã đem"],
    ),
    "contribution": SheetMapping(
        domain="contribution",
        sheet_name="Góp Tiền Trước",
        key_columns=["Nhóm", "Đã góp (VNĐ)"],
        writable_columns=[],
    ),
    "expense_query": SheetMapping(
        domain="expense_query",
        sheet_name="Chi Tiêu",
        key_columns=["Ngày", "Khoản Chi", "Số Tiền (VNĐ)"],
        writable_columns=[],
    ),
    "summary": SheetMapping(
        domain="summary",
        sheet_name="Tổng Hợp",
        key_columns=["line"],
        writable_columns=[],
    ),
    "budget": SheetMapping(
        domain="budget",
        sheet_name="Tổng Chi phí",
        gid="1005821825",
        key_columns=["Mục", "Nội dung", "Tạm tính"],
        writable_columns=[],
    ),
}


def get_sheet_mapping(domain: str) -> SheetMapping | None:
    return DEFAULT_MAPPINGS.get(domain) or TRAVEL_MAPPINGS.get(domain)
