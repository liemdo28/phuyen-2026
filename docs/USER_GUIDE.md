# Hướng Dẫn Sử Dụng PhuYen2026Bot — Cho 3 Nhóm LV / LH / CM

**Bot:** @PhuYen2026Bot
**Chuyến đi:** 23–27/05/2026 (5 ngày)
**Admin nhóm LV:** liemdo28

---

## NHỮNG GÌ BOT LÀM ĐƯỢC

### 💬 Chat tự nhiên (không cần lệnh)

Bot hiểu tiếng Việt tự nhiên. Cứ nói như chat với bạn:

| Bạn nói | Bot hiểu |
|---|---|
| `500k ăn tối` | Lưu chi tiêu 500k vào ăn uống |
| `24/5 - 300k xăng` | Lưu chi tiêu 300k ngày 24/05 vào xăng dầu |
| `1.5tr tiền phòng, 200k sáng, 80k cafe` | Lưu 3 khoản cùng lúc |
| `đã đem ô, thuốc hạ sốt, kem chống nắng` | Tick đồ đã đem trong danh sách |
| `trên đường về có quán nào ngon` | Gợi ý quán đường về (có đánh dấu "Đường về") |
| `mai trời thế nào` | Dự báo thời tiết Phú Yên |

### 🔧 Lệnh nhanh (gõ /lệnh)

| Lệnh | Làm gì |
|---|---|
| `/start` | Bắt đầu, xem danh sách lệnh |
| `/id` | Lấy User ID của bạn |
| `/thanhvien` | Xem ai ở nhóm nào (LV / LH / CM) |
| `/goptien` | Kiểm tra ai đã chuyển tiền chưa |
| `/doxep` | Xem đồ cần đem, đã đem chưa |
| `/dadem` | Xem danh sách đồ đã tick |
| `/xem` | 5 khoản chi gần nhất |
| `/tong` | Tổng đã chi (tổng + theo nhóm) |
| `/danhmuc` | Chi tiêu theo danh mục (lưu trú, ăn uống...) |
| `/theongay` | Chi tiêu theo từng ngày |
| `/quanan` | Danh sách 10 quán ăn gợi ý |
| `/thoitiet` | Dự báo thời tiết Phú Yên |
| `/baocao` | Báo cáo đầy đủ: tổng + nhóm + danh mục + góp tiền |
| `/congno` | Xem ai thừa thiếu, cần bù bao nhiêu |

---

## CÁCH SỬ DỤNG THỰC TẾ

### Ghi chi tiêu (quan trọng nhất)

**Cách 1 — Nói tự nhiên:**
```
500k ăn tối
1.2tr tiền phòng
200k cafe sáng
```

**Cách 2 — Kèm ngày:**
```
23/5 - 800k xăng đi
24/5 - 300k ăn trưa
```

**Cách 3 — Ảnh hóa đơn:**
Gửi ảnh hóa đơn → Bot đọc số tiền → hỏi xác nhận → lưu

### Tick đồ đã đem

```
đã đem ô, thuốc hạ sốt, kem chống nắng
```

Bot sẽ tick các món đó trong sheet "Phải Đem".

### Hỏi quán ăn

```
/quanan              → Danh sách 10 quán theo khu vực
gửi location        → Quán gần vị trí nhất
trên đường về có quán nào ngon  → Chỉ quán có đánh dấu "Đường về"
```

### Xem thời tiết

```
/thoitiet           → Dự báo hôm nay
mai trời thế nào    → Dự báo ngày mai
```

### Theo dõi chi tiêu

```
/xem                → Vừa chi gì (5 khoản gần nhất)
/tong               → Tổng + chia theo nhóm LV/LH/CM
/danhmuc            → Chi theo danh mục (ăn uống, xăng dầu, lưu trú...)
/baocao             → Báo cáo đầy đủ cả chuyến đi
```

---

## CẬP NHẬT GÓP TIỀN GIỮA CHUYẾN

```
nhóm CM đã chuyển 15tr
LV chuyển thêm 5tr
```

Bot cập nhật sheet "Góp Tiền Trước" ngay.

---

## NHỮNG ĐIỀU CẦN LƯU Ý

- **Sau 15 phút không nhắn**, bot ngủ (Render free sleep). Lần đầu nhắn lại sẽ chậm ~30–60 giây. Không cần lo — tin nhắn không mất.
- **Bot đọc Google Sheet thật** — mọi số liệu đều real-time, không phải mock.
- **AI hiểu tiếng Việt** — không cần command chuẩn, cứ nói tự nhiên.
- **Nếu bot trả lời lạ** — gõ `/start` để reset context.

---

## AI SẼ CHỦ ĐỘNG

Bot có "Travel Operating System" — tự động:

- 🧠 Học phong cách đi của nhóm (thích biển / ẩm thực / chậm rãi...)
- ⚡ Cảnh báo nếu nhóm mệt — giảm activity, ưu tiên nghỉ
- 🌦️ Cảnh báo thời tiết xấu — tự đổi sang phương án trong nhà
- 📍 Gợi ý quán đường về — không spam, chỉ lúc cần
- 💡 Nhắc nhở nhẹ nhàng — "Nhóm đang mệt, ưu tiên nghỉ"

---

## NGÀY NÀO NÊN HỎI GÌ

| Ngày | Nên hỏi |
|---|---|
| 23/05 (T7) | `/thoitiet` — trời đường đi thế nào? |
| 24/05 (CN) | `gửi location` — quán gần Gành Đá Đĩa? |
| 25/05 (T2) | `/thoitiet` — trời Mũi Điện sáng sớm thế nào? |
| 26/05 (T3) | `/tong` — đã chi bao nhiêu? |
| 27/05 (T4) | `/baocao` — tổng kết chuyến đi |

---

## KÊNH LIÊN HỆ NẾU CẦN HỖ TRỢ

- **Bug bot:** nhắn `/id` → gửi User ID cho admin
- **Cần thêm quán:** `thêm quán [tên] ở [khu vực]`
- **Cần hỗ trợ khác:** liemdo28