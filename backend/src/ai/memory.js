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
      budget: 'medium', // cheap, medium, premium
      travelStyle: 'family', // solo, couple, family, business, backpack, luxury
      favoriteFoods: [],
      avoidCrowds: false,
      likesCafes: false,
      likesNature: true,
      likesMuseums: false,
      likesNightlife: false,
    },
    tripContext: {
      currentLocation: null, // { lat, lon, name }
      currentDay: null,
      itinerary: [],
      currentWeather: null,
    },
    history: [], // conversation history
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