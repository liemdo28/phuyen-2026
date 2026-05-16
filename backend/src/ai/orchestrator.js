// ════════════════════════════════════════════════════════
//  AI ORCHESTRATOR — Coordinates all AI operations
// ════════════════════════════════════════════════════════

import { getAIModel } from './model.js';
import { detectIntent, detectLanguage, intentToHandler } from './intent.js';
import { buildContextString, getHistoryForAI, learnPreferences, getSession, updateTripContext } from './memory.js';
import {
  TRAVEL_ASSISTANT_PROMPT,
  FOOD_RECOMMENDATION_PROMPT,
  ITINERARY_PROMPT,
  WEATHER_ADVISORY_PROMPT,
  TRANSLATION_PROMPT,
  LOCAL_EXPERIENCE_PROMPT,
  HANDLE_NEARBY_PROMPT,
} from './prompts.js';
import * as weatherService from '../services/weather.js';
import * as placesService from '../services/places.js';
import * as itineraryService from '../services/itinerary.js';

const ai = getAIModel();

/**
 * Main orchestrator — processes user message and returns AI response
 */
export async function processMessage(userId, text, context = {}) {
  // 1. Detect language
  const lang = detectLanguage(text);

  // 2. Learn preferences from message
  learnPreferences(userId, text);

  // 3. Detect intent
  const intent = detectIntent(text, context);

  // 4. Build context
  const userContext = buildContextString(userId);
  const history = getHistoryForAI(userId, 8);

  // 5. Gather additional context data
  const additionalData = await gatherAdditionalContext(context, intent, userId);

  // 6. Route to appropriate handler and get specialized response
  const specializedResponse = await routeIntent(
    intent,
    text,
    lang,
    userContext,
    additionalData,
    history
  );

  // 7. If specialized handler didn't produce output, use general AI
  const response = specializedResponse || await generateGeneralResponse(
    text, lang, userContext, additionalData, history
  );

  return {
    response,
    intent: intent.primary,
    language: lang,
  };
}

/**
 * Route intent to specialized handler
 */
async function routeIntent(intent, text, lang, userContext, additionalData, history) {
  const handler = intentToHandler(intent.primary, intent.subIntents);

  switch (handler) {
    case 'handleWeather':
      return await handleWeatherIntent(text, lang, additionalData);
    case 'handleFood':
      return await handleFoodIntent(text, lang, userContext, additionalData);
    case 'handleNearby':
      return await handleNearbyIntent(text, lang, userContext, additionalData);
    case 'handleItinerary':
      return await handleItineraryIntent(text, lang, userContext, additionalData);
    case 'handleTransport':
      return await handleTransportIntent(text, lang, userContext, additionalData);
    case 'handleTranslate':
      return await handleTranslateIntent(text, lang);
    case 'handleLocal':
      return await handleLocalIntent(text, lang, userContext);
    case 'handleEmergency':
      return await handleEmergencyIntent(text, lang);
    case 'handleBudget':
      return await handleBudgetIntent(text, lang, userContext);
    case 'handlePacking':
      return await handlePackingIntent(text, lang);
    default:
      return null; // Fall through to general AI
  }
}

// ── Specialized Intent Handlers ─────────────────────────────

async function handleWeatherIntent(text, lang, data) {
  // Check if city is specified
  const cityMatch = text.match(/(?:ở|tại|in|at)\s+([A-Za-zÀ-ÿ\\s]+?)(?:\\s|$|\\?)/i);
  const city = cityMatch ? cityMatch[1].trim() : 'Phú Yên';

  const weather = await weatherService.getWeather(city);
  if (!weather) {
    return lang === 'vi'
      ? `❌ Không lấy được dữ liệu thời tiết cho ${city}. Thử lại nhé!`
      : `❌ Could not get weather data for ${city}. Please try again!`;
  }

  const prompt = WEATHER_ADVISORY_PROMPT + `\n\nCity: ${city}\nWeather data: ${JSON.stringify(weather)}\nUser language: ${lang}`;

  return await ai.complete(
    `Analyze this weather data and give practical travel advice:\n${JSON.stringify(weather, null, 2)}`,
    WEATHER_ADVISORY_PROMPT
  );
}

async function handleFoodIntent(text, lang, userContext, data) {
  const loc = getSession(data.userId)?.tripContext?.currentLocation;
  const places = data.nearbyPlaces || [];

  const placesText = places.slice(0, 6).map(p =>
    `- ${p.name} (${p.area}): ${p.type}, ~${Math.round(p.price / 1000)}k/người, cách ${p.distance?.toFixed(1) ?? '?'}km, giờ mở ${p.openHours}${p.note ? `, ghi chú: ${p.note}` : ''}`
  ).join('\n') || 'Không có dữ liệu quán gần đây';

  const prompt = [
    `User query: "${text}"`,
    `Language: ${lang}`,
    loc
      ? `User GPS location: ${loc.name} (lat ${loc.lat}, lon ${loc.lon}) — dùng distance để ưu tiên quán gần nhất`
      : `User GPS: chưa chia sẻ — dùng quán ở Tuy Hòa làm mặc định`,
    `Database quán (CHỈ dùng những quán này, KHÔNG bịa thêm):\n${placesText}`,
    `User preferences: ${userContext}`,
  ].join('\n');

  return await ai.complete(prompt, FOOD_RECOMMENDATION_PROMPT);
}

async function handleNearbyIntent(text, lang, userContext, data) {
  const loc = getSession(data.userId)?.tripContext?.currentLocation;
  const places = data.nearbyPlaces || [];

  const placesText = places.slice(0, 8).map(p =>
    `- ${p.name} (${p.area}): ${p.type}, ~${Math.round(p.price / 1000)}k/người, cách ${p.distance?.toFixed(1) ?? '?'}km, giờ mở ${p.openHours}${p.note ? `, ${p.note}` : ''}`
  ).join('\n') || 'Không có dữ liệu';

  const prompt = [
    `User query: "${text}"`,
    `Language: ${lang}`,
    loc
      ? `User GPS: ${loc.name} (lat ${loc.lat}, lon ${loc.lon})`
      : `User GPS: chưa chia sẻ`,
    `Địa điểm gần (sắp xếp theo khoảng cách, CHỈ dùng list này):\n${placesText}`,
    `User preferences: ${userContext}`,
  ].join('\n');

  return await ai.complete(prompt, HANDLE_NEARBY_PROMPT);
}

async function handleItineraryIntent(text, lang, userContext, data) {
  const weather = await weatherService.getWeather('Phú Yên');
  const daysMatch = text.match(/(\\d+)\\s*(ngày|day)/i);
  const days = daysMatch ? parseInt(daysMatch[1]) : 3;

  const prompt = [
    `Build a ${days}-day itinerary for Phú Yên, Vietnam.`,
    `Group: 7 people + 1 child (4 years old) — FAMILY trip`,
    `User preferences: ${userContext}`,
    `Current weather in Phú Yên: ${weather ? JSON.stringify(weather) : 'not available'}`,
    `Language: ${lang}`,
    `IMPORTANT: Prioritize child-friendliness and family activities.`,
  ].join('\n');

  return await ai.complete(prompt, ITINERARY_PROMPT);
}

async function handleTransportIntent(text, lang, userContext, data) {
  const session = getSessionContext(data.userId);
  const from = session?.tripContext?.currentLocation?.name || 'current location';
  const toMatch = text.match(/(?:đến|to|去|への)\\s*([A-Za-zÀ-ÿ\\s]+?)(?:\\s|$|\\?)/i);
  const to = toMatch ? toMatch[1].trim() : null;

  const prompt = `User wants transport info: "${text}"
From: ${from}${to ? `\nTo: ${to}` : ''}
User preferences: ${userContext}
Language: ${lang}

Provide practical transport advice for Phú Yên area.`;

  return await ai.complete(prompt, TRAVEL_ASSISTANT_PROMPT);
}

async function handleTranslateIntent(text, lang) {
  // Extract text to translate (remove command keywords)
  const translateMatch = text.match(/(?:dịch|translate|번역|翻訳|翻译)\\s*[:\\s]?\\s*(.+)/i);
  const textToTranslate = translateMatch ? translateMatch[1].trim() : text;

  const prompt = `Translate the following text. Respond in the same language the text is in:\n"${textToTranslate}"`;

  return await ai.complete(prompt, TRANSLATION_PROMPT);
}

async function handleLocalIntent(text, lang, userContext) {
  const prompt = `User wants local, authentic experiences in Phú Yên: "${text}"
User preferences: ${userContext}
Language: ${lang}

Recommend hidden gems and local-only experiences that tourists typically miss.`;

  return await ai.complete(prompt, LOCAL_EXPERIENCE_PROMPT);
}

async function handleEmergencyIntent(text, lang) {
  const places = await placesService.searchPlaces('hospital', 'Tuy Hòa');
  const nearby = places.length > 0 ? places[0] : null;

  const responses = {
    vi: `🚨 Hỗ trợ khẩn cấp!\n\n🅰️ Cấp cứu: 115\n🚔 Police: 113\n🚒 Fire: 114\n\n${nearby ? `🏥 Bệnh viện gần nhất: ${nearby.name}\n📍 ${nearby.address}` : ''}\n\nTôi đã lưu vị trí của bạn để hỗ trợ nếu cần.`,
    en: `🚨 Emergency Support!\n\n🅰️ Ambulance: 115\n🚔 Police: 113\n🚒 Fire: 114\n\n${nearby ? `🏥 Nearest hospital: ${nearby.name}\n📍 ${nearby.address}` : ''}`,
    default: `🚨 Emergency numbers: Ambulance 115, Police 113, Fire 114`,
  };

  return responses[lang] || responses.default;
}

async function handleBudgetIntent(text, lang, userContext) {
  const amountMatch = text.match(/(\\d+)\\s*(?:\\$|USD|triệu|tr|nghìn|k)?/i);
  const budget = amountMatch ? amountMatch[1] : null;

  const prompt = `User asking about budget: "${text}"${budget ? ` (Budget: ${budget})` : ''}
User preferences: ${userContext}
Language: ${lang}
Trip: Phú Yên, Vietnam — 7 people, 1 child, 4 years old, 5 days

Give realistic cost estimates for food, transport, activities in Phú Yên.`;

  return await ai.complete(prompt, TRAVEL_ASSISTANT_PROMPT);
}

async function handlePackingIntent(text, lang) {
  const responses = {
    vi: `📦 Gợi ý đồ cần đem cho chuyến Phú Yên:\n\n👶 Cho bé:\n• Kem chống nắng SPF50+\n• Áo phao bơi\n• Thuốc hạ sốt, thuốc say xe\n• Đồ chơi cho đường dài\n\n🧴 Cho cả nhà:\n• Ô / dù (trời nắng + mưa)\n• Kem chống nắng\n• Thuốc tiêu chảy, băng cứu thương\n• Giấy tờ xe, đăng ký xe\n• Tiền mặt (ATM ít ở vùng biển)\n• Dép sandal, quần áo đi biển\n• Túi nilon chống nước\n• Sạc dự phòng\n\nBạn có muốn tôi đánh dấu đã đem không? Nhắn: \"đã đem [tên đồ]\"`,
    en: `📦 Packing suggestions for Phú Yên trip:\n\n👶 For child:\n• SPF50+ sunscreen\n• Swim float\n• Fever medicine, car sickness medicine\n• Toys for the long drive\n\n🧴 For everyone:\n• Umbrella (sun + rain)\n• Sunscreen\n• Anti-diarrhea medicine, first aid kit\n• Vehicle registration documents\n• Cash (few ATMs near beaches)\n• Sandals, beach clothes\n• Waterproof bags\n• Power bank\n\nShall I mark items as packed? Just say: \"packed [item name]\"`,
    default: `📦 Pack light but prepared! Essentials: sunscreen, umbrella, cash, first aid kit.`,
  };

  return responses[lang] || responses.default;
}

async function generateGeneralResponse(text, lang, userContext, additionalData, history) {
  const session = getSession(additionalData.userId);
  const loc = session?.tripContext?.currentLocation;
  const locationLine = loc
    ? `User's saved location: ${loc.name} (lat: ${loc.lat}, lon: ${loc.lon})`
    : 'User location: not shared yet';

  const prompt = [
    `User message: "${text}"`,
    `Language: ${lang}`,
    locationLine,
    `User preferences: ${userContext}`,
    additionalData.weather
      ? `Current weather in Phú Yên: ${additionalData.weather.description}, ${additionalData.weather.temp}°C`
      : '',
  ].filter(Boolean).join('\n');

  return await ai.complete(prompt, TRAVEL_ASSISTANT_PROMPT, history);
}

async function gatherAdditionalContext(context, intent, userId) {
  const data = { userId };

  try {
    // Get weather if relevant
    if (['weather', 'food', 'nearby', 'general'].includes(intent.primary)) {
      try {
        data.weather = await weatherService.getWeather('Phú Yên');
      } catch (e) { /* ignore */ }
    }

    // Always load nearby places — use GPS if available, else default to Tuy Hoa center
    if (['food', 'nearby', 'general', 'local'].includes(intent.primary)) {
      const loc = getSession(userId)?.tripContext?.currentLocation;
      const lat = loc?.lat || context.location?.lat || 13.0955;
      const lon = loc?.lon || context.location?.lon || 109.3028;
      try {
        data.nearbyPlaces = await placesService.getNearbyPlaces(lat, lon, 'all', 12);
      } catch (e) { /* ignore */ }
    }
  } catch (e) {
    console.error('Error gathering context:', e);
  }

  return data;
}

function getSessionContext(userId) {
  try {
    return getSession(userId);
  } catch (e) {
    return null;
  }
}