// ════════════════════════════════════════════════════════
//  CONFIGURATION — PHÚ YÊN 2026 AI TRAVEL ASSISTANT
// ════════════════════════════════════════════════════════

import 'dotenv/config';

const config = {
  // ── Telegram ──────────────────────────────────────────
  telegram: {
    token: process.env.TELEGRAM_BOT_TOKEN || '',
  },

  // ── AI ─────────────────────────────────────────────────
  ai: {
    provider: process.env.OPENAI_API_KEY ? 'openai' : 'gemini',
    openai: {
      apiKey: process.env.OPENAI_API_KEY || '',
      model: process.env.OPENAI_MODEL || 'gpt-4o-mini',
      baseUrl: process.env.OPENAI_BASE_URL || 'https://api.openai.com/v1',
    },
    gemini: {
      apiKey: process.env.GEMINI_API_KEY || '',
      model: process.env.GEMINI_MODEL || 'gemini-2.0-flash',
      baseUrl: 'https://generativelanguage.googleapis.com/v2',
    },
  },

  // ── Weather ─────────────────────────────────────────────
  weather: {
    provider: 'open-meteo', // Free, no API key needed
    timezone: 'Asia/Ho_Chi_Minh',
    // Backup: OpenWeather
    openWeather: {
      apiKey: process.env.OPENWEATHER_API_KEY || '',
      baseUrl: 'https://api.openweathermap.org/data/2.5',
    },
  },

  // ── Places / Maps ───────────────────────────────────────
  places: {
    googleMaps: {
      apiKey: process.env.GOOGLE_PLACES_API_KEY || '',
      baseUrl: 'https://maps.googleapis.com/maps/api',
    },
  },

  // ── Translation ─────────────────────────────────────────
  translation: {
    // Google Cloud Translation API (or use AI for translation)
    apiKey: process.env.TRANSLATION_API_KEY || '',
    // Fallback: use AI model for translation
    useAiFallback: true,
  },

  // ── Database ────────────────────────────────────────────
  db: {
    path: process.env.DATABASE_PATH || './data/travel_assistant.db',
  },

  // ── Server ──────────────────────────────────────────────
  server: {
    port: parseInt(process.env.PORT || '3000'),
    nodeEnv: process.env.NODE_ENV || 'development',
  },

  // ── Trip Configuration ──────────────────────────────────
  trip: {
    name: process.env.TRIP_NAME || 'Phú Yên 2026',
    start: process.env.TRIP_START || '2026-05-23',
    end: process.env.TRIP_END || '2026-05-27',
    groupSize: parseInt(process.env.TRIP_GROUP_SIZE || '7'),
    childAge: parseInt(process.env.TRIP_CHILD_AGE || '4'),
    car: 'Kia Carnival (Dầu Diesel)',
    // Key locations
    locations: {
      'Tuy Hòa (trung tâm)': { lat: 13.0955, lon: 109.3028 },
      'Gành Đá Đĩa': { lat: 14.3912, lon: 109.2144 },
      'Đầm Ô Loan': { lat: 13.4200, lon: 109.2500 },
      'Mũi Điện / Đại Lãnh': { lat: 12.8667, lon: 109.4500 },
      'Bãi Xép': { lat: 13.0150, lon: 109.3280 },
      'Hòn Yến': { lat: 13.2500, lon: 109.3000 },
      'Sông Cầu': { lat: 13.4050, lon: 109.2420 },
    },
  },

  // ── Languages ───────────────────────────────────────────
  languages: {
    default: process.env.DEFAULT_LANGUAGE || 'vi',
    supported: (process.env.SUPPORTED_LANGUAGES || 'vi,en,ja,ko,zh').split(','),
    labels: {
      vi: 'Tiếng Việt',
      en: 'English',
      ja: '日本語',
      ko: '한국어',
      zh: '中文',
    },
  },

  // ── Memory / Context ───────────────────────────────────
  memory: {
    maxHistoryPerUser: 50,
    sessionTTLHours: 72,
    storePreferences: true,
  },

  // ── Intent Categories ──────────────────────────────────
  intents: {
    food: ['food', 'restaurant', 'eat', 'ăn', 'quán', 'đặc sản', 'hải sản', 'ramen', 'cafe', 'bún', 'phở'],
    weather: ['weather', 'thời tiết', 'mưa', 'nắng', '温度', '날씨'],
    hotel: ['hotel', 'khách sạn', 'resort', 'homestay', 'phòng', 'ở', '住宿'],
    itinerary: ['itinerary', 'lịch trình', 'plan', 'kế hoạch', 'ngày', '日程', '여행 일정'],
    transport: ['taxi', 'grab', 'xe', 'metro', 'bus', 'tàu', 'đi', 'đến', 'di chuyển'],
    translate: ['translate', 'dịch', 'nghĩa là', '意味', '번역'],
    emergency: ['hospital', 'bệnh viện', 'cấp cứu', 'emergency', '警察', '경찰', '응급'],
    budget: ['budget', 'tiền', 'chi phí', 'giá', '费用', '예산'],
    nearby: ['nearby', 'gần', 'xung quanh', '附近', '근처'],
    safety: ['scam', 'unsafe', 'warning', 'lừa đảo', 'nguy hiểm', 'cẩn thận'],
    packing: ['đem', 'mang', 'pack', 'đồ', 'vali', 'hành lý'],
    expense: ['chi tiêu', 'tiền', 'bao nhiêu', 'tốn', 'expense'],
    local: ['local', 'địa phương', 'người dân', ' recommendation'],
  },
};

// Validate required config
const required = ['TELEGRAM_BOT_TOKEN'];
const missing = required.filter(k => !process.env[k]);
if (missing.length > 0) {
  console.warn(`⚠️  Missing env vars: ${missing.join(', ')}. Copy .env.example to .env`);
}

export default config;