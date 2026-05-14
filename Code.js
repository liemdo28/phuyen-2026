// ════════════════════════════════════════════════════════
//  PHÚ YÊN 2026 — CHI TIÊU + LỊCH TRÌNH + TELEGRAM BOT
//  Nhóm: LV · LH · CM  |  7 người · 1 bé 4 tuổi · Carnival Dầu
//  Chuyến đi: 23–27/05/2026
// ════════════════════════════════════════════════════════

const CFG = {
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
    .addItem('🔧 Khởi tạo tất cả',             'setup')
    .addItem('🔄 Cập nhật Tổng Hợp',            'updateSummary')
    .addSeparator()
    .addItem('🤖 Cập nhật Thời Tiết & Gợi Ý',  'dailyAutoUpdate')
    .addSeparator()
    .addItem('⏰ Bật tự động 7h sáng',          'setupDailyTrigger')
    .addItem('⏹️ Tắt tự động',                  'deleteDailyTrigger')
    .addSeparator()
    .addItem('📱 Tạo sheet Bot Config',          'setupBotConfigSheet')
    .addItem('🔗 Cài đặt Webhook Telegram',      'setupTelegramWebhook')
    .addSeparator()
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
    .timeBased().atHour(7).everyDays(1).create();
  SpreadsheetApp.getUi().alert(
    '✅ Đã bật tự động 7h sáng!\n\n' +
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
  makeGopTienSheet(ss);
  makeChiTieuSheet(ss);
  makeTongHopSheet(ss);
  dailyAutoUpdate();
  reorderSheets(ss);
  SpreadsheetApp.getUi().alert(
    '✅ Khởi tạo xong!\n\n' +
    '• "Góp Tiền Trước" → khoản đã góp\n' +
    '• "Chi Tiêu" → nhập hàng ngày\n' +
    '• "Tổng Hợp" → kết quả tự động\n' +
    '• "Thời Tiết" → dự báo 23–27/05\n' +
    '• "Gợi Ý Lịch Trình" → phân tích & gợi ý\n\n' +
    'Dùng menu 📱 để cài Telegram Bot.'
  );
}

function makeGopTienSheet(ss) {
  let s = ss.getSheetByName('Góp Tiền Trước') || ss.insertSheet('Góp Tiền Trước');
  s.clear();
  s.getRange('A1').setValue('💵 KHOẢN GÓP TIỀN TRƯỚC').setFontSize(13).setFontWeight('bold');
  s.getRange('A1:D1').merge();
  s.getRange('A3:D3').setValues([['Nhóm','Đã góp (VNĐ)','Trạng thái','Ghi chú']])
    .setBackground('#2d3748').setFontColor('#fff').setFontWeight('bold');
  s.getRange('A4:D6').setValues([
    ['Nhóm LV', 0,         'Chưa góp',   ''],
    ['Nhóm LH', 0,         'Chưa góp',   ''],
    ['Nhóm CM', 15000000,  'Đã chuyển',  'Chuyển khoản ngày ...'],
  ]);
  s.getRange('B4:B6').setNumberFormat('#,##0 "đ"').setBackground('#fffbeb');
  s.getRange('C4').setBackground('#fed7d7');
  s.getRange('C5').setBackground('#fed7d7');
  s.getRange('C6').setBackground('#c6f6d5');
  s.getRange('A4:A6').setFontWeight('bold');
  [90,170,120,230].forEach((w,i) => s.setColumnWidth(i+1,w));
}

function makeChiTieuSheet(ss) {
  let s = ss.getSheetByName('Chi Tiêu') || ss.insertSheet('Chi Tiêu');
  s.clear();
  s.getRange(1,1,1,8)
    .setValues([['STT','Ngày','Khoản Chi','Danh Mục','Số Tiền (VNĐ)','Nhóm Trả','Ghi Chú 1','Ghi Chú 2']])
    .setBackground('#2d3748').setFontColor('#fff').setFontWeight('bold').setHorizontalAlignment('center');

  // Khoản Chi (cột C) — tự nhập, KHÔNG có dropdown
  s.getRange('D2:D1000').setDataValidation(
    SpreadsheetApp.newDataValidation()
      .requireValueInList(['🏨 Lưu trú','🍜 Ăn uống','🚗 Di chuyển','⛽ Xăng dầu',
                           '🎡 Vui chơi','🛒 Mua sắm','💊 Y tế','📦 Khác'], true)
      .setAllowInvalid(false).build()
  );
  s.getRange('F2:F1000').setDataValidation(
    SpreadsheetApp.newDataValidation()
      .requireValueInList(['Nhóm LV','Nhóm LH'], true)
      .setAllowInvalid(false).build()
  );
  s.getRange('B2:B1000').setNumberFormat('dd/mm/yyyy');
  s.getRange('E2:E1000').setNumberFormat('#,##0');
  for (let i = 2; i <= 300; i++) s.getRange(i,1).setFormula(`=IF(C${i}="","",ROW()-1)`);
  s.getRange('A2:A300').setFontColor('#a0aec0').setHorizontalAlignment('center');
  [45,105,210,130,155,100,185,185].forEach((w,i) => s.setColumnWidth(i+1,w));
  s.setFrozenRows(1);
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
  ['⚙️ Bot Config','Góp Tiền Trước','Chi Tiêu','Tổng Hợp','Thời Tiết','Gợi Ý Lịch Trình']
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
  s.clear();

  s.getRange('A1').setValue('⚙️ CÀI ĐẶT TELEGRAM BOT').setFontSize(13).setFontWeight('bold');
  s.getRange('A1:E1').merge();

  s.getRange('A3:E3').merge().setBackground('#2d3748').setFontColor('#fff').setFontWeight('bold').setValue('🔑 BOT TOKEN');
  s.getRange('A4').setValue('Token').setFontWeight('bold');
  s.getRange('B4:E4').merge().setValue('PASTE_TOKEN_VÀO_ĐÂY').setBackground('#fffbeb').setFontColor('#c05621');
  s.getRange('A5').setValue('Tên bot').setFontWeight('bold');
  s.getRange('B5:E5').merge().setValue('PhuYen2026Bot').setFontColor('#718096');

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
  const token      = String(s.getRange('B4').getValue()).trim();
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

function doPost(e) {
  try {
    const update = JSON.parse(e.postData.contents);
    if (update.message) handleMessage(update.message);
  } catch(err) { Logger.log(err); }
  return ContentService.createTextOutput('OK');
}

function handleMessage(msg) {
  let cfg;
  try { cfg = loadConfig(); } catch(err) { Logger.log(err); return; }

  const chatId   = msg.chat.id;
  const from     = msg.from;
  const userId   = String(from.id || '');
  const username = (from.username || '').toLowerCase().trim();
  const firstName= from.first_name || '';
  const text     = (msg.text || '').trim();

  if (text === '/start' || text === '/help') {
    sendTG(cfg.token, chatId,
      `👋 Xin chào ${firstName}!\n\nNhắn để ghi chi tiêu:\n` +
      `• <b>500k ăn tối</b>\n• <b>1.5tr tiền phòng</b>\n• <b>300k xăng dầu</b>\n• <b>24/5 - 800k ăn hải sản</b>\n\n` +
      `/xem — 5 khoản gần nhất\n/tong — tổng chi từng nhóm\n/id — xem Telegram ID của bạn`
    );
    return;
  }
  if (text === '/id') {
    sendTG(cfg.token, chatId,
      `🪪 Thông tin:\n\nUsername: @${username||'(chưa có)'}\nUser ID: <code>${userId}</code>\n\nCopy ID → paste vào cột B sheet "⚙️ Bot Config"`
    );
    return;
  }
  if (text === '/xem')  { sendRecentExpenses(cfg, chatId); return; }
  if (text === '/tong') { sendSummary(cfg, chatId); return; }

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
    sendTG(cfg.token, chatId, `❓ Không nhận ra số tiền.\n\nThử: <b>"500k ăn tối"</b> hoặc <b>"1.5tr tiền phòng"</b>`);
    return;
  }

  writeExpense(expense);
  sendTG(cfg.token, chatId,
    `✅ Đã ghi!\n\n📅 ${expense.dateStr}\n📝 ${expense.name}\n📂 ${expense.category}\n💰 ${fmtMoney(expense.amount)}\n👥 ${expense.group} (${userInfo.name})`
  );
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
  UrlFetchApp.fetch(`https://api.telegram.org/bot${token}/sendMessage`, {
    method:'post', contentType:'application/json',
    payload: JSON.stringify({ chat_id:chatId, text, parse_mode:'HTML' }),
    muteHttpExceptions:true,
  });
}

function fmtMoney(n) {
  return n >= 1000000
    ? (n/1000000).toFixed(n%1000000===0?0:1) + ' triệu đ'
    : n.toLocaleString('vi-VN') + ' đ';
}

function setupTelegramWebhook() {
  const cfg = loadConfig();
  const url = ScriptApp.getService().getUrl();
  const res = UrlFetchApp.fetch(
    `https://api.telegram.org/bot${cfg.token}/setWebhook?url=${encodeURIComponent(url)}`,
    { muteHttpExceptions:true }
  );
  const json = JSON.parse(res.getContentText());
  SpreadsheetApp.getUi().alert(
    json.ok
      ? '✅ Webhook kết nối thành công!\n\nMở Telegram nhắn /start để test.'
      : '❌ Lỗi: ' + json.description
  );
}