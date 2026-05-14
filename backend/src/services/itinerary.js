// ════════════════════════════════════════════════════════
//  ITINERARY SERVICE — Trip planner for Phú Yên
// ════════════════════════════════════════════════════════

import config from '../config/index.js';
import * as weatherService from './weather.js';
import { haversine } from '../utils/distance.js';

// Trip plan for Phú Yên 2026 (May 23-27)
const DAY_PLANS = [
  {
    day: 1,
    date: '23/05 (T7)',
    theme: 'XUẤT PHÁT → ĐẾN TUY HÒA',
    isTravelDay: true,
    morning: {
      activity: 'Khởi hành từ TP.HCM',
      details: [
        '5h–6h sáng: khởi hành sớm tránh nắng và kẹt xe',
        'Ăn sáng dọc QL1A hoặc thị xã Sông Cầu',
        'Đổ đầy dầu trước khi vào Tuy Hòa (Petrolimex Sông Cầu)',
      ],
    },
    afternoon: {
      activity: 'Đến Tuy Hòa, check-in',
      details: [
        '14h: nhận phòng (check-in từ 14h)',
        'Nghỉ ngơi, cho bé ngủ trưa',
        '16h–18h: tắm biển nhẹ tại bãi biển Tuy Hòa',
      ],
    },
    evening: {
      activity: 'Khám phá Tuy Hòa',
      details: [
        'Dạo phố Trần Phú',
        'Ăn tối hải sản: bún cá ngừ, gỏi cá mai',
        'Thử bánh tráng nướng đường phố',
      ],
    },
    food: {
      breakfast: 'Bánh mì / bún bò ven QL1A',
      lunch: 'Cơm hộp mang theo',
      dinner: 'Nhà hàng hải sản Tuy Hòa — cá ngừ đại dương must-try',
    },
    childNote: 'Cho bé ăn no trước khi lên xe. Dừng nghỉ mỗi 2h. Mang đồ chơi cho bé trong xe.',
    driveNote: 'HCM → Tuy Hòa: ~550km, 8–9h lái. Nhiên liệu: ~40–50L dầu.',
    importantNote: 'Ngày di chuyển — khởi hành sớm 5h–6h tránh nắng và kẹt xe.',
  },
  {
    day: 2,
    date: '24/05 (CN)',
    theme: 'GÀNH ĐÁ ĐĨA + VỊNH HÒA',
    morning: {
      activity: 'Gành Đá Đĩa',
      details: [
        '5h30: xuất phát (Gành Đá Đĩa cách TH ~90km, 1.5h)',
        '7h–9h: tham quan Gành Đá Đĩa (đá cột basalt — Di sản địa chất quốc gia)',
        '⚠️ Bề mặt đá trơn, bồng hoặc cầm tay bé',
      ],
    },
    afternoon: {
      activity: 'Hòn Yến + Sông Cầu',
      details: [
        '10h–11h: Hòn Yến (san hô đẹp tháng 5)',
        '11h30: ăn trưa Sông Cầu — sò huyết Ô Loan nướng',
        '13h–15h: nghỉ ngơi',
        '15h30–17h30: Vịnh Hòa — bãi biển ít người',
      ],
    },
    evening: {
      activity: 'Hải sản Sông Cầu',
      details: [
        'Ăn hải sản: tôm hùm bông, mực nướng, ốc',
        'Hoặc về Tuy Hòa ăn tối',
      ],
    },
    food: {
      breakfast: 'Bánh căn + chả cá Tuy Hòa',
      lunch: 'Sò huyết Ô Loan — đặc sản Sông Cầu',
      dinner: 'Cá ngừ đại dương câu tay',
    },
    childNote: 'Đeo giày đế cao su cho bé tại Gành Đá Đĩa. Kem SPF50+ + áo dài tay. Tránh để bé đứng sát mép đá.',
    driveNote: 'Tuy Hòa → Gành Đá Đĩa: ~90km, 1.5h. Đổ dầu tại Petrolimex Sông Cầu.',
    importantNote: 'Đi sáng sớm tránh đông và nắng gắt.',
  },
  {
    day: 3,
    date: '25/05 (T2)',
    theme: 'MŨI ĐIỆN / ĐẠI LÃNH + BÃI XÉP',
    morning: {
      activity: 'Mũi Điện — đón bình minh',
      details: [
        '4h30: xuất phát đến Mũi Điện',
        '5h30–7h: BÌNH MINH tại Mũi Điện — đón mặt trời mọc đầu tiên VN',
        '7h30: Bãi Môn — bãi biển hoang sơ nước trong xanh',
        '9h: về nghỉ, ăn sáng muộn',
      ],
    },
    afternoon: {
      activity: 'Bãi Xép',
      details: [
        '11h–13h: ăn trưa + nghỉ trưa (quan trọng với bé)',
        '14h30–16h30: Bãi Xép — bãi trong phim "Hoa Vàng Trên Cỏ Xanh" (sóng nhỏ, an toàn cho bé)',
        '17h: về khách sạn',
      ],
    },
    evening: {
      activity: 'Tuy Hòa thư giãn',
      details: [
        'Ăn tối nhẹ gần khách sạn: bún sứa, bánh hỏi thịt nướng',
        'Mua đặc sản: cá bò khô, cá ngừ khô, mực khô',
      ],
    },
    food: {
      breakfast: 'Cafe + bánh mì mang theo (xuất phát sớm)',
      lunch: 'Bún sứa Phú Yên',
      dinner: 'Bánh hỏi lòng heo',
    },
    childNote: 'Mặc thêm áo sáng sớm tại Mũi Điện (lạnh). Bãi Xép sóng nhỏ — an toàn cho bé tắm. Hôm nay dậy sớm → cho bé ngủ trưa bù.',
    driveNote: 'TH → Mũi Điện: ~40km, 1h. Đường vào nhỏ — Carnival đi được, chạy chậm.',
    importantNote: 'Xuất phát rất sớm để xem BÌNH MINH tại cực Đông Việt Nam.',
  },
  {
    day: 4,
    date: '26/05 (T3)',
    theme: 'ĐẦM Ô LOAN + THÁP NHẠN + THỰ GIÃN',
    morning: {
      activity: 'Tháp Nhạn + Đầm Ô Loan',
      details: [
        '7h–9h: Tháp Nhạn (tháp Chăm, view đẹp)',
        '9h30–11h: Đầm Ô Loan — thuyền kayak ~50–100k/người (phù hợp bé)',
      ],
    },
    afternoon: {
      activity: 'Tự do + hồ bơi',
      details: [
        '11h30: ăn trưa',
        '13h–16h: TỰ DO — hồ bơi khách sạn (bé rất thích)',
        '16h–18h: Chợ Tuy Hòa — mua đặc sản mang về',
      ],
    },
    evening: {
      activity: 'Bữa tối ĐẶC BIỆT',
      details: [
        'Tiệc hải sản: cá ngừ đại dương câu tay (sashimi / nướng / kho)',
        'Bữa đáng nhớ nhất chuyến đi!',
      ],
    },
    food: {
      breakfast: 'Chè Phú Yên, bánh căn',
      lunch: 'Cơm hến, cơm niêu',
      dinner: 'Tiệc hải sản — cá ngừ đại dương câu tay',
    },
    childNote: 'Ngày thư giãn — tốt cho bé phục hồi. Hồ bơi: mang theo phao bơi cho bé. Đổ đầy dầu hôm nay chuẩn bị ngày về.',
    driveNote: 'Di chuyển nội thành, khoảng cách ngắn. Đổ đầy dầu buổi chiều chuẩn bị ngày về.',
    importantNote: 'Ngày thư giãn — phù hợp nghỉ ngơi và khám phá thành phố.',
  },
  {
    day: 5,
    date: '27/05 (T4)',
    theme: 'VỀ NHÀ',
    isReturnDay: true,
    morning: {
      activity: 'Check-out + mua đặc sản',
      details: [
        '6h: ăn sáng lần cuối — bún cá ngừ / mì Quảng',
        '7h: check-out',
        '7h–8h: chợ Tuy Hòa mua đặc sản lần cuối',
        '8h30: đổ đầy dầu rồi lên đường',
      ],
    },
    afternoon: {
      activity: 'Trở về TP.HCM',
      details: [
        'Dừng ăn trưa tại Phan Rang hoặc Phan Thiết',
        'Nghỉ 30 phút cho bé vận động',
      ],
    },
    evening: {
      activity: 'Về đến nhà',
      details: [
        'Dự kiến về nhà 17h–19h',
      ],
    },
    food: {
      breakfast: 'Bún cá ngừ lần cuối',
      lunch: 'Quán ven QL1A',
      dinner: 'Về nhà',
    },
    childNote: 'Chuẩn bị đồ chơi / sách cho chặng về. Cho bé ăn no, uống đủ nước.',
    driveNote: 'Đổ đầy dầu tại Tuy Hòa. Nhiên liệu về: ~40–50L. Tổng nhiên liệu cả chuyến: ~2.200.000–2.600.000đ.',
    importantNote: 'Khởi hành sớm 7h–8h tránh nắng và kẹt xe.',
  },
];

// ── Public API ──────────────────────────────────────────────

/**
 * Get full itinerary
 */
export function getFullItinerary() {
  return DAY_PLANS;
}

/**
 * Get itinerary for a specific day
 */
export function getDayItinerary(dayNumber) {
  return DAY_PLANS.find(d => d.day === dayNumber) || null;
}

/**
 * Get current day of trip
 */
export function getCurrentTripDay() {
  const now = new Date();
  const start = new Date(config.trip.start + 'T00:00:00+07:00');
  const diff = Math.round((now - start) / 86400000);
  if (diff < 0) return { status: 'not_started', daysLeft: Math.ceil(-diff) };
  if (diff > 4) return { status: 'finished' };
  return { status: 'ongoing', day: DAY_PLANS[diff], dayNumber: diff + 1 };
}

/**
 * Build AI-generated itinerary with weather awareness
 */
export async function buildSmartItinerary(days = 5, preferences = {}) {
  const weather = await weatherService.getWeather('Phú Yên');
  const { travelStyle = 'family', budget = 'medium' } = preferences;

  // Get relevant day plans
  const plans = DAY_PLANS.slice(0, days);

  // Enhance with weather info
  const enhancedPlans = plans.map((plan, i) => {
    const dayWeather = weather?.daily?.[i] || null;
    return {
      ...plan,
      weather: dayWeather,
      weatherLabel: dayWeather?.weatherLabel || 'N/A',
      temperature: dayWeather ? `${dayWeather.tmax}°C / ${dayWeather.tmin}°C` : 'N/A',
      hasRainWarning: dayWeather?.precip > 5,
      uvWarning: dayWeather?.uvIndex > 5,
    };
  });

  return enhancedPlans;
}

/**
 * Format itinerary for Telegram
 */
export function formatItineraryForTelegram(plans, lang = 'vi') {
  const lines = [];

  if (lang === 'vi') {
    lines.push('🌴 <b>LỊCH TRÌNH PHÚ YÊN 2026</b>');
    lines.push('Nhóm LV · LH · CM  |  7 người · 1 bé 4 tuổi · Kia Carnival Dầu');
    lines.push('─'.repeat(30));

    plans.forEach(plan => {
      lines.push('');
      lines.push(`📅 <b>NGÀY ${plan.day}: ${plan.date}</b> — ${plan.theme}`);
      if (plan.weather) {
        lines.push(`${plan.weatherLabel} · ${plan.temperature}`);
        if (plan.hasRainWarning) lines.push('⚠️ Có mưa — mang theo ô!');
        if (plan.uvWarning) lines.push('☀️ UV cao — kem chống nắng!');
      }
      lines.push('');
      lines.push('🌅 <b>Sáng:</b>');
      plan.morning.details.forEach(d => lines.push(`  • ${d}`));
      lines.push('☀️ <b>Chiều:</b>');
      plan.afternoon.details.forEach(d => lines.push(`  • ${d}`));
      lines.push('🌙 <b>Tối:</b>');
      plan.evening.details.forEach(d => lines.push(`  • ${d}`));
      lines.push('');
      lines.push(`🍜 <b>Ăn:</b> ${plan.food.breakfast} → ${plan.food.lunch} → ${plan.food.dinner}`);
      lines.push(`👶 <b>Bé:</b> ${plan.childNote}`);
      lines.push(`🚗 <b>Di chuyển:</b> ${plan.driveNote}`);
    });
  } else {
    lines.push('🌴 <b>PHÚ YÊN 2026 ITINERARY</b>');
    plans.forEach(plan => {
      lines.push('');
      lines.push(`📅 <b>Day ${plan.day}: ${plan.date}</b> — ${plan.theme}`);
      lines.push(`🌤️ ${plan.weather?.weatherLabel || 'N/A'} · ${plan.temperature || 'N/A'}`);
      lines.push('');
      lines.push('🚗 Morning:', ...plan.morning.details.map(d => `  • ${d}`));
      lines.push('☀️ Afternoon:', ...plan.afternoon.details.map(d => `  • ${d}`));
      lines.push('🌙 Evening:', ...plan.evening.details.map(d => `  • ${d}`));
      lines.push(`🍜 Meals: ${plan.food.breakfast} → ${plan.food.lunch} → ${plan.food.dinner}`);
    });
  }

  return lines.join('\n');
}