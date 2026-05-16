// ════════════════════════════════════════════════════════
//  MEMORY STORE — User preferences & conversation history
// ════════════════════════════════════════════════════════

import NodeCache from 'node-cache';
import { v4 as uuidv4 } from 'uuid';
import config from '../config/index.js';

const memoryCache = new NodeCache({ stdTTL: config.memory.sessionTTLHours * 3600 });

/**
 * Get or create a user session
 */
export function getSession(userId) {
  const key = `session:${userId}`;
  let session = memoryCache.get(key);
  if (!session) {
    session = createNewSession(userId);
    memoryCache.set(key, session);
  }
  return session;
}

function createNewSession(userId) {
  return {
    id: uuidv4(),
    userId,
    preferences: {
      language: config.languages.default,
      budget: 'medium',
      travelStyle: 'family',
      favoriteFoods: [],
      avoidCrowds: false,
      likesCafes: false,
      likesNature: true,
      likesMuseums: false,
      likesNightlife: false,
    },
    tripContext: {
      currentLocation: null,
      currentDay: null,
      itinerary: [],
      currentWeather: null,
    },
    // ── Emotional companion state ──────────────────────────
    companionState: {
      energyLevel: 'normal',        // exhausted | low | normal | hype
      fatigueScore: 0,              // 0–10, accumulates from mệt signals
      lastFatigueAt: null,

      socialMode: 'neutral',        // introvert | hype | healing | lonely | nightlife | neutral
      stressScore: 0,               // 0–10
      lastStressAt: null,

      cognitiveLoad: 'normal',      // normal | overloaded
      consecutiveHeavyMessages: 0,

      crowdTolerance: 'medium',     // low | medium | high
      recoveryStyle: 'cafe',        // cafe | nature | food | rest
      excitementStreak: 0,          // consecutive excited messages
    },
    history: [],
    createdAt: new Date().toISOString(),
    lastActive: new Date().toISOString(),
  };
}

/**
 * Add a message to conversation history
 */
export function addToHistory(userId, role, content, metadata = {}) {
  const session = getSession(userId);
  session.history.push({
    id: uuidv4(),
    role, // 'user' or 'assistant'
    content,
    metadata,
    timestamp: new Date().toISOString(),
  });
  
  // Trim history if too long
  if (session.history.length > config.memory.maxHistoryPerUser) {
    session.history = session.history.slice(-config.memory.maxHistoryPerUser);
  }
  
  session.lastActive = new Date().toISOString();
  memoryCache.set(`session:${userId}`, session);
  return session;
}

/**
 * Update user preferences
 */
export function updatePreferences(userId, updates) {
  const session = getSession(userId);
  session.preferences = { ...session.preferences, ...updates };
  memoryCache.set(`session:${userId}`, session);
  return session.preferences;
}

/**
 * Update trip context
 */
export function updateTripContext(userId, updates) {
  const session = getSession(userId);
  session.tripContext = { ...session.tripContext, ...updates };
  memoryCache.set(`session:${userId}`, session);
  return session.tripContext;
}

/**
 * Extract learned preferences from conversation
 */
export function learnPreferences(userId, text) {
  const t = text.toLowerCase();
  const session = getSession(userId);
  const prefs = session.preferences;
  let updated = false;

  // Budget keywords
  if (/\b(rẻ|cheap|budget|tiet kiem|tiết kiệm|discount)\b/.test(t)) {
    prefs.budget = 'cheap';
    updated = true;
  }
  if (/\b(đắt|expensive|sang trọng|luxury|premium)\b/.test(t)) {
    prefs.budget = 'premium';
    updated = true;
  }

  // Travel style
  if (/\b(một mình|solo|alone)\b/.test(t)) prefs.travelStyle = 'solo';
  if (/\b(couple|2 người|vợ chồng|boyfriend|girlfriend|honeymoon)\b/.test(t)) prefs.travelStyle = 'couple';
  if (/\b(gia đình|family|con nhỏ|bé|trẻ em)\b/.test(t)) prefs.travelStyle = 'family';

  // Food preferences
  const foodKeywords = ['hải sản', 'seafood', 'đặc sản', 'bún', 'phở', 'bánh', 'cơm', 'cafe', 'coffee', 'ramen', 'sushi'];
  foodKeywords.forEach(food => {
    if (t.includes(food) && !prefs.favoriteFoods.includes(food)) {
      prefs.favoriteFoods.push(food);
      updated = true;
    }
  });

  // Activity preferences
  if (/\b(cà phê|cafe|quán|chill|view)\b/.test(t)) { prefs.likesCafes = true; updated = true; }
  if (/\b(biển|beach|ocean|bãi)\b/.test(t)) { prefs.likesNature = true; updated = true; }
  if (/\b(bảo tàng|museum|di tích|lịch sử)\b/.test(t)) { prefs.likesMuseums = true; updated = true; }
  if (/\b(đông|đám đông|crowd|người đông)\b/.test(t)) { prefs.avoidCrowds = true; updated = true; }
  if (/\b(bar|club|beer|đời|nightlife)\b/.test(t)) { prefs.likesNightlife = true; updated = true; }

  if (updated) {
    memoryCache.set(`session:${userId}`, session);
  }
  return prefs;
}

/**
 * Build context string for AI prompt
 */
export function buildContextString(userId) {
  const session = getSession(userId);
  const parts = [];

  parts.push(`Language: ${session.preferences.language}`);
  parts.push(`Budget: ${session.preferences.budget}`);
  parts.push(`Travel Style: ${session.preferences.travelStyle}`);
  parts.push(`Favorite Foods: ${session.preferences.favoriteFoods.join(', ') || 'none specified'}`);
  parts.push(`Avoid Crowds: ${session.preferences.avoidCrowds}`);
  parts.push(`Likes Cafes: ${session.preferences.likesCafes}`);
  parts.push(`Likes Nature: ${session.preferences.likesNature}`);
  parts.push(`Likes Museums: ${session.preferences.likesMuseums}`);

  if (session.tripContext.currentLocation) {
    parts.push(`Current Location: ${session.tripContext.currentLocation.name} (${session.tripContext.currentLocation.lat}, ${session.tripContext.currentLocation.lon})`);
  }
  if (session.tripContext.currentWeather) {
    parts.push(`Current Weather: ${session.tripContext.currentWeather.description}, ${session.tripContext.currentWeather.temp}°C`);
  }
  if (session.tripContext.currentDay) {
    parts.push(`Trip Day: ${session.tripContext.currentDay}`);
  }

  return parts.join('\n');
}

/**
 * Get conversation history for AI context
 */
export function getHistoryForAI(userId, maxMessages = 10) {
  const session = getSession(userId);
  return session.history.slice(-maxMessages);
}

/**
 * Update companion state from extracted signals
 */
export function updateCompanionState(userId, signals) {
  const session = getSession(userId);
  const cs = session.companionState;
  const now = new Date();

  // Fatigue: accumulate, decay 1 point per hour of inactivity
  if (cs.lastFatigueAt) {
    const hoursAgo = (now - new Date(cs.lastFatigueAt)) / 3600000;
    cs.fatigueScore = Math.max(0, cs.fatigueScore - Math.floor(hoursAgo * 0.5));
  }
  cs.fatigueScore = Math.max(0, Math.min(10, cs.fatigueScore + (signals.fatigueDelta || 0)));
  if (signals.fatigueDelta > 0) cs.lastFatigueAt = now.toISOString();

  // Energy level from fatigue score
  if (cs.fatigueScore >= 7) cs.energyLevel = 'exhausted';
  else if (cs.fatigueScore >= 4) cs.energyLevel = 'low';
  else if (signals.excitementSignal && cs.fatigueScore < 3) cs.energyLevel = 'hype';
  else cs.energyLevel = 'normal';

  // Excitement streak
  cs.excitementStreak = signals.excitementSignal ? cs.excitementStreak + 1 : 0;

  // Stress: accumulate, decay per session day
  if (cs.lastStressAt) {
    const hoursAgo = (now - new Date(cs.lastStressAt)) / 3600000;
    cs.stressScore = Math.max(0, cs.stressScore - Math.floor(hoursAgo * 0.3));
  }
  cs.stressScore = Math.max(0, Math.min(10, cs.stressScore + (signals.stressDelta || 0)));
  if (signals.stressDelta > 0) cs.lastStressAt = now.toISOString();

  // Social mode — latest signal wins
  if (signals.socialMode) cs.socialMode = signals.socialMode;
  else if (cs.excitementStreak >= 2) cs.socialMode = 'hype';

  // Cognitive load
  if (signals.cognitiveOverload) {
    cs.consecutiveHeavyMessages = Math.min(5, cs.consecutiveHeavyMessages + 1);
  } else {
    cs.consecutiveHeavyMessages = Math.max(0, cs.consecutiveHeavyMessages - 1);
  }
  cs.cognitiveLoad = cs.consecutiveHeavyMessages >= 2 || cs.fatigueScore >= 6
    ? 'overloaded'
    : 'normal';

  // Crowd tolerance from signals
  if (signals.crowdAvoidance) cs.crowdTolerance = 'low';
  else if (signals.crowdSeeking) cs.crowdTolerance = 'high';

  // Recovery style preference
  if (signals.recoverySignal) {
    const t = signals._rawText || '';
    if (/cafe|cà phê|coffee/.test(t)) cs.recoveryStyle = 'cafe';
    else if (/biển|beach|gió|nature/.test(t)) cs.recoveryStyle = 'nature';
    else if (/ăn|food|quán/.test(t)) cs.recoveryStyle = 'food';
    else cs.recoveryStyle = 'rest';
  }

  memoryCache.set(`session:${userId}`, session);
  return cs;
}

/**
 * Build companion context string to inject before every AI prompt.
 * This is Mi's "thought layer" — computed state the AI uses to adapt.
 */
export function buildCompanionContext(userId) {
  const session = getSession(userId);
  const cs = session.companionState;
  const now = new Date();
  const hour = now.getHours();
  const lines = [];

  // Time-of-day life rhythm
  const timeSlots = [
    [5, 8,   'sáng sớm — người thường còn mơ màng, cần thời gian'],
    [8, 11,  'sáng — năng lượng đang lên, thời điểm tốt để di chuyển'],
    [11, 13, 'trưa nắng gắt — ưu tiên ăn trong mát, hạn chế đi bộ ngoài trời'],
    [13, 15, 'sau ăn trưa — buồn ngủ sinh lý, tránh hoạt động nặng'],
    [15, 17, 'chiều — nắng dịu dần, có thể di chuyển'],
    [17, 19, 'chiều vàng — giờ đẹp nhất để đi biển/ngắm hoàng hôn'],
    [19, 22, 'tối — ăn tối, đi dạo, xã hội hóa'],
    [22, 24, 'khuya — quán bắt đầu thưa, nên gợi ý gần hoặc nghỉ ngơi'],
    [0, 5,   'đêm khuya — chỉ gợi ý cực gần, ưu tiên an toàn'],
  ];
  const slot = timeSlots.find(([from, to]) => hour >= from && hour < to);
  if (slot) lines.push(`Giờ ${String(hour).padStart(2,'0')}:${String(now.getMinutes()).padStart(2,'0')} → ${slot[2]}`);

  // Trip day context
  const createdAt = new Date(session.createdAt);
  const tripDay = Math.floor((now - createdAt) / 86400000) + 1;
  const tripStageMap = { 1: 'ngày đầu — hứng khởi cao', 2: 'ngày 2 — đang nhập cuộc', 3: 'giữa chuyến — có thể mệt tích lũy', 4: 'gần cuối — ưu tiên kỷ niệm hơn di chuyển', 5: 'ngày cuối — nhẹ nhàng, không ép thêm' };
  const stage = tripStageMap[Math.min(tripDay, 5)] || 'đang trong chuyến';
  lines.push(`Ngày ${tripDay} trong chuyến → ${stage}`);

  // Energy & fatigue
  const energyMap = {
    exhausted: 'kiệt sức (mức mệt ' + cs.fatigueScore + '/10) → CHỈ gợi ý nghỉ hoặc ăn gần, câu ngắn, 1 lựa chọn',
    low:       'mệt vừa (mức mệt ' + cs.fatigueScore + '/10) → tối đa 2 lựa chọn, ưu tiên gần',
    hype:      'đang hứng khởi → có thể gợi ý phong phú hơn, match năng lượng',
    normal:    'bình thường',
  };
  lines.push(`Năng lượng: ${energyMap[cs.energyLevel] || cs.energyLevel}`);

  // Social mode
  const socialMap = {
    lonely:    'đang cô đơn → đồng cảm trước, gợi ý chỗ ấm áp/có con người',
    nightlife: 'đang nightlife mood → vui theo, gợi ý quán đêm',
    introvert: 'muốn yên tĩnh → tránh gợi ý chỗ đông',
    hype:      'đang hype → match năng lượng',
    healing:   'đang cần chữa lành → nhẹ nhàng, không ép',
    neutral:   null,
  };
  const socialHint = socialMap[cs.socialMode];
  if (socialHint) lines.push(`Trạng thái xã hội: ${socialHint}`);

  // Cognitive load
  if (cs.cognitiveLoad === 'overloaded') {
    lines.push('Tải nhận thức: OVERLOADED → câu ngắn, không liệt kê, 1 lựa chọn duy nhất');
  }

  // Stress
  if (cs.stressScore >= 4) {
    lines.push(`Stress level ${cs.stressScore}/10 → bình tĩnh hóa trước khi gợi ý`);
  }

  if (lines.length === 0) return '';
  return `[TRẠNG THÁI MI ĐANG NHẬN DIỆN]\n${lines.join('\n')}\n`;
}

/**
 * Clear user session
 */
export function clearSession(userId) {
  memoryCache.del(`session:${userId}`);
}

/**
 * List all active sessions (for admin/debug)
 */
export function getAllSessions() {
  const keys = memoryCache.keys();
  return keys.map(k => {
    const s = memoryCache.get(k);
    return s ? { userId: s.userId, lastActive: s.lastActive, historyLength: s.history.length } : null;
  }).filter(Boolean);
}