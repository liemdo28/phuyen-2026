// ════════════════════════════════════════════════════════
//  INTENT DETECTOR — Classify user message intent
// ════════════════════════════════════════════════════════

import config from '../config/index.js';

/**
 * Detect primary and secondary intents from user text
 */
export function detectIntent(text, context = {}) {
  const t = text.toLowerCase();
  const scores = {};

  for (const [intent, keywords] of Object.entries(config.intents)) {
    scores[intent] = scoreIntent(t, keywords, context);
  }

  // Sort by score
  const sorted = Object.entries(scores)
    .filter(([, score]) => score > 0)
    .sort((a, b) => b[1] - a[1]);

  const primary = sorted[0]?.[0] || 'general';
  const secondary = sorted[1]?.[0] || null;

  return {
    primary,
    secondary,
    scores,
    confidence: sorted[0]?.[1] || 0,
    subIntents: extractSubIntents(text, primary),
  };
}

function scoreIntent(text, keywords, context) {
  let score = 0;
  for (const kw of keywords) {
    // Word boundary match
    const regex = new RegExp(`\\b${escapeRegex(kw)}\\b`, 'i');
    if (regex.test(text)) {
      score += 2;
    } else if (text.includes(kw)) {
      score += 1;
    }
  }
  return score;
}

function escapeRegex(str) {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/**
 * Extract specific sub-intents for richer understanding
 */
function extractSubIntents(text, primaryIntent) {
  const t = text.toLowerCase();
  const subs = [];

  // Time-of-day context
  const hour = new Date().getHours();
  if (hour >= 5 && hour < 11) subs.push('breakfast');
  if (hour >= 11 && hour < 14) subs.push('lunch');
  if (hour >= 14 && hour < 18) subs.push('afternoon');
  if (hour >= 18 && hour < 22) subs.push('dinner');
  if (hour >= 22 || hour < 5) subs.push('latenight');

  // Urgency signals
  if (/khẩn|cấp bách|emergency|ngay|urgently/.test(t)) subs.push('urgent');
  if (/gấp|nhanh/.test(t)) subs.push('time-sensitive');

  // Budget signals
  if (/rẻ|cheap|budget|tiết kiệm|discount/.test(t)) subs.push('budget-conscious');
  if (/ngon|đỉnh|best|top|tuyệt/.test(t)) subs.push('quality-focused');

  // Location signals
  if (/gần|nearby|xung quanh/.test(t)) subs.push('nearby');
  if (/đường về|trên đường|way back/.test(t)) subs.push('on-route');

  // Crowd signals
  if (/vắng|quiet|calm|peaceful|yên tĩnh/.test(t)) subs.push('quiet-preferred');
  if (/đông|busy|crowd|happening/.test(t)) subs.push('lively-preferred');

  // Transport preferences
  if (/metro|tàu|xe buýt|bus/.test(t)) subs.push('public-transport');
  if (/taxi|grab|xe ôm/.test(t)) subs.push('ride-share');

  // Specific intent-dependent extraction
  if (primaryIntent === 'itinerary') {
    const days = text.match(/(\d+)\s*(ngày|day)/i);
    if (days) subs.push(`days:${days[1]}`);
    const city = extractCity(text);
    if (city) subs.push(`city:${city}`);
  }

  if (primaryIntent === 'food') {
    if (/quán|restaurant|nhà hàng/.test(t)) subs.push('restaurant');
    if (/cafe|cà phê|coffee/.test(t)) subs.push('cafe');
    if (/hải sản|seafood/.test(t)) subs.push('seafood');
    if (/mang về|takeaway|delivery/.test(t)) subs.push('takeaway');
    if (/buffet|自助/.test(t)) subs.push('buffet');
  }

  if (primaryIntent === 'budget') {
    const amount = text.match(/(\d+)\s*\$|(\d+)\s*dollars|(\d+)\s*(triệu|tr|k|nghìn)/i);
    if (amount) subs.push(`budget-amount:${amount[0]}`);
  }

  return subs;
}

/**
 * Extract city/destination from text
 */
function extractCity(text) {
  const cities = [
    'tokyo', 'osaka', 'kyoto', 'hanoi', 'hcmc', 'ho chi minh',
    'da nang', 'đà nẵng', 'phú yên', 'tuy hòa', 'vietnam',
    'japan', 'korea', 'thailand', 'bangkok', 'singapore',
  ];
  const t = text.toLowerCase();
  for (const city of cities) {
    if (t.includes(city)) return city;
  }
  return null;
}

/**
 * Detect language of input text (simple heuristic)
 */
export function detectLanguage(text) {
  // Japanese: hiragana/katakana/kanji range
  const jaPatterns = /[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]/;
  // Korean: Hangul range
  const koPatterns = /[\uAC00-\uD7AF\u1100-\u11FF]/;
  // Chinese: CJK range
  const zhPatterns = /[\u4E00-\u9FFF]/;

  if (jaPatterns.test(text)) return 'ja';
  if (koPatterns.test(text)) return 'ko';
  if (zhPatterns.test(text)) return 'zh';

  // Full Vietnamese diacritics set — includes ALL tone marks (à á ã ả ạ etc. were missing before)
  const viDiacritics = /[àáảãạăắằẳẵặâấầẩẫậđèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵ]/i;
  if (viDiacritics.test(text)) return 'vi';

  // No-accent Vietnamese: common words that can't be English
  const viNoAccent = /\b(khong|muon|duoc|ngon|tuoi|biet|uong|nghi|quan|tren|duoi|trong|ngoai|truoc|nhung|cung|that|neu|thi|roi|doi|oke|vl|vcl|ez)\b/i;
  if (viNoAccent.test(text)) return 'vi';

  // Default to Vietnamese — this is a Vietnamese travel app
  return 'vi';
}

/**
 * Map detected intent to handler name
 */
export function intentToHandler(intent, subIntents = []) {
  const handlerMap = {
    food: 'handleFood',
    weather: 'handleWeather',
    hotel: 'handleHotel',
    itinerary: 'handleItinerary',
    transport: 'handleTransport',
    translate: 'handleTranslate',
    emergency: 'handleEmergency',
    budget: 'handleBudget',
    nearby: 'handleNearby',
    safety: 'handleSafety',
    packing: 'handlePacking',
    expense: 'handleExpense',
    local: 'handleLocal',
    general: 'handleGeneral',
  };

  // Check for specific sub-intents that might redirect
  if (subIntents.includes('nearby')) return 'handleNearby';
  if (subIntents.includes('on-route')) return 'handleNearby';

  return handlerMap[intent] || 'handleGeneral';
}