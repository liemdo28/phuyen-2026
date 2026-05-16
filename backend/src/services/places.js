// ════════════════════════════════════════════════════════
//  PLACES SERVICE — Google Places + Local Database
// ════════════════════════════════════════════════════════

import axios from 'axios';
import config from '../config/index.js';
import { haversine } from '../utils/distance.js';

// ── Local Phú Yên Restaurant Database ───────────────────────
const LOCAL_PLACES = [
  {
    name: 'Quán Bún Cá Ngừ Bà Hai',
    type: '🍜 Bún/Mì',
    area: 'Tuy Hòa',
    price: 40000,
    lat: 13.0982,
    lon: 109.2970,
    rating: 4.5,
    onRoute: true,
    note: 'Must try — cá ngừ đại dương tươi',
    openHours: '6:00 - 14:00',
    childFriendly: true,
    cuisine: 'seafood',
    ambience: 'casual',
  },
  {
    name: 'Bánh Căn Ngọc Lan',
    type: '🥞 Bánh',
    area: 'Tuy Hòa',
    price: 30000,
    lat: 13.0962,
    lon: 109.2958,
    rating: 4.3,
    onRoute: true,
    note: 'Sáng sớm 6h–9h',
    openHours: '6:00 - 9:00',
    childFriendly: true,
    cuisine: 'local',
    ambience: 'casual',
  },
  {
    name: 'Bún Sứa Đặc Sản',
    type: '🍜 Bún/Mì',
    area: 'Tuy Hòa',
    price: 35000,
    lat: 13.0935,
    lon: 109.2962,
    rating: 4.6,
    onRoute: true,
    note: 'Phải thử ở Phú Yên',
    openHours: '6:00 - 14:00',
    childFriendly: true,
    cuisine: 'local',
    ambience: 'casual',
  },
  {
    name: 'Bánh Hỏi Lòng Heo',
    type: '🍽️ Đặc sản',
    area: 'Tuy Hòa',
    price: 45000,
    lat: 13.0948,
    lon: 109.2975,
    rating: 4.4,
    onRoute: true,
    note: 'Đặc sản Phú Yên',
    openHours: '7:00 - 20:00',
    childFriendly: true,
    cuisine: 'local',
    ambience: 'casual',
  },
  {
    name: 'Mì Quảng Bà Mua',
    type: '🍜 Bún/Mì',
    area: 'Tuy Hòa',
    price: 35000,
    lat: 13.0965,
    lon: 109.2980,
    rating: 4.2,
    onRoute: true,
    note: '',
    openHours: '6:00 - 14:00',
    childFriendly: true,
    cuisine: 'local',
    ambience: 'casual',
  },
  {
    name: 'Hải Sản Sông Biển',
    type: '🦞 Hải sản',
    area: 'Tuy Hòa',
    price: 150000,
    lat: 13.0945,
    lon: 109.3150,
    rating: 4.5,
    onRoute: false,
    note: 'Tôm hùm, mực nướng',
    openHours: '10:00 - 22:00',
    childFriendly: true,
    cuisine: 'seafood',
    ambience: 'restaurant',
  },
  {
    name: 'Sò Huyết Ô Loan',
    type: '🦞 Hải sản',
    area: 'Sông Cầu',
    price: 80000,
    lat: 13.4200,
    lon: 109.2500,
    rating: 4.7,
    onRoute: false,
    note: 'Gần Đầm Ô Loan — đặc sản',
    openHours: '8:00 - 20:00',
    childFriendly: true,
    cuisine: 'seafood',
    ambience: 'casual',
  },
  {
    name: 'Tôm Hùm Sông Cầu',
    type: '🦞 Hải sản',
    area: 'Sông Cầu',
    price: 200000,
    lat: 13.4050,
    lon: 109.2420,
    rating: 4.8,
    onRoute: false,
    note: 'Ngon nhất vùng',
    openHours: '9:00 - 21:00',
    childFriendly: true,
    cuisine: 'seafood',
    ambience: 'restaurant',
  },
  {
    name: 'Quán Hải Sản Gành Đá Đĩa',
    type: '🦞 Hải sản',
    area: 'Sông Cầu',
    price: 120000,
    lat: 14.3880,
    lon: 109.2160,
    rating: 4.3,
    onRoute: false,
    note: 'Gần Gành Đá Đĩa',
    openHours: '8:00 - 20:00',
    childFriendly: true,
    cuisine: 'seafood',
    ambience: 'casual',
  },
  {
    name: 'Cafe Biển Bãi Xép',
    type: '☕ Cà phê',
    area: 'Bãi Xép',
    price: 30000,
    lat: 13.0150,
    lon: 109.3280,
    rating: 4.6,
    onRoute: false,
    note: 'View biển đẹp',
    openHours: '6:00 - 22:00',
    childFriendly: true,
    cuisine: 'cafe',
    ambience: 'cafe',
  },
  {
    name: 'Quán Cá Ngừ Đại Dương',
    type: '🦞 Hải sản',
    area: 'Tuy Hòa',
    price: 100000,
    lat: 13.0950,
    lon: 109.2985,
    rating: 4.5,
    onRoute: true,
    note: 'Cá ngừ đại dương câu tay — must try',
    openHours: '10:00 - 22:00',
    childFriendly: true,
    cuisine: 'seafood',
    ambience: 'restaurant',
  },
  {
    name: 'Bánh Tráng Nướng Đường Phố',
    type: '🍽️ Đặc sản',
    area: 'Tuy Hòa',
    price: 15000,
    lat: 13.0968,
    lon: 109.3010,
    rating: 4.4,
    onRoute: true,
    note: 'Đặc sản đường phố — ăn đêm',
    openHours: '18:00 - 23:00',
    childFriendly: false,
    cuisine: 'street',
    ambience: 'street',
  },
];

// ── Google Places API ───────────────────────────────────────
async function searchGooglePlaces(query, location, radius = 5000) {
  if (!config.places.googleMaps.apiKey) return [];
  
  try {
    const url = `${config.places.googleMaps.baseUrl}/place/textsearch/json`;
    const params = {
      query: `${query} ${location}`,
      key: config.places.googleMaps.apiKey,
      language: 'vi',
    };
    const response = await axios.get(url, { params, timeout: 8000 });
    return (response.data.results || []).map(formatGooglePlace);
  } catch (e) {
    console.error('Google Places error:', e.message);
    return [];
  }
}

function formatGooglePlace(result) {
  return {
    name: result.name,
    address: result.formatted_address || result.vicinity || '',
    rating: result.rating || 0,
    lat: result.geometry?.location?.lat,
    lon: result.geometry?.location?.lng,
    openNow: result.opening_hours?.open_now,
    types: result.types || [],
    placeId: result.place_id,
    priceLevel: result.price_level,
  };
}

// ── Public API ──────────────────────────────────────────────

/**
 * Find places near coordinates
 */
export async function getNearbyPlaces(lat, lon, type = 'restaurant', limit = 10) {
  const all = await getAllNearbyPlaces(lat, lon);
  
  let filtered = all;
  if (type && type !== 'all') {
    filtered = all.filter(p => {
      const typeLower = type.toLowerCase();
      return p.type.toLowerCase().includes(typeLower) ||
             p.cuisine?.includes(typeLower) ||
             p.name.toLowerCase().includes(typeLower);
    });
  }
  
  return filtered.slice(0, limit);
}

/**
 * Get all nearby places sorted by distance
 */
export async function getAllNearbyPlaces(lat, lon) {
  const withDistance = LOCAL_PLACES.map(place => ({
    ...place,
    distance: haversine(lat, lon, place.lat, place.lon),
  })).sort((a, b) => a.distance - b.distance);
  
  return withDistance;
}

/**
 * Find places along route (near resort)
 */
export async function getPlacesOnRoute(lat, lon) {
  const resort = { lat: 13.0955, lon: 109.3028 }; // Tuy Hòa center
  const direct = haversine(lat, lon, resort.lat, resort.lon);
  
  const onRoute = LOCAL_PLACES
    .filter(p => p.onRoute)
    .map(place => {
      const dist = haversine(lat, lon, place.lat, place.lon);
      const detour = dist + haversine(place.lat, place.lon, resort.lat, resort.lon) - direct;
      return { ...place, distance: dist, detour };
    })
    .filter(p => p.detour < Math.max(5, direct * 0.25))
    .sort((a, b) => a.detour - b.detour);
  
  return onRoute;
}

/**
 * Search places by query
 */
export async function searchPlaces(query, area = 'Phú Yên') {
  // First check local database
  const localResults = LOCAL_PLACES.filter(p =>
    p.name.toLowerCase().includes(query.toLowerCase()) ||
    p.type.toLowerCase().includes(query.toLowerCase()) ||
    p.note.toLowerCase().includes(query.toLowerCase())
  );
  
  // Then try Google Places API
  const googleResults = await searchGooglePlaces(query, area);
  
  return [...localResults, ...googleResults].slice(0, 15);
}

/**
 * Format places for Telegram display
 */
export function formatPlacesForTelegram(places, title = '📍 Địa điểm gần bạn:') {
  if (!places.length) return '❌ Không tìm thấy địa điểm phù hợp.';
  
  const lines = [`${title}\n`];
  places.slice(0, 5).forEach((p, i) => {
    const stars = p.rating ? '⭐'.repeat(Math.round(p.rating)) : '';
    const distance = p.distance !== undefined ? `📏 ${p.distance.toFixed(1)}km` : '';
    const price = p.price ? `💰 ~${(p.price / 1000).toFixed(0)}k/người` : '';
    
    lines.push(`${i + 1}. <b>${p.name}</b>${stars ? ` ${stars}` : ''}`);
    lines.push(`   ${p.type} · ${distance} ${price}`.trim());
    if (p.openHours) lines.push(`   🕐 ${p.openHours}`);
    if (p.note) lines.push(`   💬 ${p.note}`);
    lines.push('');
  });
  
  lines.push('💡 Gửi vị trí để cập nhật khoảng cách chính xác.');
  return lines.join('\n');
}