from __future__ import annotations

from app.adapters.google_sheets import GoogleSheetsAdapter
from app.adapters.sheets_api_client import SheetsApiClient, SheetsApiError


def format_vnd(amount: float) -> str:
    amount = int(amount or 0)
    if amount >= 1_000_000_000:
        return f"{amount / 1_000_000_000:.1f} tỷ".replace(".0 tỷ", " tỷ")
    if amount >= 1_000_000:
        return f"{amount / 1_000_000:.1f}tr".replace(".0tr", "tr")
    if amount >= 1_000:
        return f"{amount / 1_000:.0f}k"
    return f"{amount:,}đ".replace(",", ".")


COMMAND_LIST = [
    ("/xem", "chi tiêu gần đây"),
    ("/tong", "tổng đã chi theo nhóm"),
    ("/baocao", "báo cáo đầy đủ"),
    ("/danhmuc", "chi tiêu theo danh mục"),
    ("/theongay", "chi tiêu theo ngày"),
    ("/congno", "ai trả ai (công nợ)"),
    ("/goptien", "tình hình góp tiền"),
    ("/doxep", "đồ cần đem — còn thiếu gì"),
    ("/dadem", "đồ đã đem"),
    ("/quanan", "danh sách quán ăn"),
    ("/thanhvien", "danh sách thành viên"),
    ("/reload", "refresh data cache từ Google Sheet"),
    ("/id", "lấy Telegram User ID"),
    ("/menu", "xem lại danh sách lệnh"),
]


class CommandHandlers:
    def __init__(
        self,
        sheets: SheetsApiClient | None = None,
        sheet_adapter: GoogleSheetsAdapter | None = None,
    ) -> None:
        self.sheets = sheets or SheetsApiClient()
        self.sheet_adapter = sheet_adapter or GoogleSheetsAdapter()

    async def handle(self, text: str, message) -> str | None:
        if not text.startswith("/"):
            return None

        cmd = text.split()[0].split("@")[0].lower()
        handler = {
            "/start": self._start,
            "/help": self._start,
            "/menu": self._menu,
            "/id": self._id,
            "/xem": self._xem,
            "/tong": self._tong,
            "/baocao": self._baocao,
            "/danhmuc": self._danhmuc,
            "/theongay": self._theongay,
            "/congno": self._congno,
            "/goptien": self._goptien,
            "/doxep": self._doxep,
            "/dadem": self._dadem,
            "/quanan": self._quanan,
            "/thanhvien": self._thanhvien,
            "/reload": self._reload,
        }.get(cmd)

        if handler is None:
            return f"Mình chưa có lệnh {cmd}. Gõ /menu để xem các lệnh đang hỗ trợ nhé."

        if cmd in {"/start", "/help", "/id", "/menu"}:
            return await handler(message)

        try:
            return await handler(message)
        except SheetsApiError as exc:
            return (
                "Mình chưa lấy được dữ liệu từ Google Sheet 😔\n"
                f"({exc})\n"
                "Bạn thử lại sau một chút, hoặc kiểm tra kết nối Sheet."
            )

    async def _start(self, message) -> str:
        first_name = message.from_user.first_name or "bạn"
        lines = [
            f"👋 Xin chào {first_name}! Mình là trợ lý chuyến Phú Yên 2026.",
            "",
            "💰 Ghi chi tiêu — nhắn tự nhiên:",
            "• 500k ăn tối | 1.5tr tiền phòng | 24/5 - 300k xăng",
            "• 📸 Gửi ảnh hoá đơn → bot tự đọc",
            "",
            "🍜 Tìm quán ăn — gửi 📍 vị trí rồi hỏi",
            "📦 Đồ cần đem — nhắn \"đã đem ô, thuốc\"",
            "",
            "📋 Các lệnh tra cứu:",
        ]
        for cmd, desc in COMMAND_LIST:
            lines.append(f"{cmd} — {desc}")
        return "\n".join(lines)

    async def _menu(self, message) -> str:
        lines = ["📋 Danh sách lệnh:"]
        for cmd, desc in COMMAND_LIST:
            lines.append(f"{cmd} — {desc}")
        return "\n".join(lines)

    async def _id(self, message) -> str:
        u = message.from_user
        username = f"@{u.username}" if u.username else "@(chưa có)"
        return (
            "🪪 Thông tin:\n\n"
            f"Username: {username}\n"
            f"User ID: {u.id}\n\n"
            'Copy ID -> paste vào cột B sheet "⚙️ Bot Config"'
        )

    async def _xem(self, message) -> str:
        data = await self.sheets.expenses_recent(limit=5)
        items = data.get("items", [])
        if not items:
            return "📋 Chưa có khoản chi tiêu nào được ghi."
        lines = [f"📋 {len(items)} khoản chi gần nhất (tổng cộng {data.get('total_rows', 0)} khoản):", ""]
        for it in items:
            line = f"• {it['date']} — {it['note']}: {format_vnd(it['amount'])}"
            if it.get("category"):
                line += f" ({it['category']})"
            if it.get("group"):
                line += f" [{it['group']}]"
            lines.append(line)
        return "\n".join(lines)

    async def _tong(self, message) -> str:
        data = await self.sheets.expenses_total()
        total = data.get("total", 0)
        by_group = data.get("by_group", {})
        lines = [f"💰 Tổng đã chi: {format_vnd(total)} ({data.get('count', 0)} khoản)", ""]
        for group, amount in sorted(by_group.items(), key=lambda x: -x[1]):
            lines.append(f"• {group}: {format_vnd(amount)}")
        return "\n".join(lines)

    async def _danhmuc(self, message) -> str:
        data = await self.sheets.expenses_by_category()
        by_cat = data.get("by_category", {})
        active = {k: v for k, v in by_cat.items() if v > 0}
        if not active:
            return "📊 Chưa có chi tiêu nào để thống kê theo danh mục."
        lines = ["📊 Chi tiêu theo danh mục:", ""]
        for cat, amount in sorted(active.items(), key=lambda x: -x[1]):
            lines.append(f"• {cat}: {format_vnd(amount)}")
        return "\n".join(lines)

    async def _theongay(self, message) -> str:
        data = await self.sheets.expenses_by_day()
        by_day = data.get("by_day", {})
        if not by_day:
            return "📅 Chưa có chi tiêu nào để thống kê theo ngày."
        lines = ["📅 Chi tiêu theo ngày:", ""]
        for day, amount in by_day.items():
            lines.append(f"• {day}: {format_vnd(amount)}")
        return "\n".join(lines)

    async def _baocao(self, message) -> str:
        data = await self.sheets.report_full()
        total = data.get("total", {})
        by_cat = data.get("by_category", {}).get("by_category", {})
        contrib = data.get("contributions", {})
        debts = data.get("debts", {})

        lines = ["📊 BÁO CÁO CHUYẾN PHÚ YÊN 2026", "─────────────────"]
        lines.append(f"💰 Tổng đã chi: {format_vnd(total.get('total', 0))} ({total.get('count', 0)} khoản)")
        for group, amount in sorted(total.get("by_group", {}).items(), key=lambda x: -x[1]):
            lines.append(f"   • {group}: {format_vnd(amount)}")

        active_cat = {k: v for k, v in by_cat.items() if v > 0}
        if active_cat:
            lines.extend(["", "📂 Theo danh mục:"])
            for cat, amount in sorted(active_cat.items(), key=lambda x: -x[1]):
                lines.append(f"   • {cat}: {format_vnd(amount)}")

        if contrib.get("items"):
            lines.extend(["", f"💵 Đã góp: {format_vnd(contrib.get('total_contributed', 0))}"])
            for it in contrib["items"]:
                lines.append(f"   • {it['group']}: {format_vnd(it['amount'])} — {it['status']}")

        balance = debts.get("balance", {})
        if balance:
            lines.extend(["", "⚖️ Cân đối (đã chi − phải trả):"])
            for group, amount in balance.items():
                sign = "dư" if amount >= 0 else "thiếu"
                lines.append(f"   • {group}: {format_vnd(abs(amount))} ({sign})")

        return "\n".join(lines)

    async def _congno(self, message) -> str:
        data = await self.sheets.debts()
        spent = data.get("spent", {})
        balance = data.get("balance", {})
        lines = ["⚖️ CÔNG NỢ", "─────────────────", "Đã chi:"]
        for group, amount in spent.items():
            if group == "total":
                continue
            lines.append(f"• {group}: {format_vnd(amount)}")
        lines.append(f"• Tổng: {format_vnd(spent.get('total', 0))}")
        lines.extend(["", "Cân đối (đã chi − phải trả):"])
        for group, amount in balance.items():
            sign = "được nhận lại" if amount >= 0 else "cần bù thêm"
            lines.append(f"• {group}: {format_vnd(abs(amount))} ({sign})")
        return "\n".join(lines)

    async def _goptien(self, message) -> str:
        data = await self.sheets.contributions()
        items = data.get("items", [])
        if not items:
            return "💵 Chưa có dữ liệu góp tiền."
        lines = [f"💵 GÓP TIỀN TRƯỚC — tổng {format_vnd(data.get('total_contributed', 0))}", ""]
        for it in items:
            emoji = "✅" if it["status"] == "Đã chuyển" else "⏳"
            line = f"{emoji} {it['group']}: {format_vnd(it['amount'])} — {it['status']}"
            if it.get("note"):
                line += f" ({it['note']})"
            lines.append(line)
        return "\n".join(lines)

    async def _doxep(self, message) -> str:
        data = await self.sheets.packing_status(filter="left")
        items = data.get("items", [])
        mandatory = data.get("mandatory_left", [])
        lines = [f"📦 ĐỒ CẦN ĐEM — còn {data.get('not_packed', 0)}/{data.get('total', 0)} món chưa đem"]
        if mandatory:
            lines.extend(["", "⚠️ BẮT BUỘC chưa đem:"])
            for name in mandatory:
                lines.append(f"   ❗ {name}")
        if items:
            lines.extend(["", "Danh sách chưa đem:"])
            by_group: dict[str, list] = {}
            for it in items:
                by_group.setdefault(it["group"] or "Chung", []).append(it)
            for group, group_items in by_group.items():
                lines.append(f"  [{group}]")
                for it in group_items:
                    qty = f" ({it['quantity']})" if it.get("quantity") else ""
                    lines.append(f"   ☐ {it['name']}{qty}")
        else:
            lines.extend(["", "🎉 Đã đem hết đồ rồi!"])
        return "\n".join(lines)

    async def _dadem(self, message) -> str:
        data = await self.sheets.packing_status(filter="packed")
        items = data.get("items", [])
        if not items:
            return "📦 Chưa đánh dấu món nào là đã đem."
        lines = [f"✅ ĐÃ ĐEM — {data.get('packed', 0)}/{data.get('total', 0)} món", ""]
        for it in items:
            qty = f" ({it['quantity']})" if it.get("quantity") else ""
            lines.append(f"   ✓ {it['name']}{qty}")
        return "\n".join(lines)

    async def _quanan(self, message) -> str:
        data = await self.sheets.restaurants()
        items = data.get("items", [])
        if not items:
            return "🍜 Chưa có quán ăn nào trong danh sách."
        lines = [f"🍜 DANH SÁCH QUÁN ĂN ({len(items)} quán):", ""]
        by_area: dict[str, list] = {}
        for it in items:
            by_area.setdefault(it["area"] or "Khác", []).append(it)
        for area, area_items in by_area.items():
            lines.append(f"📍 {area}:")
            for it in area_items:
                route = " 🚗" if it.get("on_route") else ""
                lines.append(f"   • {it['name']} — {it['type']} ~{it['price_k']}k/người{route}")
                if it.get("note"):
                    lines.append(f"     💬 {it['note']}")
        lines.extend(["", "💡 Gửi 📍 vị trí để mình tìm quán gần bạn nhất."])
        return "\n".join(lines)

    async def _thanhvien(self, message) -> str:
        data = await self.sheets.members()
        items = data.get("items", [])
        if not items:
            return "👥 Chưa có thành viên nào trong Bot Config."
        lines = [f"👥 THÀNH VIÊN ({len(items)} người):", ""]
        by_group: dict[str, list] = {}
        for it in items:
            by_group.setdefault(it["group"], []).append(it)
        for group, group_members in by_group.items():
            lines.append(f"  [{group}]")
            for member in group_members:
                uname = f" (@{member['username']})" if member.get("username") else ""
                note = f" — {member['note']}" if member.get("note") else ""
                lines.append(f"   • {member['name']}{uname}{note}")
        return "\n".join(lines)

    async def _reload(self, message) -> str:
        self.sheet_adapter.invalidate_cache()
        return "✅ Đã refresh data từ sheet."
