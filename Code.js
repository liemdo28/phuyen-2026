// ════════════════════════════════════════════════════════
//  PHÚ YÊN 2026 — CHI TIÊU + LỊCH TRÌNH + TELEGRAM BOT
//  Nhóm: LV · LH · CM  |  7 người · 1 bé 4 tuổi · Carnival Dầu
//  Chuyến đi: 23–27/05/2026
// ════════════════════════════════════════════════════════

const CFG = {
  botBuild  : '2026-05-14-telefix-02',
  tripStart : '2026-05-23',
  tripEnd   : '2026-05-27',
  days      : ['23/05 (T7)','24/05 (CN)','25/05 (T2)','26/05 (T3)','27/05 (T4)'],
  groupSize : 7,
  childAge  : 4,
  car       : 'Kia Carnival (Dầu Diesel)',
  geminiApiKey: '', // ← Thêm key tại aistudio.google.com (miễn phí)

  coords: {
    'Tuy Hòa (trung tâm)'  : { lat: 13.0955, lon: 109.3028 },
    'Gành Đá Đĩa'          : { lat: 14.3912, lon: 109.2144 },
    'Đầm Ô Loan'           : { lat: 13.4200, lon: 109.2500 },
    'Mũi Điện / Đại Lãnh'  : { lat: 12.8667, lon: 109.4500 },
    'Bãi Xép'              : { lat: 13.0150, lon: 109.3280 },
    'Hòn Yến'              : { lat: 13.2500, lon: 109.3000 },
  },

  skipSheets: ['Chi Tiêu','Tổng Hợp','Góp Tiền Trước','Thời Tiết','Gợi Ý Lịch Trình','⚙️ Bot Config'],

  // Khách sạn / resort — cập nhật lat/lon đúng khi biết địa chỉ thật
  resort: { lat: 13.0955, lon: 109.3028, name: 'Khách sạn Tuy Hòa' },
};

const WX_LABEL = {
  0:'☀️ Trời quang',1:'🌤️ Ít mây',2:'⛅ Nhiều mây',3:'☁️ Âm u',
  45:'🌫️ Sương mù',48:'🌫️ Sương đá',
  51:'🌦️ Mưa phùn nhẹ',53:'🌦️ Mưa phùn',55:'🌧️ Mưa phùn nặng',
  61:'🌧️ Mưa nhẹ',63:'🌧️ Mưa vừa',65:'🌧️ Mưa to',
  80:'🌦️ Mưa rào nhẹ',81:'🌧️ Mưa rào',82:'⛈️ Mưa rào nặng',
  95:'⛈️ Giông',96:'⛈️ Giông + đá',99:'⛈️ Giông lớn',
};
function wxLabel(c) { return WX_LABEL[c] || `(${c})`; }
function wxOk(c,p)  { return c<=3&&p<5 ? '✅ Đẹp' : c<=55&&p<15 ? '⚠️ Được' : '❌ Xấu'; }

// ════════════════════════════════════════════════════════
//  MENU
// ════════════════════════════════════════════════════════
function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('🌴 Phú Yên 2026')
    .addItem('📖 Hướng Dẫn Sử Dụng',           'openHuongDan')
    .addSeparator()
    .addItem('🔧 Khởi tạo tất cả',             'setup')
    .addItem('🔄 Cập nhật Tổng Hợp',            'updateSummary')
    .addSeparator()
    .addItem('🤖 Cập nhật Thời Tiết & Gợi Ý',  'dailyAutoUpdate')
    .addSeparator()
    .addItem('⏰ Bật tự động 5h sáng',          'setupDailyTrigger')
    .addItem('⏹️ Tắt tự động',                  'deleteDailyTrigger')
    .addSeparator()
    .addItem('📱 Tạo sheet Bot Config',          'setupBotConfigSheet')
    .addItem('🔎 Kiểm tra Webhook Telegram',     'checkTelegramWebhookInfo')
    .addItem('🔗 Cài đặt Webhook Telegram',      'setupTelegramWebhook')
    .addItem('🧹 Xoá pending updates Telegram',  'clearTelegramPendingUpdates')
    .addSeparator()
    .addItem('☀️ Bật tin nhắn sáng 6h',         'setupMorningBriefingTrigger')
    .addItem('🔔 Bật nhắc nhở 20h tối',         'setupEveningReminderTrigger')
    .addItem('🔕 Tắt nhắc & tin nhắn sáng',     'deleteNotificationTriggers')
    .addSeparator()
    .addItem('🔄 Đặt lại Góp Tiền về 0',        'resetGopTien')
    .addItem('🗑️ Xoá dữ liệu chi tiêu',         'clearData')
    .addToUi();
}

// ════════════════════════════════════════════════════════
//  TRIGGER TỰ ĐỘNG 7H SÁNG
// ════════════════════════════════════════════════════════
function setupDailyTrigger() {
  ScriptApp.getProjectTriggers().forEach(t => {
    if (t.getHandlerFunction() === 'dailyAutoUpdate') ScriptApp.deleteTrigger(t);
  });
  ScriptApp.newTrigger('dailyAutoUpdate')
    .timeBased().atHour(5).everyDays(1).create();
  SpreadsheetApp.getUi().alert(
    '✅ Đã bật tự động 5h sáng!\n\n' +
    '⚠️ Quan trọng: Extensions → Apps Script → ⚙️ Project Settings\n' +
    '→ Time zone = "Asia/Ho_Chi_Minh"'
  );
}

function deleteDailyTrigger() {
  let n = 0;
  ScriptApp.getProjectTriggers().forEach(t => {
    if (t.getHandlerFunction() === 'dailyAutoUpdate') { ScriptApp.deleteTrigger(t); n++; }
  });
  SpreadsheetApp.getUi().alert(n > 0 ? '✅ Đã tắt.' : 'Không có trigger nào đang chạy.');
}

function dailyAutoUpdate() {
  const ss      = SpreadsheetApp.getActiveSpreadsheet();
  const weather = fetchWeather();
  buildWeatherSheet(ss, weather);
  const planData = readAllPlanSheets(ss);
  const text     = CFG.geminiApiKey
    ? analyzeWithGemini(planData, weather)
    : analyzeBuiltIn(planData, weather);
  buildSuggestionSheet(ss, text);
}

// ════════════════════════════════════════════════════════
//  SETUP
// ════════════════════════════════════════════════════════
function setup() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  makeQuanAnSheet(ss);
  makePhaIDemSheet(ss);
  makeGopTienSheet(ss);
  makeChiTieuSheet(ss);
  makeTongHopSheet(ss);
  dailyAutoUpdate();
  reorderSheets(ss);
  SpreadsheetApp.getUi().alert(
    '✅ Khởi tạo xong!\n\n' +
    '• "Quán Ăn" → danh sách quán, bot tìm theo vị trí\n' +
    '• "Phải Đem" → checklist đồ đem, bot check/update\n' +
    '• "Góp Tiền Trước" → khoản đã góp\n' +
    '• "Chi Tiêu" → nhập hàng ngày\n' +
    '• "Tổng Hợp" → kết quả tự động\n' +
    '• "Thời Tiết" → dự báo 23–27/05\n' +
    '• "Gợi Ý Lịch Trình" → phân tích & gợi ý\n\n' +
    'Dùng menu 📱 để cài Telegram Bot.'
  );
}

function makeGopTienSheet(ss) {
  let s = ss.getSheetByName('Góp Tiền Trước');
  const isNew = !s;
  if (isNew) s = ss.insertSheet('Góp Tiền Trước');

  // Giữ nguyên data người dùng đã nhập nếu sheet đã tồn tại
  let savedData = null;
  if (!isNew) savedData = s.getRange('A4:D6').getValues();

  try { const f = s.getFilter(); if (f) f.remove(); } catch(e) {}
  s.clear();
  s.getRange('A1').setValue('💵 KHOẢN GÓP TIỀN TRƯỚC').setFontSize(13).setFontWeight('bold');
  s.getRange('A1:D1').merge();
  s.getRange('A3:D3').setValues([['Nhóm','Đã góp (VNĐ)','Trạng thái','Ghi chú']])
    .setBackground('#2d3748').setFontColor('#fff').setFontWeight('bold');

  // Mặc định ban đầu tất cả 0 — không hardcode số tiền
  const defaultData = [
    ['Nhóm LV', 0, 'Chưa góp', ''],
    ['Nhóm LH', 0, 'Chưa góp', ''],
    ['Nhóm CM', 0, 'Chưa góp', ''],
  ];
  s.getRange('A4:D6').setValues(savedData || defaultData);
  s.getRange('B4:B6').setNumberFormat('#,##0 "đ"').setBackground('#fffbeb');
  // Màu trạng thái động theo giá trị
  for (let r = 4; r <= 6; r++) {
    const status = s.getRange(r, 3).getValue();
    s.getRange(r, 3).setBackground(status === 'Đã chuyển' ? '#c6f6d5' : '#fed7d7');
  }
  s.getRange('A4:A6').setFontWeight('bold');
  [90,170,120,230].forEach((w,i) => s.setColumnWidth(i+1,w));
}

function makeChiTieuSheet(ss) {
  let s = ss.getSheetByName('Chi Tiêu');
  const isNew = !s;
  if (isNew) s = ss.insertSheet('Chi Tiêu');

  // Giữ nguyên data chi tiêu đã nhập (cột B–H)
  let savedRows = null;
  if (!isNew && s.getLastRow() > 1) {
    savedRows = s.getRange(2, 2, s.getLastRow() - 1, 7).getValues();
  }

  try { const f = s.getFilter(); if (f) f.remove(); } catch(e) {}
  s.clear();
  s.getRange(1,1,1,8)
    .setValues([['STT','Ngày','Khoản Chi','Danh Mục','Số Tiền (VNĐ)','Nhóm Trả','Ghi Chú 1','Ghi Chú 2']])
    .setBackground('#2d3748').setFontColor('#fff').setFontWeight('bold').setHorizontalAlignment('center');

  s.getRange('D2:D1000').setDataValidation(
    SpreadsheetApp.newDataValidation()
      .requireValueInList(['🏨 Lưu trú','🍜 Ăn uống','🚗 Di chuyển','⛽ Xăng dầu',
                           '🎡 Vui chơi','🛒 Mua sắm','💊 Y tế','📦 Khác'], true)
      .setAllowInvalid(true).build()   // allowInvalid=true để không block restore data
  );
  s.getRange('F2:F1000').setDataValidation(
    SpreadsheetApp.newDataValidation()
      .requireValueInList(['Nhóm LV','Nhóm LH'], true)
      .setAllowInvalid(true).build()
  );
  s.getRange('B2:B1000').setNumberFormat('dd/mm/yyyy');
  s.getRange('E2:E1000').setNumberFormat('#,##0');
  for (let i = 2; i <= 300; i++) s.getRange(i,1).setFormula(`=IF(C${i}="","",ROW()-1)`);
  s.getRange('A2:A300').setFontColor('#a0aec0').setHorizontalAlignment('center');
  [45,105,210,130,155,100,185,185].forEach((w,i) => s.setColumnWidth(i+1,w));
  s.setFrozenRows(1);

  // Khôi phục data đã lưu
  if (savedRows && savedRows.length) {
    s.getRange(2, 2, savedRows.length, 7).setValues(savedRows);
    s.getRange(2, 2, savedRows.length, 1).setNumberFormat('dd/mm/yyyy');
  }
}

function makeTongHopSheet(ss) {
  let s = ss.getSheetByName('Tổng Hợp') || ss.insertSheet('Tổng Hợp');
  buildSummary(s);
}

function updateSummary() {
  const s = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Tổng Hợp');
  if (!s) { SpreadsheetApp.getUi().alert('Chạy Khởi tạo trước!'); return; }
  buildSummary(s);
  SpreadsheetApp.getUi().alert('✅ Đã cập nhật Tổng Hợp!');
}

function buildSummary(s) {
  s.clear();
  const hdr = (row, txt, bg) => {
    s.getRange(row,1).setValue(txt).setFontWeight('bold').setFontColor('#4a5568');
    s.getRange(row,1,1,4).merge().setBackground(bg || '#edf2f7');
  };
  s.getRange('A1').setValue('📊 TỔNG HỢP CHI TIÊU — PHÚ YÊN 2026').setFontSize(14).setFontWeight('bold');
  s.getRange('A1:D1').merge();

  hdr(3,'═ KHOẢN GÓP TRƯỚC');
  s.getRange('A4:D4').setValues([['','Nhóm LV','Nhóm LH','Nhóm CM']])
    .setBackground('#2d3748').setFontColor('#fff').setFontWeight('bold');
  s.getRange('A5').setValue('Đã góp');
  ['B','C','D'].forEach((col,i) => s.getRange(`${col}5`).setFormula(`='Góp Tiền Trước'!B${4+i}`));
  s.getRange('B5:D5').setNumberFormat('#,##0 "đ"');
  s.getRange('D5').setBackground('#fffbeb').setFontWeight('bold');

  hdr(7,'═ CHI TIÊU THỰC TẾ (Nhóm LV & LH trả)');
  s.getRange('A8:D8').setValues([['','Nhóm LV','Nhóm LH','Tổng']])
    .setBackground('#2d3748').setFontColor('#fff').setFontWeight('bold');
  s.getRange('A9').setValue('Đã chi').setFontWeight('bold');
  s.getRange('B9').setFormula("=SUMIF('Chi Tiêu'!F:F,\"Nhóm LV\",'Chi Tiêu'!E:E)");
  s.getRange('C9').setFormula("=SUMIF('Chi Tiêu'!F:F,\"Nhóm LH\",'Chi Tiêu'!E:E)");
  s.getRange('D9').setFormula('=B9+C9');
  s.getRange('B9:D9').setNumberFormat('#,##0 "đ"');

  hdr(11,'═ QUYẾT TOÁN CUỐI CHUYẾN');
  [
    ['Tổng chi thực tế (LV+LH)', '=D9'],
    ['Nhóm CM đã góp trước',     "='Góp Tiền Trước'!B6"],
    ['Còn lại (LV & LH chia đôi)','=B12-B13'],
    ['Mỗi nhóm phải trả',        '=B14/2'],
  ].forEach(([lbl,f],i) => {
    s.getRange(12+i,1).setValue(lbl).setFontWeight('bold').setFontColor('#4a5568');
    s.getRange(12+i,2).setFormula(f).setNumberFormat('#,##0 "đ"').setFontWeight('bold');
  });
  s.getRange('B14').setBackground('#e6ffed');
  s.getRange('B15').setBackground('#667eea').setFontColor('#fff');

  hdr(17,'═ SỐ DƯ TỪNG NHÓM');
  s.getRange('A18:C18').setValues([['','Nhóm LV','Nhóm LH']])
    .setBackground('#2d3748').setFontColor('#fff').setFontWeight('bold');
  s.getRange('A19').setValue('Đã chi − Phải trả').setFontWeight('bold');
  s.getRange('B19').setFormula('=B9-B15');
  s.getRange('C19').setFormula('=C9-B15');
  s.getRange('B19:C19').setNumberFormat('#,##0 "đ"').setFontWeight('bold');

  s.getRange('A21').setFormula(
    '=IF(B19<0,"⚡ Nhóm LV → Nhóm LH : "&TEXT(ABS(B19),"#,##0")&" đ",' +
    'IF(B19>0,"⚡ Nhóm LH → Nhóm LV : "&TEXT(B19,"#,##0")&" đ","✅ Cân bằng!"))'
  );
  s.getRange('A21:D21').merge()
    .setBackground('#fffbeb').setFontSize(13).setFontWeight('bold')
    .setHorizontalAlignment('center').setVerticalAlignment('middle');
  s.setRowHeight(21,46);

  hdr(23,'═ THEO DANH MỤC');
  s.getRange('A24:D24').setValues([['Danh mục','Nhóm LV','Nhóm LH','Tổng']])
    .setBackground('#2d3748').setFontColor('#fff').setFontWeight('bold');
  ['🏨 Lưu trú','🍜 Ăn uống','🚗 Di chuyển','⛽ Xăng dầu','🎡 Vui chơi','🛒 Mua sắm','💊 Y tế','📦 Khác']
    .forEach((cat,i) => {
      const r = 25+i;
      s.getRange(r,1).setValue(cat);
      s.getRange(r,2).setFormula(`=SUMIFS('Chi Tiêu'!E:E,'Chi Tiêu'!D:D,"${cat}",'Chi Tiêu'!F:F,"Nhóm LV")`);
      s.getRange(r,3).setFormula(`=SUMIFS('Chi Tiêu'!E:E,'Chi Tiêu'!D:D,"${cat}",'Chi Tiêu'!F:F,"Nhóm LH")`);
      s.getRange(r,4).setFormula(`=B${r}+C${r}`);
      s.getRange(r,2,1,3).setNumberFormat('#,##0 "đ"');
      if (i%2===0) s.getRange(r,1,1,4).setBackground('#f7fafc');
    });

  [220,155,155,130].forEach((w,i) => s.setColumnWidth(i+1,w));
  s.setFrozenRows(1);
}

function reorderSheets(ss) {
  ['⚙️ Bot Config','Quán Ăn','Phải Đem','Góp Tiền Trước','Chi Tiêu','Tổng Hợp','Thời Tiết','Gợi Ý Lịch Trình']
    .forEach((n,i) => {
      const sh = ss.getSheetByName(n);
      if (sh) { ss.setActiveSheet(sh); ss.moveActiveSheet(i+1); }
    });
}

function clearData() {
  const ui = SpreadsheetApp.getUi();
  if (ui.alert('Xoá toàn bộ dữ liệu "Chi Tiêu"?', ui.ButtonSet.YES_NO) !== ui.Button.YES) return;
  const s = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Chi Tiêu');
  if (s) s.getRange('B2:H500').clearContent();
}

function resetGopTien() {
  const ui = SpreadsheetApp.getUi();
  if (ui.alert('Đặt lại tất cả số tiền Góp Tiền về 0?', ui.ButtonSet.YES_NO) !== ui.Button.YES) return;
  const s = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Góp Tiền Trước');
  if (!s) { ui.alert('Không tìm thấy sheet "Góp Tiền Trước".'); return; }
  s.getRange('B4:D6').setValues([
    [0, 'Chưa góp', ''],
    [0, 'Chưa góp', ''],
    [0, 'Chưa góp', ''],
  ]);
  s.getRange('B4:B6').setNumberFormat('#,##0 "đ"').setBackground('#fffbeb');
  for (let r = 4; r <= 6; r++) s.getRange(r, 3).setBackground('#fed7d7');
  ui.alert('✅ Đã đặt lại tất cả về 0!');
}

function openHuongDan() {
  SpreadsheetApp.getUi().alert(
    '📖 HƯỚNG DẪN SỬ DỤNG — PHÚ YÊN 2026\n' +
    '══════════════════════════════\n\n' +
    '🤖 TELEGRAM BOT\n' +
    '• Nhắn: 500k ăn tối  |  1.5tr tiền phòng  |  24/5 - 300k xăng\n' +
    '• Gửi ảnh hoá đơn → bot tự đọc số tiền\n' +
    '• /xem  /tong  /baocao  /id\n\n' +
    '📋 CÁC SHEET\n' +
    '• ⚙️ Bot Config → token + danh sách thành viên\n' +
    '• 💵 Góp Tiền Trước → khoản đã góp ban đầu\n' +
    '• 📋 Chi Tiêu → nhập tay hoặc qua bot\n' +
    '• 📊 Tổng Hợp → quyết toán tự động\n' +
    '• 🌤️ Thời Tiết → cập nhật 5h sáng\n\n' +
    '⚙️ CÀI ĐẶT (admin, 1 lần)\n' +
    '1. BotFather → lấy token → paste vào Bot Config B4\n' +
    '2. Thành viên nhắn /id → copy vào cột B Bot Config\n' +
    '3. Triển khai Web App → copy URL\n' +
    '4. Menu → 🔗 Cài đặt Webhook\n' +
    '5. Menu → ⏰ Bật 5h sáng  +  🔔 Bật nhắc 20h tối\n\n' +
    '⚠️ Sau mỗi lần deploy mới → cài lại Webhook!'
  );
}

// ════════════════════════════════════════════════════════
//  SHEET QUÁN ĂN
//  Cột: STT | Tên quán | Khu vực | Loại | Giá(k/ng) | Lat | Lon | Trên đường về | Ghi chú
// ════════════════════════════════════════════════════════
function makeQuanAnSheet(ss) {
  let s = ss.getSheetByName('Quán Ăn');
  const isNew = !s;
  if (isNew) s = ss.insertSheet('Quán Ăn');

  let savedRows = null;
  if (!isNew && s.getLastRow() > 1)
    savedRows = s.getRange(2, 1, s.getLastRow() - 1, 9).getValues();

  try { const f = s.getFilter(); if (f) f.remove(); } catch(e) {}
  s.clear();
  s.getRange('A1').setValue('🍜 DANH SÁCH QUÁN ĂN PHÚ YÊN').setFontSize(13).setFontWeight('bold');
  s.getRange('A1:I1').merge();
  s.getRange('A2:I2')
    .setValues([['STT','Tên quán','Khu vực','Loại','Giá (k/ng)','Lat','Lon','Đường về','Ghi chú']])
    .setBackground('#2d3748').setFontColor('#fff').setFontWeight('bold').setHorizontalAlignment('center');

  const defaults = [
    [1,'Quán Bún Cá Ngừ Bà Hai','Tuy Hòa','🍜 Bún/Mì',40,13.0982,109.2970,'✅','Must try — cá ngừ đại dương tươi'],
    [2,'Bánh Căn Ngọc Lan','Tuy Hòa','🥞 Bánh',30,13.0962,109.2958,'✅','Sáng sớm 6h–9h'],
    [3,'Bún Sứa Đặc Sản','Tuy Hòa','🍜 Bún/Mì',35,13.0935,109.2962,'✅','Phải thử ở Phú Yên'],
    [4,'Bánh Hỏi Lòng Heo','Tuy Hòa','🍽️ Đặc sản',45,13.0948,109.2975,'✅',''],
    [5,'Mì Quảng Bà Mua','Tuy Hòa','🍜 Bún/Mì',35,13.0965,109.2980,'✅',''],
    [6,'Hải Sản Sông Biển','Tuy Hòa','🦞 Hải sản',150,13.0945,109.3150,'✅','Tôm hùm, mực nướng'],
    [7,'Sò Huyết Ô Loan','Sông Cầu','🦞 Hải sản',80,13.4200,109.2500,'','Gần Đầm Ô Loan — đặc sản'],
    [8,'Tôm Hùm Sông Cầu','Sông Cầu','🦞 Hải sản',200,13.4050,109.2420,'','Ngon nhất vùng'],
    [9,'Quán Hải Sản Gành Đá Đĩa','Sông Cầu','🦞 Hải sản',120,14.3880,109.2160,'','Gần Gành Đá Đĩa'],
    [10,'Cafe Biển Bãi Xép','Bãi Xép','☕ Cà phê',30,13.0150,109.3280,'','View biển đẹp'],
  ];

  const rows = savedRows || defaults;
  s.getRange(3, 1, rows.length, 9).setValues(rows);
  s.getRange(3, 5, rows.length, 1).setNumberFormat('#,##0 "k"');
  s.getRange(3, 6, rows.length, 2).setNumberFormat('0.0000').setFontColor('#a0aec0');

  // Alternate row colors
  for (let r = 3; r < 3 + rows.length; r++)
    if (r % 2 === 1) s.getRange(r, 1, 1, 9).setBackground('#f7fafc');

  s.getRange(3, 8, rows.length, 1).setHorizontalAlignment('center');
  [45,200,100,100,90,80,80,100,220].forEach((w,i) => s.setColumnWidth(i+1,w));
  s.setFrozenRows(2);

  if (!isNew && savedRows)
    s.getRange(3, 6, rows.length, 2).setNumberFormat('0.0000').setFontColor('#a0aec0');
}

// ════════════════════════════════════════════════════════
//  SHEET PHẢI ĐEM
//  Cột: STT | Đồ vật | Nhóm | Số lượng | Đã đem (checkbox) | Ghi chú
// ════════════════════════════════════════════════════════
function makePhaIDemSheet(ss) {
  let s = ss.getSheetByName('Phải Đem');
  const isNew = !s;
  if (isNew) s = ss.insertSheet('Phải Đem');

  let savedRows = null;
  if (!isNew && s.getLastRow() > 2)
    savedRows = s.getRange(3, 1, s.getLastRow() - 2, 6).getValues();

  try { const f = s.getFilter(); if (f) f.remove(); } catch(e) {}
  s.clear();
  s.getRange('A1').setValue('📦 DANH SÁCH ĐỒ CẦN ĐEM').setFontSize(13).setFontWeight('bold');
  s.getRange('A1:F1').merge();
  s.getRange('A2').setValue('💡 Tick ô "Đã đem" để đánh dấu — hoặc nhắn bot: "đã đem ô, thuốc, kem chống nắng"')
    .setFontColor('#718096').setFontStyle('italic').setFontSize(9);
  s.getRange('A2:F2').merge().setBackground('#ebf8ff');
  s.getRange('A3:F3')
    .setValues([['STT','Đồ vật','Nhóm phụ trách','Số lượng','Đã đem','Ghi chú']])
    .setBackground('#2d3748').setFontColor('#fff').setFontWeight('bold').setHorizontalAlignment('center');

  const defaults = [
    [1,'Kem chống nắng SPF50+','Nhóm LV','2 chai',false,'Cho bé + người lớn — BẮT BUỘC'],
    [2,'Áo phao trẻ em','Nhóm LV','1',false,'BẮT BUỘC khi tắm biển'],
    [3,'Thuốc hạ sốt (Paracetamol)','Nhóm LV','1 hộp',false,''],
    [4,'Thuốc say xe','Nhóm LV','1 hộp',false,'Uống trước 30 phút'],
    [5,'Băng cứu thương','Nhóm LV','1 hộp',false,''],
    [6,'Thuốc tiêu chảy','Nhóm LV','1 hộp',false,''],
    [7,'Ô / dù (chống nắng + mưa)','Nhóm LH','2',false,''],
    [8,'Kính râm','Nhóm LH','Đủ dùng',false,''],
    [9,'Nón/mũ rộng vành','Nhóm LH','Đủ dùng',false,''],
    [10,'Dép biển / sandal','Nhóm LH','Đủ dùng',false,''],
    [11,'Đồ chơi / sách cho bé','Nhóm LH','Đủ',false,'Cho chặng đường dài'],
    [12,'Sạc điện thoại + cáp','Nhóm CM','Đủ',false,''],
    [13,'Powerbank','Nhóm CM','2',false,''],
    [14,'Túi lạnh đựng đồ uống','Nhóm CM','1',false,''],
    [15,'Tiền mặt dự phòng','Nhóm CM','Đủ',false,'ATM ít ở vùng biển'],
    [16,'Giấy tờ xe (đăng ký, bảo hiểm)','Nhóm LV','1 bộ',false,'BẮT BUỘC'],
    [17,'Quần áo đi biển','Chung','Đủ dùng',false,''],
    [18,'Túi nilon chống nước','Chung','Vài cái',false,'Cho điện thoại, giấy tờ'],
  ];

  const rows = savedRows || defaults;
  s.getRange(4, 1, rows.length, 6).setValues(rows);

  // Checkbox cho cột E (Đã đem)
  s.getRange(4, 5, rows.length, 1).setDataValidation(
    SpreadsheetApp.newDataValidation().requireCheckbox().build()
  ).setHorizontalAlignment('center');

  // Dropdown nhóm cột C
  s.getRange(4, 3, rows.length, 1).setDataValidation(
    SpreadsheetApp.newDataValidation()
      .requireValueInList(['Nhóm LV','Nhóm LH','Nhóm CM','Chung'], true)
      .build()
  );

  // Màu xen kẽ + highlight BẮT BUỘC
  for (let r = 4; r < 4 + rows.length; r++) {
    const note = String(s.getRange(r, 6).getValue());
    if (note.includes('BẮT BUỘC')) s.getRange(r, 1, 1, 6).setBackground('#fff5f5');
    else if (r % 2 === 0) s.getRange(r, 1, 1, 6).setBackground('#f7fafc');
  }

  [45,220,110,90,75,200].forEach((w,i) => s.setColumnWidth(i+1,w));
  s.setFrozenRows(3);
}

// ════════════════════════════════════════════════════════
//  THỜI TIẾT — Open-Meteo, lọc 23–27/05
// ════════════════════════════════════════════════════════
function fetchWeather() {
  const result = {};
  Object.entries(CFG.coords).forEach(([place, coord]) => {
    try {
      const url =
        `https://api.open-meteo.com/v1/forecast?latitude=${coord.lat}&longitude=${coord.lon}` +
        `&daily=weathercode,temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max,uv_index_max` +
        `&timezone=Asia%2FHo_Chi_Minh&start_date=${CFG.tripStart}&end_date=${CFG.tripEnd}`;
      const res  = UrlFetchApp.fetch(url, { muteHttpExceptions: true });
      result[place] = JSON.parse(res.getContentText()).daily || null;
    } catch(e) { result[place] = null; }
  });
  return result;
}

function buildWeatherSheet(ss, weather) {
  let s = ss.getSheetByName('Thời Tiết') || ss.insertSheet('Thời Tiết');
  s.clear();
  s.getRange('A1').setValue('🌤️ DỰ BÁO THỜI TIẾT PHÚ YÊN — 23 đến 27/05/2026')
    .setFontSize(13).setFontWeight('bold');
  s.getRange('A1:H1').merge();
  s.getRange('A2').setValue(`Cập nhật: ${new Date().toLocaleString('vi-VN')}`)
    .setFontColor('#718096').setFontStyle('italic');
  s.getRange('A2:H2').merge();

  let row = 4;
  Object.entries(weather).forEach(([place, daily]) => {
    s.getRange(row,1).setValue(`📍 ${place}`);
    s.getRange(row,1,1,8).merge().setBackground('#2d3748').setFontColor('#fff').setFontWeight('bold');
    row++;
    s.getRange(row,1,1,8)
      .setValues([['Ngày','Thời tiết','Tmax','Tmin','Mưa (mm)','Gió (km/h)','UV','Đánh giá']])
      .setFontWeight('bold').setBackground('#edf2f7');
    row++;
    if (!daily) { s.getRange(row,1).setValue('❌ Không lấy được dữ liệu'); row+=2; return; }
    daily.time.forEach((d,i) => {
      const code   = daily.weathercode[i];
      const precip = daily.precipitation_sum[i] || 0;
      s.getRange(row,1,1,8).setValues([[
        CFG.days[i] || d,
        wxLabel(code),
        `${daily.temperature_2m_max[i]}°C`,
        `${daily.temperature_2m_min[i]}°C`,
        precip.toFixed(1),
        daily.windspeed_10m_max[i] || '—',
        daily.uv_index_max ? (daily.uv_index_max[i] || '—') : '—',
        wxOk(code, precip),
      ]]);
      if (i%2===0) s.getRange(row,1,1,8).setBackground('#f7fafc');
      row++;
    });
    row++;
  });
  [130,170,65,65,90,90,60,110].forEach((w,i) => s.setColumnWidth(i+1,w));
  s.setFrozenRows(1);
}

// ════════════════════════════════════════════════════════
//  ĐỌC TẤT CẢ SHEET KẾ HOẠCH
// ════════════════════════════════════════════════════════
function readAllPlanSheets(ss) {
  const result = {};
  ss.getSheets()
    .filter(sh => !CFG.skipSheets.includes(sh.getName()))
    .forEach(sh => {
      const vals = sh.getDataRange().getValues();
      if (vals.length > 1 || (vals.length===1 && vals[0].some(c=>c!=='')))
        result[sh.getName()] = vals.map(r=>r.join(' | ')).join('\n');
    });
  return result;
}

// ════════════════════════════════════════════════════════
//  PHÂN TÍCH & GỢI Ý
// ════════════════════════════════════════════════════════
function weatherByDay(weather) {
  const byDay = {};
  CFG.days.forEach((label, i) => {
    byDay[label] = {};
    Object.entries(weather).forEach(([place, daily]) => {
      if (!daily) return;
      byDay[label][place] = {
        label : wxLabel(daily.weathercode[i]),
        ok    : wxOk(daily.weathercode[i], daily.precipitation_sum[i]||0),
        tmax  : daily.temperature_2m_max[i],
        tmin  : daily.temperature_2m_min[i],
        precip: daily.precipitation_sum[i] || 0,
      };
    });
  });
  return byDay;
}

function analyzeWithGemini(planData, weather) {
  const planText = Object.entries(planData)
    .map(([name, content]) => `=== Sheet: ${name} ===\n${content}`).join('\n\n');
  const wxText = Object.entries(weather).map(([place, daily]) => {
    if (!daily) return `${place}: N/A`;
    return `${place}:\n` + daily.time.map((d,i) =>
      `  ${CFG.days[i]}: ${wxLabel(daily.weathercode[i])}, ${daily.temperature_2m_max[i]}°C, mưa ${(daily.precipitation_sum[i]||0).toFixed(1)}mm`
    ).join('\n');
  }).join('\n\n');

  const prompt =
    `Bạn là chuyên gia du lịch Việt Nam. Phân tích kế hoạch và gợi ý chi tiết cho chuyến đi:\n` +
    `- ${CFG.groupSize} người (1 bé ${CFG.childAge} tuổi), mục tiêu DU LỊCH NGHỈ DƯỠNG gia đình\n` +
    `- Xe: ${CFG.car}\n- Thời gian: 5 ngày (23–27/05/2026)\n\n` +
    `DỮ LIỆU CÁC SHEET:\n${planText||'(chưa có)'}\n\n` +
    `DỰ BÁO THỜI TIẾT:\n${wxText}\n\n` +
    `Viết tiếng Việt, chi tiết TỪNG NGÀY (23→27/05). Mỗi ngày gồm:\n` +
    `1. Thời tiết & cảnh báo\n2. Lịch trình sáng/trưa/chiều/tối\n` +
    `3. Ăn uống (gợi ý thêm ngoài kế hoạch)\n4. Di chuyển & đổ dầu\n` +
    `5. Lưu ý bé ${CFG.childAge} tuổi\nCuối: đặc sản mua về, trạm dầu, chi phí dự kiến.`;

  try {
    const res = UrlFetchApp.fetch(
      `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${CFG.geminiApiKey}`,
      { method:'post', contentType:'application/json',
        payload: JSON.stringify({ contents:[{ parts:[{ text:prompt }] }] }),
        muteHttpExceptions:true }
    );
    const text = JSON.parse(res.getContentText()).candidates?.[0]?.content?.parts?.[0]?.text;
    return text || analyzeBuiltIn({}, weather);
  } catch(e) { return analyzeBuiltIn({}, weather); }
}

function analyzeBuiltIn(planData, weather) {
  const wbd   = weatherByDay(weather);
  const lines = [];

  const PLAN = [
    { day: CFG.days[0], theme: 'XUẤT PHÁT → ĐẾN TUY HÒA',
      note: 'Ngày di chuyển — khởi hành sớm 5h–6h tránh nắng và kẹt xe',
      morning  : ['Khởi hành 5h–6h sáng','Ăn sáng dọc QL1A hoặc thị xã Sông Cầu','Đổ đầy dầu trước khi vào Tuy Hòa (Petrolimex Sông Cầu)'],
      afternoon: ['Nhận phòng (check-in từ 14h)','Nghỉ ngơi, cho bé ngủ trưa','Tắm biển nhẹ tại bãi biển Tuy Hòa (16h–18h)'],
      evening  : ['Dạo phố Trần Phú','Ăn tối hải sản: bún cá ngừ, gỏi cá mai','Thử bánh tráng nướng đường phố'],
      food     : ['Sáng: bánh mì / bún bò ven QL1A','Trưa: cơm hộp mang theo','Tối: nhà hàng hải sản Tuy Hòa — cá ngừ đại dương must-try'],
      child    : ['Cho bé ăn no trước khi lên xe','Dừng nghỉ mỗi 2h','Mang đồ chơi / máy tính bảng cho bé trong xe'],
      drive    : ['HCM → Tuy Hòa: ~550km, 8–9h lái','Nhiên liệu: ~40–50L dầu ≈ 1.000.000–1.200.000đ','Trạm dầu: Bình Thuận, Ninh Thuận, Sông Cầu'] },

    { day: CFG.days[1], theme: 'GÀNH ĐÁ ĐĨA + VỊNH HÒA',
      note: 'Đi sáng sớm tránh đông và nắng gắt',
      morning  : ['5h30: xuất phát (Gành Đá Đĩa cách TH ~90km)','7h–9h: tham quan Gành Đá Đĩa (đá cột basalt — Di sản địa chất quốc gia)','Chú ý: bề mặt đá trơn, bồng hoặc cầm tay bé'],
      afternoon: ['10h–11h: Hòn Yến (san hô đẹp tháng 5)','11h30: ăn trưa Sông Cầu — sò huyết Ô Loan nướng','13h–15h: nghỉ ngơi','15h30–17h30: Vịnh Hòa — bãi biển ít người'],
      evening  : ['Ăn hải sản Sông Cầu: tôm hùm bông, mực nướng, ốc','Hoặc về Tuy Hòa ăn tối'],
      food     : ['Sáng: bánh căn + chả cá Tuy Hòa','Trưa: sò huyết Ô Loan — đặc sản Sông Cầu','Tối: cá ngừ đại dương câu tay'],
      child    : ['Đeo giày đế cao su cho bé tại Gành Đá Đĩa','Kem chống nắng SPF50+ + áo dài tay','Tránh để bé đứng sát mép đá'],
      drive    : ['Tuy Hòa → Gành Đá Đĩa: ~90km, 1.5h','Đổ dầu tại Petrolimex Sông Cầu'] },

    { day: CFG.days[2], theme: 'MŨI ĐIỆN / ĐẠI LÃNH + BÃI XÉP',
      note: 'Xuất phát rất sớm để xem BÌNH MINH tại cực Đông Việt Nam',
      morning  : ['4h30: xuất phát đến Mũi Điện','5h30–7h: BÌNH MINH tại Mũi Điện — đón mặt trời mọc đầu tiên VN','7h30: Bãi Môn — bãi biển hoang sơ nước trong xanh','9h: về nghỉ, ăn sáng muộn'],
      afternoon: ['11h–13h: ăn trưa + nghỉ trưa (quan trọng với bé)','14h30–16h30: Bãi Xép — bãi trong phim "Hoa Vàng Trên Cỏ Xanh" (sóng nhỏ, an toàn cho bé)','17h: về khách sạn'],
      evening  : ['Ăn tối nhẹ gần khách sạn: bún sứa, bánh hỏi thịt nướng','Mua đặc sản: cá bò khô, cá ngừ khô, mực khô'],
      food     : ['Sáng: cafe + bánh mì mang theo (xuất phát sớm)','Trưa: bún sứa Phú Yên','Tối: bánh hỏi lòng heo'],
      child    : ['Mặc thêm áo sáng sớm tại Mũi Điện (lạnh)','Bãi Xép sóng nhỏ — an toàn cho bé tắm','Hôm nay dậy sớm → cho bé ngủ trưa bù'],
      drive    : ['TH → Mũi Điện: ~40km, 1h','Đường vào nhỏ — Carnival đi được, chạy chậm'] },

    { day: CFG.days[3], theme: 'ĐẦM Ô LOAN + THÁP NHẠN + THỰ GIÃN',
      note: 'Ngày thư giãn — phù hợp nghỉ ngơi và khám phá thành phố',
      morning  : ['7h–9h: Tháp Nhạn (tháp Chăm, view đẹp)','9h30–11h: Đầm Ô Loan — thuyền kayak ~50–100k/người (phù hợp bé)'],
      afternoon: ['11h30: ăn trưa','13h–16h: TỰ DO — hồ bơi khách sạn (bé rất thích)','16h–18h: Chợ Tuy Hòa — mua đặc sản mang về'],
      evening  : ['Bữa tối ĐẶC BIỆT: cá ngừ đại dương câu tay (sashimi / nướng / kho)'],
      food     : ['Sáng: chè Phú Yên, bánh căn','Trưa: cơm hến, cơm niêu','Tối: tiệc hải sản — bữa đáng nhất chuyến đi'],
      child    : ['Ngày thư giãn — tốt cho bé phục hồi','Hồ bơi: mang theo phao bơi cho bé','Đổ đầy dầu hôm nay chuẩn bị ngày về'],
      drive    : ['Di chuyển nội thành, khoảng cách ngắn','Đổ đầy dầu buổi chiều chuẩn bị ngày về'] },

    { day: CFG.days[4], theme: 'VỀ NHÀ',
      note: 'Khởi hành sớm 7h–8h tránh nắng và kẹt xe',
      morning  : ['6h: ăn sáng lần cuối — bún cá ngừ / mì Quảng','7h: check-out','7h–8h: chợ Tuy Hòa mua đặc sản lần cuối','8h30: đổ đầy dầu rồi lên đường'],
      afternoon: ['Dừng ăn trưa tại Phan Rang hoặc Phan Thiết','Nghỉ 30 phút cho bé vận động'],
      evening  : ['Dự kiến về nhà 17h–19h'],
      food     : ['Sáng: bún cá ngừ lần cuối','Trưa: quán ven QL1A'],
      child    : ['Chuẩn bị đồ chơi / sách cho chặng về','Cho bé ăn no, uống đủ nước'],
      drive    : ['Đổ đầy dầu tại Tuy Hòa','Nhiên liệu về: ~40–50L ≈ 1.000.000–1.200.000đ','Tổng nhiên liệu cả chuyến: ~2.200.000–2.600.000đ'] },
  ];

  lines.push('══════════════════════════════════════════════════════');
  lines.push('GỢI Ý LỊCH TRÌNH — PHÚ YÊN 2026');
  lines.push(`Nhóm LV · Nhóm LH · Nhóm CM  |  ${CFG.groupSize} người · 1 bé ${CFG.childAge} tuổi · ${CFG.car}`);
  lines.push(`Cập nhật: ${new Date().toLocaleString('vi-VN')}`);
  lines.push('══════════════════════════════════════════════════════');

  PLAN.forEach((day, idx) => {
    lines.push('');
    lines.push(`━━━ NGÀY ${idx+1}: ${day.day} — ${day.theme} ━━━`);
    lines.push(`📌 ${day.note}`);
    lines.push('');
    lines.push('🌤️ THỜI TIẾT:');
    const wx = wbd[day.day] || {};
    if (!Object.keys(wx).length) { lines.push('  (Chưa có dữ liệu)'); }
    else {
      Object.entries(wx).forEach(([place, w]) =>
        lines.push(`  📍 ${place}: ${w.label} · ${w.tmax}°C/${w.tmin}°C · Mưa ${w.precip.toFixed(1)}mm · ${w.ok}`)
      );
      if (Object.values(wx).some(w=>w.label.includes('Giông')))
        lines.push('  ⛈️ CẢNH BÁO GIÔNG — cân nhắc thay đổi hoạt động ngoài trời!');
      else if (Object.values(wx).some(w=>w.precip>10))
        lines.push('  ☂️ Có mưa — mang áo mưa, cân nhắc thời điểm đi ngoài trời');
    }
    lines.push('');
    lines.push('📋 LỊCH TRÌNH:');
    lines.push('  🌅 Sáng:');    day.morning.forEach(m   => lines.push(`    • ${m}`));
    lines.push('  ☀️ Chiều:');   day.afternoon.forEach(a => lines.push(`    • ${a}`));
    lines.push('  🌙 Tối:');     day.evening.forEach(e   => lines.push(`    • ${e}`));
    lines.push('');
    lines.push('🍜 ĂN UỐNG:');   day.food.forEach(f  => lines.push(`  • ${f}`));
    lines.push('');
    lines.push(`🚗 DI CHUYỂN:`); day.drive.forEach(d => lines.push(`  • ${d}`));
    lines.push('');
    lines.push(`👶 LƯU Ý BÉ:`); day.child.forEach(c => lines.push(`  • ${c}`));
  });

  if (Object.keys(planData).length > 0) {
    lines.push('');
    lines.push('══════════════════════════════════════════════════════');
    lines.push('📊 DỮ LIỆU TỪ CÁC SHEET KẾ HOẠCH');
    lines.push('══════════════════════════════════════════════════════');
    Object.entries(planData).forEach(([name, content]) => {
      lines.push(''); lines.push(`📄 ${name}`);
      content.split('\n').slice(0,30).forEach(l => lines.push(`  ${l}`));
    });
  }

  lines.push('');
  lines.push('══════════════════════════════════════════════════════');
  lines.push('🛍️ ĐẶC SẢN MUA VỀ');
  lines.push('══════════════════════════════════════════════════════');
  ['Cá ngừ đại dương khô / sốt','Cá bò khô tẩm gia vị','Mực khô Phú Yên',
   'Ruốc / mắm nhĩ','Bánh tráng nướng','Nước mắm Phú Yên']
    .forEach(i => lines.push(`  • ${i}`));

  lines.push('');
  lines.push('══════════════════════════════════════════════════════');
  lines.push('⛽ TRẠM DẦU DIESEL TRÊN TUYẾN');
  lines.push('══════════════════════════════════════════════════════');
  ['Petrolimex Sông Cầu (Bình Định) — trước Gành Đá Đĩa',
   'Petrolimex Tuy Hòa — đường Trần Phú','Phan Rang (về)','Phan Thiết (về)',
   'Mẹo: đổ đầy bình mỗi tối hoặc trước chặng > 100km']
    .forEach(i => lines.push(`  • ${i}`));

  lines.push('');
  lines.push('══════════════════════════════════════════════════════');
  lines.push('💰 CHI PHÍ DỰ KIẾN (7 người)');
  lines.push('══════════════════════════════════════════════════════');
  [['Khách sạn (4 đêm)','3.000.000 – 6.000.000đ'],
   ['Ăn uống (5 ngày)','3.500.000 – 6.000.000đ'],
   ['Xăng dầu (khứ hồi)','2.200.000 – 2.600.000đ'],
   ['Vé tham quan','500.000 – 1.000.000đ'],
   ['Mua sắm đặc sản','500.000 – 1.500.000đ'],
   ['Dự phòng','1.000.000đ'],
   ['TỔNG DỰ KIẾN','~11 – 18 triệu đồng']]
    .forEach(([c,e]) => lines.push(`  ${c.padEnd(25)}: ${e}`));

  lines.push('');
  lines.push('✏️ Chỉnh sửa trực tiếp trong sheet này theo tình hình thực tế.');
  lines.push('💡 Thêm Gemini API key vào CFG.geminiApiKey để nhận gợi ý AI chi tiết hơn (miễn phí tại aistudio.google.com)');

  return lines.join('\n');
}

function buildSuggestionSheet(ss, text) {
  let s = ss.getSheetByName('Gợi Ý Lịch Trình') || ss.insertSheet('Gợi Ý Lịch Trình');
  try { const f = s.getFilter(); if (f) f.remove(); } catch(e) {}
  s.clear();
  s.setColumnWidth(1, 680);
  text.split('\n').forEach((line, i) => {
    const cell = s.getRange(i+1, 1);
    cell.setValue(line).setWrap(true);
    if (line.startsWith('══'))      cell.setFontWeight('bold').setBackground('#2d3748').setFontColor('#fff').setFontSize(11);
    else if (line.startsWith('━━')) cell.setFontWeight('bold').setBackground('#4a5568').setFontColor('#fff').setFontSize(11);
    else if (line.match(/^[🌤️📋🍜🚗👶🛍️⛽💰📊📌]/u)) cell.setFontWeight('bold').setBackground('#edf2f7');
    else if (line.match(/^[🌅☀️🌙]/u)) cell.setFontWeight('bold').setBackground('#f7fafc');
    else if (line.includes('⛈️')||line.includes('☂️')) cell.setBackground('#fff5f5').setFontColor('#c53030').setFontWeight('bold');
    else if (line.startsWith('  •')||line.startsWith('    •')) cell.setFontColor('#4a5568');
  });
}

// ════════════════════════════════════════════════════════
//  TELEGRAM BOT — CẤU HÌNH QUA SHEET
// ════════════════════════════════════════════════════════
function setupBotConfigSheet() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let s = ss.getSheetByName('⚙️ Bot Config') || ss.insertSheet('⚙️ Bot Config');
  try { const f = s.getFilter(); if (f) f.remove(); } catch(e) {}
  s.clear();

  s.getRange('A1').setValue('⚙️ CÀI ĐẶT TELEGRAM BOT').setFontSize(13).setFontWeight('bold');
  s.getRange('A1:E1').merge();

  s.getRange('A3:E3').merge().setBackground('#2d3748').setFontColor('#fff').setFontWeight('bold').setValue('🔑 BOT TOKEN');
  s.getRange('A4').setValue('Token').setFontWeight('bold');
  s.getRange('B4:E4').merge().setValue('PASTE_TOKEN_VÀO_ĐÂY').setBackground('#fffbeb').setFontColor('#c05621');
  s.getRange('A5').setValue('Tên bot').setFontWeight('bold');
  s.getRange('B5:E5').merge().setValue('PhuYen2026Bot').setFontColor('#718096');
  s.getRange('A6').setValue('Web App URL').setFontWeight('bold');
  s.getRange('B6:E6').merge().setValue('PASTE_WEB_APP_URL_VÀO_ĐÂY').setBackground('#ebf8ff').setFontColor('#2b6cb0')
    .setNote('Apps Script → Deploy → Manage deployments → copy URL (dạng .../exec)');

  s.getRange('A7:E7').merge().setBackground('#2d3748').setFontColor('#fff').setFontWeight('bold').setValue('⚙️ CÀI ĐẶT CHUNG');
  s.getRange('A8').setValue('Nhóm mặc định').setFontWeight('bold');
  s.getRange('B8').setValue('Nhóm LV').setBackground('#fffbeb')
    .setNote('Nhóm gán khi không nhận ra tài khoản');
  s.getRange('B8').setDataValidation(
    SpreadsheetApp.newDataValidation().requireValueInList(['Nhóm LV','Nhóm LH','Nhóm CM'],true).build()
  );

  s.getRange('A11:E11').merge().setBackground('#2d3748').setFontColor('#fff').setFontWeight('bold').setValue('👥 DANH SÁCH THÀNH VIÊN');
  s.getRange('A12:E12').setValues([['Username Telegram','Telegram User ID','Tên hiển thị','Nhóm','Ghi chú']])
    .setBackground('#edf2f7').setFontWeight('bold');
  s.getRange('A13:E15').setValues([
    ['liemdo28','','Liem Do','Nhóm LV','Admin'],
    ['user_lh', '','Người LH','Nhóm LH',''],
    ['user_cm', '','Người CM','Nhóm CM','Đã góp 15tr'],
  ]);
  s.getRange('D13:D50').setDataValidation(
    SpreadsheetApp.newDataValidation().requireValueInList(['Nhóm LV','Nhóm LH','Nhóm CM'],true).build()
  );
  s.getRange('A13:A50').setFontColor('#2b6cb0');
  s.getRange('B13:B50').setNumberFormat('@');
  for (let r=13;r<=25;r++) if(r%2===0) s.getRange(r,1,1,5).setBackground('#f7fafc');

  s.getRange('A52:E52').merge().setBackground('#e6ffed').setWrap(true).setFontStyle('italic').setFontColor('#276749')
    .setValue('💡 Lấy User ID: nhắn /id vào bot, bot tự reply ID của bạn — copy paste vào cột B');
  s.getRange('A53:E53').merge().setBackground('#ebf8ff').setWrap(true).setFontStyle('italic').setFontColor('#2c5282')
    .setValue('💡 Username: Telegram → Settings → Username (không gõ dấu @). User ID ổn định hơn username.');
  s.setRowHeight(52,40); s.setRowHeight(53,40);

  [160,140,140,110,180].forEach((w,i) => s.setColumnWidth(i+1,w));
  ss.setActiveSheet(s); ss.moveActiveSheet(1);
  SpreadsheetApp.getUi().alert('✅ Đã tạo sheet "⚙️ Bot Config"!\n\n1. Paste token vào ô B4\n2. Điền username/ID thành viên\n3. Deploy Web App → Cài đặt Webhook');
}

function loadConfig() {
  const s = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('⚙️ Bot Config');
  if (!s) throw new Error('Chưa tạo Bot Config. Chạy setupBotConfigSheet() trước.');
  const token      = getBotToken(true);
  const defaultGrp = String(s.getRange('B8').getValue()).trim() || 'Nhóm LV';
  const rows       = s.getRange('A13:D62').getValues();
  const byUsername = {}, byUserId = {};
  rows.forEach(([uname, uid, displayName, group]) => {
    if (!group) return;
    const info = { group: String(group).trim(), name: String(displayName).trim() };
    if (uname) byUsername[String(uname).trim().toLowerCase()] = info;
    if (uid)   byUserId[String(uid).trim()] = info;
  });
  return { token, defaultGrp, byUsername, byUserId };
}

function getBotToken(forceRefresh) {
  const cache = CacheService.getScriptCache();
  if (!forceRefresh) {
    const cached = cache.get('tg_bot_token');
    if (cached) return cached;
  }

  const props = PropertiesService.getScriptProperties();
  if (!forceRefresh) {
    const saved = props.getProperty('tg_bot_token');
    if (saved) {
      cache.put('tg_bot_token', saved, 21600);
      return saved;
    }
  }

  const s = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('⚙️ Bot Config');
  if (!s) throw new Error('Chưa tạo Bot Config. Chạy setupBotConfigSheet() trước.');
  const token = String(s.getRange('B4').getValue()).trim();
  if (!token) throw new Error('Chưa nhập Telegram Bot Token trong sheet "⚙️ Bot Config".');

  props.setProperty('tg_bot_token', token);
  cache.put('tg_bot_token', token, 21600);
  return token;
}

function doPost(e) {
  try {
    const update = JSON.parse(e.postData.contents);
    logTelegramEvent_('incoming_update', update);
    if (!update || !update.message) {
      return ContentService.createTextOutput('OK');
    }
    if (isIgnorableTelegramMessage_(update.message)) {
      logTelegramEvent_('ignored_message', update);
      return ContentService.createTextOutput('OK');
    }
    if (isDuplicateTelegramUpdate(update)) {
      logTelegramEvent_('duplicate_update', update);
      return ContentService.createTextOutput('OK');
    }
    if (isRateLimitedTelegramMessage_(update.message)) {
      logTelegramEvent_('rate_limited', update);
      maybeSendRateLimitNotice_(update.message);
      return ContentService.createTextOutput('OK');
    }
    handleMessage(update.message);
  } catch(err) { Logger.log(err); }
  return ContentService.createTextOutput('OK');
}

function isIgnorableTelegramMessage_(msg) {
  if (!msg || !msg.from) return true;
  if (msg.from.is_bot === true) return true;
  if (msg.via_bot) return true;
  if (msg.new_chat_members || msg.left_chat_member) return true;
  if (msg.group_chat_created || msg.supergroup_chat_created || msg.channel_chat_created) return true;
  return false;
}

function isDuplicateTelegramUpdate(update) {
  const updateId = Number(update && update.update_id);
  const msg = update && update.message;
  const fingerprint = msg
    ? [
        String(updateId || ''),
        String(msg.chat && msg.chat.id || ''),
        String(msg.message_id || ''),
        String(msg.date || ''),
        String((msg.text || msg.caption || '').trim().toLowerCase()),
      ].join(':')
    : '';
  if (!Number.isFinite(updateId) && !fingerprint) return false;

  const cache = CacheService.getScriptCache();
  const keys = [];

  if (Number.isFinite(updateId)) {
    keys.push(`tg_upd_${updateId}`);
  }
  if (fingerprint) {
    const digest = Utilities.base64EncodeWebSafe(
      Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, fingerprint)
    );
    keys.push(`tg_fp_${digest}`);
  }

  if (keys.some(key => cache.get(key))) return true;
  keys.forEach(key => cache.put(key, '1', 21600));
  return false;
}

function isRateLimitedTelegramMessage_(msg) {
  const userId = String(msg && msg.from && msg.from.id || '');
  const chatId = String(msg && msg.chat && msg.chat.id || '');
  const text   = String(msg && (msg.text || msg.caption) || '').trim().toLowerCase();
  if (!userId || !chatId) return false;

  const key = ['tg_rl', chatId, userId, text || '__nontext__'].join(':');
  const cache = CacheService.getScriptCache();
  const current = Number(cache.get(key) || '0');
  const limit = text === '/start' ? 1 : 3;
  if (current >= limit) return true;
  cache.put(key, String(current + 1), 10);
  return false;
}

function maybeSendRateLimitNotice_(msg) {
  const chatId = String(msg && msg.chat && msg.chat.id || '');
  const text   = String(msg && (msg.text || msg.caption) || '').trim().toLowerCase();
  if (!chatId) return;

  let token;
  try { token = getBotToken(); } catch (e) { Logger.log(e); return; }

  const cache = CacheService.getScriptCache();
  const noticeKey = ['tg_rl_notice', chatId, text || '__nontext__'].join(':');
  if (cache.get(noticeKey)) return;
  cache.put(noticeKey, '1', 10);

  const reply = text === '/start'
    ? 'Mình vừa xử lý `/start` rồi. Đợi vài giây rồi nhắn lại nhé.'
    : 'Mình vừa nhận lệnh này rồi. Đợi 5–10 giây rồi thử lại nhé.';
  sendTG(token, Number(chatId), reply);
}

function handleMessage(msg) {
  const chatId   = msg.chat.id;
  const from     = msg.from;
  const userId   = String(from.id || '');
  const username = (from.username || '').toLowerCase().trim();
  const firstName= from.first_name || '';
  const text     = (msg.text || '').trim();
  const isHelpCommand = text === '/start' || text === '/help';
  const isIdCommand   = text === '/id';

  if (isHelpCommand || isIdCommand) {
    let token;
    try { token = getBotToken(); } catch(err) { Logger.log(err); return; }

    if (isHelpCommand) {
      sendTG(token, chatId,
        `👋 Xin chào ${firstName}!\n\n` +
        `💰 <b>Ghi chi tiêu:</b>\n• 500k ăn tối  |  1.5tr tiền phòng  |  24/5 - 300k xăng\n• 📸 Gửi ảnh hoá đơn → bot tự đọc\n\n` +
        `🍜 <b>Tìm quán ăn</b> (gửi 📍 vị trí trước):\n• quán gần tôi nhất\n• trên đường về, quán nào ngon\n\n` +
        `📦 <b>Đồ cần đem:</b>\n• danh sách cần đem  |  còn gì chưa đem\n• đã đem ô, thuốc, kem chống nắng\n\n` +
        `/xem  /tong  /baocao  /id\n\n` +
        `<i>build ${CFG.botBuild}</i>`
      );
      return;
    }

    sendTG(token, chatId,
      `🪪 Thông tin:\n\nUsername: @${username||'(chưa có)'}\nUser ID: <code>${userId}</code>\n\nCopy ID → paste vào cột B sheet "⚙️ Bot Config"\n\n<i>build ${CFG.botBuild}</i>`
    );
    return;
  }

  let cfg;
  try { cfg = loadConfig(); } catch(err) { Logger.log(err); return; }
  if (text === '/xem')    { sendRecentExpenses(cfg, chatId); return; }
  if (text === '/tong')   { sendSummary(cfg, chatId); return; }
  if (text === '/baocao') { sendDailyReport(cfg, chatId); return; }

  // Ảnh hoá đơn
  if (msg.photo) { handlePhoto(msg, cfg); return; }

  // Vị trí (Location pin)
  if (msg.location) { handleLocation(msg, cfg); return; }

  const t = text.toLowerCase();

  // Quán ăn — phải kiểm tra trước expense vì có chữ "ăn"
  if (/tìm quán|quán gần|gần nhất|đường về|trên đường.*quán|quán.*ngon|nhà hàng gần/.test(t)) {
    handleRestaurantQuery(msg, cfg); return;
  }

  // Đồ cần đem
  if (/^đã đem|chưa đem|còn thiếu|còn gì.*đem|danh sách.*đem|cần đem|phải đem|đem theo|list đem/.test(t)) {
    handlePackingQuery(msg, cfg, text); return;
  }

  const userInfo =
    (userId   && cfg.byUserId[userId])   ||
    (username && cfg.byUsername[username]) ||
    (firstName&& cfg.byUsername[firstName.toLowerCase()]);

  if (!userInfo) {
    sendTG(cfg.token, chatId,
      `❓ Tài khoản chưa đăng ký.\n\nNhắn /id rồi báo admin thêm vào sheet <b>⚙️ Bot Config</b>.`
    );
    return;
  }

  const expense = parseTGExpense(text, userInfo.group);
  if (!expense) {
    sendTG(cfg.token, chatId,
      `❓ Không hiểu tin nhắn này.\n\n` +
      `💰 Ghi chi tiêu: <b>500k ăn tối</b>\n` +
      `🍜 Tìm quán: <b>quán gần tôi nhất</b>\n` +
      `📦 Đồ đem: <b>danh sách cần đem</b> / <b>còn gì chưa đem</b>\n` +
      `✅ Đánh dấu: <b>đã đem ô, thuốc, dép</b>`
    );
    return;
  }

  writeExpense(expense);
  sendTG(cfg.token, chatId,
    `✅ Đã ghi!\n\n📅 ${expense.dateStr}\n📝 ${expense.name}\n📂 ${expense.category}\n💰 ${fmtMoney(expense.amount)}\n👥 ${expense.group} (${userInfo.name})`
  );
}

// ════════════════════════════════════════════════════════
//  📸 ĐỌC HOÁ ĐƠN QUA GEMINI VISION
// ════════════════════════════════════════════════════════
function handlePhoto(msg, cfg) {
  const chatId = msg.chat.id;
  const from   = msg.from;
  const userId   = String(from.id || '');
  const username = (from.username || '').toLowerCase().trim();
  const firstName= from.first_name || '';

  if (!CFG.geminiApiKey) {
    sendTG(cfg.token, chatId,
      '❌ Chưa có Gemini API key.\n\nThêm key vào <code>CFG.geminiApiKey</code> trong Code.js (miễn phí tại aistudio.google.com)'
    );
    return;
  }

  sendTG(cfg.token, chatId, '🔍 Đang đọc hoá đơn...');

  try {
    // Lấy ảnh độ phân giải cao nhất
    const photo   = msg.photo[msg.photo.length - 1];
    const fileRes = UrlFetchApp.fetch(
      `https://api.telegram.org/bot${cfg.token}/getFile?file_id=${photo.file_id}`,
      { muteHttpExceptions: true }
    );
    const fileJson = JSON.parse(fileRes.getContentText());
    if (!fileJson.ok) { sendTG(cfg.token, chatId, '❌ Không tải được ảnh.'); return; }

    const imageBytes = UrlFetchApp.fetch(
      `https://api.telegram.org/file/bot${cfg.token}/${fileJson.result.file_path}`,
      { muteHttpExceptions: true }
    ).getContent();
    const base64Image = Utilities.base64Encode(imageBytes);

    const prompt =
      'Đây là ảnh hoá đơn/receipt. Đọc và trả lời ĐÚNG format sau (không thêm gì khác):\n' +
      'TÊN: [tên món/dịch vụ ngắn gọn tiếng Việt]\n' +
      'SỐ TIỀN: [chỉ số nguyên, không dấu phẩy không ký hiệu]\n' +
      'DANH MỤC: [một trong: ăn uống, lưu trú, di chuyển, xăng dầu, vui chơi, mua sắm, y tế, khác]\n' +
      'Nếu không đọc được số tiền, chỉ viết: KHÔNG RÕ';

    const gemRes  = UrlFetchApp.fetch(
      `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${CFG.geminiApiKey}`,
      {
        method: 'post', contentType: 'application/json',
        payload: JSON.stringify({ contents: [{ parts: [
          { text: prompt },
          { inline_data: { mime_type: 'image/jpeg', data: base64Image } }
        ]}]}),
        muteHttpExceptions: true,
      }
    );
    const result = JSON.parse(gemRes.getContentText()).candidates?.[0]?.content?.parts?.[0]?.text || '';

    if (!result || result.includes('KHÔNG RÕ')) {
      sendTG(cfg.token, chatId, '❓ Không đọc được số tiền từ ảnh.\nThử nhắn thủ công: <b>500k ăn tối</b>');
      return;
    }

    const nameMatch   = result.match(/TÊN:\s*(.+)/i);
    const amountMatch = result.match(/SỐ TIỀN:\s*([\d]+)/i);
    const catMatch    = result.match(/DANH MỤC:\s*(.+)/i);

    if (!amountMatch) {
      sendTG(cfg.token, chatId, `🤖 Gemini đọc được:\n<pre>${result}</pre>\n\n❓ Không parse được số tiền. Nhắn thủ công nhé.`);
      return;
    }

    const userInfo =
      (userId   && cfg.byUserId[userId])   ||
      (username && cfg.byUsername[username]) ||
      (firstName&& cfg.byUsername[firstName.toLowerCase()]) ||
      { group: cfg.defaultGrp, name: firstName || 'Unknown' };

    const amount  = parseInt(amountMatch[1]);
    const name    = nameMatch ? nameMatch[1].trim() : 'Chi tiêu từ hoá đơn';
    const catRaw  = catMatch  ? catMatch[1].trim().toLowerCase() : 'khác';
    const CAT_MAP = {
      'ăn uống':'🍜 Ăn uống','lưu trú':'🏨 Lưu trú','di chuyển':'🚗 Di chuyển',
      'xăng dầu':'⛽ Xăng dầu','vui chơi':'🎡 Vui chơi','mua sắm':'🛒 Mua sắm',
      'y tế':'💊 Y tế','khác':'📦 Khác',
    };
    const category = CAT_MAP[catRaw] || detectCategory(name);
    const dateStr  = Utilities.formatDate(new Date(), 'Asia/Ho_Chi_Minh', 'dd/MM/yyyy');

    writeExpense({ dateStr, name, amount, category, group: userInfo.group });
    sendTG(cfg.token, chatId,
      `✅ Đọc hoá đơn xong!\n\n📅 ${dateStr}\n📝 ${name}\n📂 ${category}\n💰 ${fmtMoney(amount)}\n👥 ${userInfo.group} (${userInfo.name})`
    );
  } catch(e) {
    Logger.log(e);
    sendTG(cfg.token, chatId, '❌ Lỗi khi đọc ảnh. Thử nhắn thủ công.');
  }
}

// ════════════════════════════════════════════════════════
//  📍 VỊ TRÍ + TÌM QUÁN ĂN
// ════════════════════════════════════════════════════════
function handleLocation(msg, cfg) {
  const chatId = msg.chat.id;
  const { latitude, longitude } = msg.location;
  PropertiesService.getScriptProperties()
    .setProperty(`loc_${chatId}`, JSON.stringify({ lat: latitude, lon: longitude }));
  sendTG(cfg.token, chatId,
    `📍 Đã lưu vị trí!\n\nBây giờ hỏi:\n` +
    `• <b>quán gần tôi nhất</b>\n• <b>trên đường về, quán nào ngon</b>`
  );
}

function handleRestaurantQuery(msg, cfg) {
  const chatId = msg.chat.id;
  const text   = (msg.text || '').toLowerCase();
  const locStr = PropertiesService.getScriptProperties().getProperty(`loc_${chatId}`);

  if (!locStr) {
    sendTG(cfg.token, chatId,
      '📍 Gửi vị trí trước để tôi tìm quán!\n\n' +
      'Trong Telegram: <b>📎 → Location</b> (hoặc 📎 → Share location)'
    );
    return;
  }

  const { lat, lon } = JSON.parse(locStr);
  const restaurants  = getRestaurantData();
  if (!restaurants.length) {
    sendTG(cfg.token, chatId, '❌ Sheet "Quán Ăn" chưa có dữ liệu. Chạy menu Khởi tạo trước.');
    return;
  }

  const isRouteQuery = /đường về|trên đường/.test(text);
  const results = isRouteQuery
    ? findAlongRoute(restaurants, lat, lon)
    : findNearestRestaurants(restaurants, lat, lon);

  if (!results.length) {
    sendTG(cfg.token, chatId, '🔍 Không tìm thấy quán nào phù hợp.');
    return;
  }

  const title = isRouteQuery
    ? `🛣️ <b>Quán trên đường về ${CFG.resort.name}:</b>\n`
    : `📍 <b>Quán gần bạn nhất:</b>\n`;

  const lines = [title];
  results.slice(0, 5).forEach((r, i) => {
    lines.push(`${i+1}. <b>${r.name}</b> (${r.area})`);
    lines.push(`   ${r.type} · ~${r.price}k/người · 📏 ${r.dist.toFixed(1)}km`);
    if (r.note) lines.push(`   💬 ${r.note}`);
  });
  lines.push('\n💡 Gửi lại 📍 vị trí để cập nhật.');
  sendTG(cfg.token, chatId, lines.join('\n'));
}

function getRestaurantData() {
  const s = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Quán Ăn');
  if (!s || s.getLastRow() < 3) return [];
  return s.getRange(3, 1, s.getLastRow() - 2, 9).getValues()
    .filter(r => r[1])
    .map(r => ({
      name: String(r[1]), area: String(r[2]), type: String(r[3]),
      price: r[4] || 0, lat: r[5], lon: r[6], onRoute: r[7], note: String(r[8]),
    }));
}

function haversine(lat1, lon1, lat2, lon2) {
  const R = 6371;
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(dLat/2)**2
    + Math.cos(lat1*Math.PI/180) * Math.cos(lat2*Math.PI/180) * Math.sin(dLon/2)**2;
  return R * 2 * Math.asin(Math.sqrt(a));
}

function findNearestRestaurants(restaurants, lat, lon) {
  return restaurants
    .filter(r => r.lat && r.lon)
    .map(r => ({ ...r, dist: haversine(lat, lon, r.lat, r.lon) }))
    .sort((a, b) => a.dist - b.dist);
}

function findAlongRoute(restaurants, fromLat, fromLon) {
  const { lat: toLat, lon: toLon } = CFG.resort;
  const direct = haversine(fromLat, fromLon, toLat, toLon);
  return restaurants
    .filter(r => r.lat && r.lon)
    .map(r => {
      const dist   = haversine(fromLat, fromLon, r.lat, r.lon);
      const detour = dist + haversine(r.lat, r.lon, toLat, toLon) - direct;
      return { ...r, dist, detour };
    })
    .filter(r => r.detour < Math.max(5, direct * 0.25)) // ≤25% hoặc 5km chênh lệch
    .sort((a, b) => a.detour - b.detour);
}

// ════════════════════════════════════════════════════════
//  📦 DANH SÁCH ĐỒ CẦN ĐEM
// ════════════════════════════════════════════════════════
function handlePackingQuery(msg, cfg, text) {
  const chatId = msg.chat.id;
  const t      = text.toLowerCase();

  if (/^đã đem/.test(t)) {
    const raw   = text.replace(/^đã đem\s*/i, '').replace(/\bvà\b/gi, ',');
    const items = raw.split(/[,;]+/).map(s => s.trim()).filter(Boolean);
    markPacked(cfg, chatId, items);
  } else if (/chưa đem|còn thiếu|còn gì/.test(t)) {
    listUnpacked(cfg, chatId);
  } else {
    listAllPacking(cfg, chatId);
  }
}

function getPackingData() {
  const s = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Phải Đem');
  if (!s || s.getLastRow() < 4) return [];
  return s.getRange(4, 1, s.getLastRow() - 3, 6).getValues()
    .filter(r => r[1])
    .map((r, i) => ({
      row    : i + 4,
      name   : String(r[1]),
      group  : String(r[2]),
      qty    : String(r[3]),
      packed : r[4] === true,
      note   : String(r[5]),
    }));
}

function listAllPacking(cfg, chatId) {
  const items = getPackingData();
  if (!items.length) { sendTG(cfg.token, chatId, '❌ Sheet "Phải Đem" chưa có dữ liệu.'); return; }

  const byGroup = {};
  items.forEach(i => { (byGroup[i.group] = byGroup[i.group] || []).push(i); });

  const lines = ['📦 <b>Danh sách đồ cần đem:</b>\n'];
  Object.entries(byGroup).forEach(([grp, gItems]) => {
    lines.push(`<b>${grp}:</b>`);
    gItems.forEach(i => lines.push(`  ${i.packed ? '✅' : '⬜'} ${i.name}${i.qty ? ' ('+i.qty+')' : ''}`));
  });
  const packed = items.filter(i => i.packed).length;
  lines.push(`\n📊 <b>${packed}/${items.length}</b> đã đem`);
  sendTG(cfg.token, chatId, lines.join('\n'));
}

function listUnpacked(cfg, chatId) {
  const items = getPackingData().filter(i => !i.packed);
  if (!items.length) { sendTG(cfg.token, chatId, '✅ Tất cả đã đem đủ rồi! 🎉'); return; }

  const byGroup = {};
  items.forEach(i => { (byGroup[i.group] = byGroup[i.group] || []).push(i); });

  const lines = [`⬜ <b>Chưa đem (${items.length} món):</b>\n`];
  Object.entries(byGroup).forEach(([grp, gItems]) => {
    lines.push(`<b>${grp}:</b>`);
    gItems.forEach(i => {
      const urgent = i.note.includes('BẮT BUỘC') ? ' ⚠️' : '';
      lines.push(`  • ${i.name}${i.qty ? ' ('+i.qty+')' : ''}${urgent}`);
    });
  });
  lines.push('\nNhắn: <b>đã đem [tên đồ]</b> để đánh dấu');
  sendTG(cfg.token, chatId, lines.join('\n'));
}

function markPacked(cfg, chatId, itemNames) {
  const s = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Phải Đem');
  if (!s) { sendTG(cfg.token, chatId, '❌ Sheet "Phải Đem" chưa có.'); return; }

  const items    = getPackingData();
  const marked   = [];
  const notFound = [];

  itemNames.forEach(query => {
    const q = query.toLowerCase().trim();
    const match = items.find(i =>
      i.name.toLowerCase().includes(q) || q.includes(i.name.toLowerCase().split(' ')[0])
    );
    if (match) {
      s.getRange(match.row, 5).setValue(true);
      marked.push(match.name);
    } else {
      notFound.push(query);
    }
  });

  let reply = '';
  if (marked.length)   reply += `✅ Đã đánh dấu đem:\n${marked.map(m => `• ${m}`).join('\n')}`;
  if (notFound.length) reply += `${reply ? '\n\n' : ''}❓ Không tìm thấy:\n${notFound.map(m => `• ${m}`).join('\n')}\n\n💡 Thử: <b>danh sách cần đem</b> để xem đúng tên`;
  sendTG(cfg.token, chatId, reply || '❓ Không tìm thấy món nào.');
}

// ════════════════════════════════════════════════════════
//  📊 BÁO CÁO HÔM NAY
// ════════════════════════════════════════════════════════
function sendDailyReport(cfg, chatId) {
  const s = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Chi Tiêu');
  if (!s || s.getLastRow() < 2) { sendTG(cfg.token, chatId, 'Chưa có dữ liệu chi tiêu.'); return; }

  const today    = Utilities.formatDate(new Date(), 'Asia/Ho_Chi_Minh', 'yyyyMMdd');
  const todayStr = Utilities.formatDate(new Date(), 'Asia/Ho_Chi_Minh', 'dd/MM/yyyy');
  const data     = s.getRange(2, 2, s.getLastRow() - 1, 5).getValues()
    .filter(r => r[0] instanceof Date && r[1]);
  const todayData = data.filter(r =>
    Utilities.formatDate(r[0], 'Asia/Ho_Chi_Minh', 'yyyyMMdd') === today
  );

  if (!todayData.length) {
    sendTG(cfg.token, chatId, `📊 Hôm nay ${todayStr} chưa có khoản chi nào.`);
    return;
  }

  const lines   = todayData.map(r => `• ${r[1]} — <b>${fmtMoney(r[3])}</b> <i>(${r[4]})</i>`);
  const total   = todayData.reduce((acc, r) => acc + r[3], 0);
  const byGroup = {};
  todayData.forEach(r => { byGroup[r[4]] = (byGroup[r[4]] || 0) + r[3]; });

  let msg = `📊 <b>Chi tiêu hôm nay ${todayStr}:</b>\n\n${lines.join('\n')}\n\n`;
  msg += Object.entries(byGroup).map(([g, v]) => `${g}: ${fmtMoney(v)}`).join('\n');
  msg += `\n────────────\nTổng: <b>${fmtMoney(total)}</b>`;
  sendTG(cfg.token, chatId, msg);
}

// ════════════════════════════════════════════════════════
//  ☀️ TIN NHẮN BUỔI SÁNG 6H — THỜI TIẾT + LỊCH TRÌNH
// ════════════════════════════════════════════════════════

// Tóm tắt ngắn gọn từng ngày để gửi Telegram
const DAY_BRIEF = [
  { theme: 'XUẤT PHÁT → TUY HÒA', items: [
    '🚗 Khởi hành 5h–6h sáng, đổ đầy dầu',
    '🏨 Check-in từ 14h, tắm biển Tuy Hòa 16h',
    '🍜 Tối: bún cá ngừ, gỏi cá mai, bánh tráng nướng',
  ]},
  { theme: 'GÀNH ĐÁ ĐĨA + HÒN YẾN', items: [
    '🌅 5h30 xuất phát (90km) — đá basalt Di sản quốc gia',
    '🦀 Trưa: sò huyết Ô Loan nướng tại Sông Cầu',
    '🏖️ Chiều: Vịnh Hòa — bãi ít người, nước xanh',
  ]},
  { theme: 'MŨI ĐIỆN + BÃI XÉP', items: [
    '🌄 4h30 xuất phát — đón bình minh cực Đông VN',
    '🏖️ Chiều: Bãi Xép (sóng nhỏ, an toàn cho bé)',
    '🛒 Tối: cá bò khô, mực khô, cá ngừ đại dương',
  ]},
  { theme: 'ĐẦM Ô LOAN + THƯ GIÃN', items: [
    '🛕 7h–9h: Tháp Nhạn — view đẹp',
    '🚣 9h30: Đầm Ô Loan — kayak ~50k/người',
    '🏊 Chiều: hồ bơi khách sạn — bé thích lắm',
    '🐟 Tối đặc biệt: cá ngừ đại dương câu tay',
  ]},
  { theme: 'VỀ NHÀ', items: [
    '🍜 6h: ăn sáng lần cuối — bún cá ngừ',
    '🛒 7h: chợ Tuy Hòa mua đặc sản lần cuối',
    '⛽ 8h30: đổ đầy dầu rồi lên đường',
    '🏠 Dự kiến về 17h–19h',
  ]},
];

function setupMorningBriefingTrigger() {
  ScriptApp.getProjectTriggers().forEach(t => {
    if (t.getHandlerFunction() === 'sendMorningBriefing') ScriptApp.deleteTrigger(t);
  });
  ScriptApp.newTrigger('sendMorningBriefing').timeBased().atHour(6).everyDays(1).create();
  SpreadsheetApp.getUi().alert('✅ Đã bật tin nhắn buổi sáng 6h!\n\nMỗi sáng 6h bot sẽ gửi thời tiết + lịch trình ngày hôm đó.');
}

function deleteNotificationTriggers() {
  const fns = ['sendMorningBriefing', 'sendEveningReminder'];
  let n = 0;
  ScriptApp.getProjectTriggers().forEach(t => {
    if (fns.includes(t.getHandlerFunction())) { ScriptApp.deleteTrigger(t); n++; }
  });
  SpreadsheetApp.getUi().alert(n > 0 ? `✅ Đã tắt ${n} trigger.` : 'Không có trigger nào đang chạy.');
}

function sendMorningBriefing() {
  let cfg;
  try { cfg = loadConfig(); } catch(e) { Logger.log(e); return; }
  const text = buildMorningBriefing();
  getAllUserIds(cfg).forEach(uid => {
    try { sendTG(cfg.token, uid, text); } catch(e) { Logger.log(e); }
  });
}

function buildMorningBriefing() {
  const now       = new Date();
  const tripStart = new Date(CFG.tripStart + 'T00:00:00+07:00');
  const dayIndex  = Math.round((now - tripStart) / 86400000);

  if (dayIndex < 0) {
    const daysLeft = Math.ceil((tripStart - now) / 86400000);
    return `🌴 <b>Phú Yên 2026</b>\n\n⏳ Còn <b>${daysLeft} ngày</b> nữa xuất phát!\n📅 Khởi hành: 23/05/2026`;
  }
  if (dayIndex > 4) {
    return `🌴 <b>Phú Yên 2026</b>\n\n✅ Chuyến đi đã kết thúc. Cảm ơn cả nhà! 🎉`;
  }

  const brief   = DAY_BRIEF[dayIndex];
  const weather = fetchWeather();
  const lines   = [
    `☀️ <b>Chào buổi sáng! Ngày ${dayIndex+1}/5 — ${CFG.days[dayIndex]}</b>`,
    `📍 <b>${brief.theme}</b>`,
    '',
    '🌤️ <b>Thời tiết hôm nay:</b>',
  ];

  const wxEntries = Object.entries(weather);
  // Chỉ lấy 3 địa điểm gần nhất với ngày hôm nay để tin nhắn không quá dài
  const relevant = wxEntries.filter(([,d]) => d).slice(0, 3);
  if (relevant.length) {
    relevant.forEach(([place, daily]) => {
      const code   = daily.weathercode[dayIndex];
      const tmax   = daily.temperature_2m_max[dayIndex];
      const precip = (daily.precipitation_sum[dayIndex] || 0).toFixed(1);
      lines.push(`  📍 ${place}: ${wxLabel(code)} · ${tmax}°C · Mưa ${precip}mm · ${wxOk(code, parseFloat(precip))}`);
    });
  } else {
    lines.push('  (Chưa có dữ liệu — chạy Cập nhật Thời Tiết)');
  }

  lines.push('');
  lines.push('📋 <b>Kế hoạch hôm nay:</b>');
  brief.items.forEach(item => lines.push(`  ${item}`));
  lines.push('');
  lines.push('/baocao — xem chi tiêu hôm nay');

  return lines.join('\n');
}

// ════════════════════════════════════════════════════════
//  🔔 NHẮC NHỞ & TỔNG KẾT TỰ ĐỘNG 20H TỐI
// ════════════════════════════════════════════════════════
function setupEveningReminderTrigger() {
  ScriptApp.getProjectTriggers().forEach(t => {
    if (t.getHandlerFunction() === 'sendEveningReminder') ScriptApp.deleteTrigger(t);
  });
  ScriptApp.newTrigger('sendEveningReminder').timeBased().atHour(20).everyDays(1).create();
  SpreadsheetApp.getUi().alert(
    '✅ Đã bật nhắc nhở 20h tối!\n\nMỗi tối 20h bot sẽ tự gửi tổng kết + nhắc ghi chi tiêu cho tất cả thành viên.'
  );
}


function sendEveningReminder() {
  let cfg;
  try { cfg = loadConfig(); } catch(e) { Logger.log(e); return; }

  const todayStr = Utilities.formatDate(new Date(), 'Asia/Ho_Chi_Minh', 'dd/MM/yyyy');
  const { count, total } = getTodayStats();

  const summaryLine = count > 0
    ? `Hôm nay đã ghi <b>${count} khoản</b> — tổng <b>${fmtMoney(total)}</b>.`
    : 'Hôm nay chưa ghi khoản nào.';

  const msg =
    `🌙 Tổng kết ${todayStr}\n\n` +
    `${summaryLine}\n\n` +
    `Còn khoản nào chưa ghi? Nhắn ngay:\n` +
    `• <b>200k ăn tối</b>\n• <b>gửi ảnh hoá đơn</b>\n\n` +
    `/baocao — xem chi tiết hôm nay`;

  getAllUserIds(cfg).forEach(uid => {
    try { sendTG(cfg.token, uid, msg); } catch(e) { Logger.log(e); }
  });
}

function getTodayStats() {
  const s = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Chi Tiêu');
  if (!s || s.getLastRow() < 2) return { count: 0, total: 0 };
  const today = Utilities.formatDate(new Date(), 'Asia/Ho_Chi_Minh', 'yyyyMMdd');
  const data  = s.getRange(2, 2, s.getLastRow() - 1, 4).getValues()
    .filter(r => r[0] instanceof Date && r[2]);
  let count = 0, total = 0;
  data.forEach(r => {
    if (Utilities.formatDate(r[0], 'Asia/Ho_Chi_Minh', 'yyyyMMdd') === today) {
      count++; total += r[3];
    }
  });
  return { count, total };
}

function getAllUserIds(cfg) {
  // Với Telegram DM: user_id === chat_id
  return [...new Set(Object.keys(cfg.byUserId))].filter(Boolean);
}

function parseTGExpense(text, group) {
  let dateStr, content = text;
  const dm = text.match(/(\d{1,2})[\/\-](\d{1,2})(?:[\/\-]\d{2,4})?\s*[-–]\s*(.+)/);
  if (dm) {
    dateStr = `${String(dm[1]).padStart(2,'0')}/${String(dm[2]).padStart(2,'0')}/2026`;
    content = dm[3].trim();
  } else {
    dateStr = Utilities.formatDate(new Date(), 'Asia/Ho_Chi_Minh', 'dd/MM/yyyy');
  }
  const amount = parseTGAmount(content);
  if (!amount) return null;
  const name = content
    .replace(/(\d+[\.,]?\d*)\s*(tr|triệu|trieu|k|nghìn|nghin|đồng|dong|đ\b|vnd)/gi,'')
    .replace(/^[\s\-–,]+/,'').replace(/[\s\-–,]+$/,'').trim() || 'Chi tiêu';
  return { dateStr, name, amount, category: detectCategory(name+' '+content), group };
}

function parseTGAmount(text) {
  const t = text.toLowerCase().replace(/,/g,'');
  let m;
  m = t.match(/(\d+\.?\d*)\s*(tr|triệu|trieu)/); if(m) return Math.round(parseFloat(m[1])*1e6);
  m = t.match(/(\d+\.?\d*)\s*(k|nghìn|nghin)/);  if(m) return Math.round(parseFloat(m[1])*1e3);
  m = t.match(/(\d{4,})/);                         if(m) return parseInt(m[1]);
  return null;
}

function detectCategory(text) {
  const t = text.toLowerCase();
  const MAP = [
    ['⛽ Xăng dầu',  ['xăng','dầu','petro','nhiên liệu']],
    ['🚗 Di chuyển', ['xe','taxi','grab','bus','tàu','máy bay','di chuyển','vé xe','đi lại']],
    ['🏨 Lưu trú',   ['phòng','khách sạn','resort','homestay','lưu trú','ngủ','check-in','checkin']],
    ['🍜 Ăn uống',   ['ăn','cơm','bún','phở','mì','quán','nhà hàng','cafe','cà phê','uống','tối','sáng','trưa','hải sản','đặc sản','bánh']],
    ['🎡 Vui chơi',  ['vé','tham quan','vui chơi','tour','giải trí','du lịch']],
    ['🛒 Mua sắm',   ['mua','chợ','siêu thị','sắm','quà','mang về']],
    ['💊 Y tế',      ['thuốc','y tế','bệnh viện','khám','đau']],
  ];
  for (const [cat, kws] of MAP) if (kws.some(k=>t.includes(k))) return cat;
  return '📦 Khác';
}

function writeExpense(exp) {
  const s = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Chi Tiêu');
  if (!s) return;
  let row = 2;
  while (s.getRange(row,3).getValue()) row++;
  const [d,m,y] = exp.dateStr.split('/').map(Number);
  s.getRange(row,2).setValue(new Date(y,m-1,d)).setNumberFormat('dd/mm/yyyy');
  s.getRange(row,3).setValue(exp.name);
  s.getRange(row,4).setValue(exp.category);
  s.getRange(row,5).setValue(exp.amount).setNumberFormat('#,##0');
  s.getRange(row,6).setValue(exp.group);
}

function sendRecentExpenses(cfg, chatId) {
  const s = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Chi Tiêu');
  if (!s || s.getLastRow()<2) { sendTG(cfg.token, chatId, 'Chưa có khoản chi nào.'); return; }
  const data = s.getRange(2,2,s.getLastRow()-1,5).getValues().filter(r=>r[1]).slice(-5);
  const lines = data.map(r => {
    const d = r[0] ? Utilities.formatDate(new Date(r[0]),'Asia/Ho_Chi_Minh','dd/MM') : '—';
    return `${d}  ${r[1]}  ${fmtMoney(r[3])}  <i>${r[4]}</i>`;
  });
  sendTG(cfg.token, chatId, `📋 <b>5 khoản gần nhất:</b>\n\n${lines.join('\n')}`);
}

function sendSummary(cfg, chatId) {
  const s = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Chi Tiêu');
  if (!s || s.getLastRow()<2) { sendTG(cfg.token, chatId, 'Chưa có dữ liệu.'); return; }
  const data   = s.getRange(2,5,s.getLastRow()-1,2).getValues().filter(r=>r[0]&&r[1]);
  const totals = {};
  data.forEach(([amt,grp]) => { totals[grp]=(totals[grp]||0)+amt; });
  const total  = Object.values(totals).reduce((a,b)=>a+b,0);
  const lines  = Object.entries(totals).map(([g,v])=>`${g}: <b>${fmtMoney(v)}</b>`);
  lines.push('────────────');
  lines.push(`Tổng: <b>${fmtMoney(total)}</b>`);
  sendTG(cfg.token, chatId, `💰 <b>Tổng chi từng nhóm:</b>\n\n${lines.join('\n')}`);
}

function sendTG(token, chatId, text) {
  const res = UrlFetchApp.fetch(`https://api.telegram.org/bot${token}/sendMessage`, {
    method:'post', contentType:'application/json',
    payload: JSON.stringify({ chat_id:chatId, text, parse_mode:'HTML' }),
    muteHttpExceptions:true,
  });
  try {
    const body = JSON.parse(res.getContentText() || '{}');
    if (!body.ok) {
      Logger.log(JSON.stringify({
        label: 'sendTG_error',
        chat_id: chatId,
        status_code: res.getResponseCode(),
        response: body,
      }));
    }
  } catch (e) {
    Logger.log(JSON.stringify({
      label: 'sendTG_parse_error',
      chat_id: chatId,
      status_code: res.getResponseCode(),
      raw: res.getContentText(),
    }));
    Logger.log(e);
  }
}

function logTelegramEvent_(label, update) {
  try {
    const msg = update && update.message;
    const from = msg && msg.from;
    Logger.log(JSON.stringify({
      label,
      update_id: update && update.update_id || null,
      message_id: msg && msg.message_id || null,
      text: msg && (msg.text || msg.caption) || '',
      from_user_id: from && from.id || null,
      from_user_is_bot: from && from.is_bot === true,
      chat_id: msg && msg.chat && msg.chat.id || null,
    }));
  } catch (e) {
    Logger.log(e);
  }
}

function fmtMoney(n) {
  return n >= 1000000
    ? (n/1000000).toFixed(n%1000000===0?0:1) + ' triệu đ'
    : n.toLocaleString('vi-VN') + ' đ';
}

function setupTelegramWebhook() {
  const cfg = loadConfig();

  // Đọc Web App URL từ sheet (B6) — đáng tin hơn ScriptApp.getService().getUrl()
  const s   = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('⚙️ Bot Config');
  const url = s ? String(s.getRange('B6').getValue()).trim() : '';

  if (!url || !url.startsWith('https://script.google.com')) {
    SpreadsheetApp.getUi().alert(
      '⚠️ Chưa có Web App URL!\n\n' +
      '1. Apps Script → Deploy → Manage deployments\n' +
      '2. Copy URL (dạng .../exec)\n' +
      '3. Paste vào ô B6 sheet "⚙️ Bot Config"\n' +
      '4. Chạy lại menu này'
    );
    return;
  }

  resetTelegramUpdateState_();
  try {
    UrlFetchApp.fetch(
      `https://api.telegram.org/bot${cfg.token}/deleteWebhook?drop_pending_updates=true`,
      { muteHttpExceptions:true }
    );
  } catch (e) {
    Logger.log(e);
  }

  const res  = UrlFetchApp.fetch(
    `https://api.telegram.org/bot${cfg.token}/setWebhook?url=${encodeURIComponent(url)}&drop_pending_updates=true`,
    { muteHttpExceptions:true }
  );
  const json = JSON.parse(res.getContentText());
  SpreadsheetApp.getUi().alert(
    json.ok
      ? `✅ Webhook kết nối thành công!\n\nURL: ${url}\n\nĐã xoá pending updates cũ.\nMở Telegram nhắn /start để test.`
      : '❌ Lỗi: ' + json.description + '\n\nKiểm tra lại token và URL.'
  );
}

function checkTelegramWebhookInfo() {
  const cfg = loadConfig();
  const res = UrlFetchApp.fetch(
    `https://api.telegram.org/bot${cfg.token}/getWebhookInfo`,
    { muteHttpExceptions:true }
  );
  const json = JSON.parse(res.getContentText());
  if (!json.ok) {
    SpreadsheetApp.getUi().alert('❌ Không lấy được webhook info: ' + json.description);
    return;
  }

  const info = json.result || {};
  SpreadsheetApp.getUi().alert(
    '🔎 TELEGRAM WEBHOOK INFO\n\n' +
    'URL: ' + (info.url || '(trống)') + '\n' +
    'Pending updates: ' + (info.pending_update_count || 0) + '\n' +
    'Last error date: ' + (info.last_error_date || '(không có)') + '\n' +
    'Last error message: ' + (info.last_error_message || '(không có)') + '\n' +
    'Max connections: ' + (info.max_connections || '(mặc định)') + '\n' +
    'Has custom cert: ' + (info.has_custom_certificate === true ? 'Có' : 'Không')
  );
}

function clearTelegramPendingUpdates() {
  const cfg = loadConfig();
  const res = UrlFetchApp.fetch(
    `https://api.telegram.org/bot${cfg.token}/deleteWebhook?drop_pending_updates=true`,
    { muteHttpExceptions:true }
  );
  resetTelegramUpdateState_();
  const json = JSON.parse(res.getContentText());
  SpreadsheetApp.getUi().alert(
    json.ok
      ? '✅ Đã xoá pending updates Telegram và reset trạng thái dedupe.\n\nBây giờ chạy lại "🔗 Cài đặt Webhook Telegram".'
      : '❌ Không xoá được pending updates: ' + json.description
  );
}

function resetTelegramUpdateState_() {
  // CacheService không hỗ trợ xoá hàng loạt theo prefix.
  // Sau khi reset webhook với drop_pending_updates, TTL cache cũ sẽ tự hết hạn.
}

// ============================================================================
// APPS SCRIPT API LAYER
// Dùng cho backend Python (Render) đọc dữ liệu thật từ Google Sheet qua doGet.
// Không đụng vào doPost hiện có để tránh ảnh hưởng webhook Telegram cũ.
// ============================================================================

var API_SHEETS = {
  chiTieu:   'Chi Tiêu',
  gopTien:   'Góp Tiền Trước',
  tongHop:   'Tổng Hợp',
  quanAn:    'Quán Ăn',
  phaiDem:   'Phải Đem',
  botConfig: '⚙️ Bot Config',
};

var API_CATEGORIES = ['🏨 Lưu trú','🍜 Ăn uống','🚗 Di chuyển','⛽ Xăng dầu',
                      '🎡 Vui chơi','🛒 Mua sắm','💊 Y tế','📦 Khác'];

function doGet(e) {
  try {
    var params = (e && e.parameter) || {};
    var action = params.action || '';
    var expected = PropertiesService.getScriptProperties().getProperty('api_shared_secret');

    if (!expected || params.token !== expected) {
      return apiJson_({ ok: false, error: 'unauthorized' });
    }

    var data;
    switch (action) {
      case 'ping': data = { ok: true, pong: true }; break;
      case 'expenses_recent': data = apiExpensesRecent_(params); break;
      case 'expenses_total': data = apiExpensesTotal_(); break;
      case 'report_full': data = apiReportFull_(); break;
      case 'debts': data = apiDebts_(); break;
      case 'contributions': data = apiContributions_(); break;
      case 'packing_status': data = apiPackingStatus_(params); break;
      case 'restaurants': data = apiRestaurants_(params); break;
      case 'expenses_by_category': data = apiExpensesByCategory_(); break;
      case 'expenses_by_day': data = apiExpensesByDay_(); break;
      case 'members': data = apiMembers_(); break;
      default:
        data = { ok: false, error: 'unknown_action', action: action };
    }
    return apiJson_(data);
  } catch (err) {
    return apiJson_({ ok: false, error: 'exception', message: String(err) });
  }
}

function apiJson_(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

function apiReadExpenses_() {
  var s = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(API_SHEETS.chiTieu);
  if (!s || s.getLastRow() < 2) return [];
  var values = s.getRange(2, 1, s.getLastRow() - 1, 8).getValues();
  var rows = [];
  values.forEach(function (r) {
    var khoanChi = String(r[2] || '').trim();
    if (!khoanChi) return;
    rows.push({
      stt: r[0],
      date: r[1] instanceof Date ? Utilities.formatDate(r[1], 'GMT+7', 'dd/MM/yyyy') : String(r[1] || ''),
      note: khoanChi,
      category: String(r[3] || '').trim(),
      amount: Number(r[4]) || 0,
      group: String(r[5] || '').trim(),
      note1: String(r[6] || '').trim(),
      note2: String(r[7] || '').trim(),
    });
  });
  return rows;
}

function apiExpensesRecent_(params) {
  var limit = Math.min(Math.max(parseInt(params.limit, 10) || 5, 1), 20);
  var rows = apiReadExpenses_();
  var recent = rows.slice(-limit).reverse();
  return { ok: true, count: recent.length, total_rows: rows.length, items: recent };
}

function apiExpensesTotal_() {
  var rows = apiReadExpenses_();
  var total = 0, byGroup = {};
  rows.forEach(function (r) {
    total += r.amount;
    byGroup[r.group || '(không nhóm)'] = (byGroup[r.group || '(không nhóm)'] || 0) + r.amount;
  });
  return { ok: true, total: total, by_group: byGroup, count: rows.length };
}

function apiExpensesByCategory_() {
  var rows = apiReadExpenses_();
  var byCat = {};
  API_CATEGORIES.forEach(function (c) { byCat[c] = 0; });
  rows.forEach(function (r) {
    var c = r.category || '📦 Khác';
    byCat[c] = (byCat[c] || 0) + r.amount;
  });
  return { ok: true, by_category: byCat, count: rows.length };
}

function apiExpensesByDay_() {
  var rows = apiReadExpenses_();
  var byDay = {};
  rows.forEach(function (r) {
    var d = r.date || '(không ngày)';
    byDay[d] = (byDay[d] || 0) + r.amount;
  });
  return { ok: true, by_day: byDay, count: rows.length };
}

function apiContributions_() {
  var s = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(API_SHEETS.gopTien);
  if (!s) return { ok: false, error: 'sheet_not_found' };
  var values = s.getRange('A4:D6').getValues();
  var items = [], totalContributed = 0;
  values.forEach(function (r) {
    if (!r[0]) return;
    var amount = Number(r[1]) || 0;
    totalContributed += amount;
    items.push({
      group: String(r[0]).trim(),
      amount: amount,
      status: String(r[2] || '').trim(),
      note: String(r[3] || '').trim(),
    });
  });
  return { ok: true, total_contributed: totalContributed, items: items };
}

function apiDebts_() {
  var s = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(API_SHEETS.tongHop);
  if (!s) return { ok: false, error: 'sheet_not_found' };
  var spentLV = Number(s.getRange('B9').getValue()) || 0;
  var spentLH = Number(s.getRange('C9').getValue()) || 0;
  var spentTotal = Number(s.getRange('D9').getValue()) || 0;
  var balanceLV = Number(s.getRange('B19').getValue()) || 0;
  var balanceLH = Number(s.getRange('C19').getValue()) || 0;
  return {
    ok: true,
    spent: { 'Nhóm LV': spentLV, 'Nhóm LH': spentLH, total: spentTotal },
    balance: { 'Nhóm LV': balanceLV, 'Nhóm LH': balanceLH },
  };
}

function apiReportFull_() {
  return {
    ok: true,
    total: apiExpensesTotal_(),
    by_category: apiExpensesByCategory_(),
    by_day: apiExpensesByDay_(),
    contributions: apiContributions_(),
    debts: apiDebts_(),
  };
}

function apiPackingStatus_(params) {
  var s = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(API_SHEETS.phaiDem);
  if (!s || s.getLastRow() < 4) return { ok: false, error: 'sheet_not_found' };
  var values = s.getRange(4, 1, s.getLastRow() - 3, 6).getValues();
  var items = [], packed = 0, notPacked = 0, mandatoryLeft = [];
  values.forEach(function (r) {
    var name = String(r[1] || '').trim();
    if (!name) return;
    var isPacked = r[4] === true;
    var note = String(r[5] || '').trim();
    if (isPacked) packed++; else {
      notPacked++;
      if (note.indexOf('BẮT BUỘC') !== -1) mandatoryLeft.push(name);
    }
    items.push({
      name: name,
      group: String(r[2] || '').trim(),
      quantity: String(r[3] || '').trim(),
      packed: isPacked,
      note: note,
    });
  });
  var filter = (params.filter || '').toLowerCase();
  var filtered = items;
  if (filter === 'left') filtered = items.filter(function (i) { return !i.packed; });
  if (filter === 'packed') filtered = items.filter(function (i) { return i.packed; });
  return {
    ok: true,
    total: items.length,
    packed: packed,
    not_packed: notPacked,
    mandatory_left: mandatoryLeft,
    items: filtered,
  };
}

function apiRestaurants_(params) {
  var s = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(API_SHEETS.quanAn);
  if (!s || s.getLastRow() < 3) return { ok: false, error: 'sheet_not_found' };
  var values = s.getRange(3, 1, s.getLastRow() - 2, 9).getValues();
  var items = [];
  values.forEach(function (r) {
    var name = String(r[1] || '').trim();
    if (!name) return;
    items.push({
      name: name,
      area: String(r[2] || '').trim(),
      type: String(r[3] || '').trim(),
      price_k: Number(r[4]) || 0,
      lat: Number(r[5]) || null,
      lon: Number(r[6]) || null,
      on_route: String(r[7] || '').trim() === '✅',
      note: String(r[8] || '').trim(),
    });
  });
  var area = (params.area || '').toLowerCase();
  if (area) items = items.filter(function (i) { return i.area.toLowerCase().indexOf(area) !== -1; });
  return { ok: true, count: items.length, items: items };
}

function apiMembers_() {
  var s = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(API_SHEETS.botConfig);
  if (!s) return { ok: false, error: 'sheet_not_found' };
  var values = s.getRange('A13:E62').getValues();
  var items = [];
  values.forEach(function (r) {
    var group = String(r[3] || '').trim();
    if (!group) return;
    items.push({
      username: String(r[0] || '').trim(),
      user_id: String(r[1] || '').trim(),
      name: String(r[2] || '').trim(),
      group: group,
      note: String(r[4] || '').trim(),
    });
  });
  return { ok: true, count: items.length, items: items };
}
