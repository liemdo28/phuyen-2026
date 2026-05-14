// ════════════════════════════════════════════════════════
//  WEATHER SERVICE — Open-Meteo + OpenWeather
// ════════════════════════════════════════════════════════

import axios from 'axios';
import config from '../config/index.js';

const WX_LABELS = {
  0: '☀️ Trời quang', 1: '🌤️ Ít mây', 2: '⛅ Nhiều mây', 3: '☁️ Âm u',
  45: '🌫️ Sương mù', 48: '🌫️ Sương đá',
  51: '🌦️ Mưa phùn nhẹ', 53: '🌦️ Mưa phùn', 55: '🌧️ Mưa phùn nặng',
  61: '🌧️ Mưa nhẹ', 63: '🌧️ Mưa vừa', 65: '🌧️ Mưa to',
  80: '🌦️ Mưa rào nhẹ', 81: '🌧️ Mưa rào', 82: '⛈️ Mưa rào nặng',
  95: '⛈️ Giông', 96: '⛈️ Giông + đá', 99: '⛈️ Giông lớn',
};

// City coordinates lookup
const CITY_COORDS = {
  'tuy hòa': { lat: 13.0955, lon: 109.3028 },
  'tuy hoa': { lat: 13.0955, lon: 109.3028 },
  'phú yên': { lat: 13.0955, lon: 109.3028 },
  'phu yen': { lat: 13.0955, lon: 109.3028 },
  'gành đá đĩa': { lat: 14.3912, lon: 109.2144 },
  'ganh da dia': { lat: 14.3912, lon: 109.2144 },
  'đầm ô loan': { lat: 13.4200, lon: 109.2500 },
  'dam o loan': { lat: 13.4200, lon: 109.2500 },
  'mũi điện': { lat: 12.8667, lon: 109.4500 },
  'mui dien': { lat: 12.8667, lon: 109.4500 },
  'bãi xép': { lat: 13.0150, lon: 109.3280 },
  'bai xep': { lat: 13.0150, lon: 109.3280 },
  'hòn yến': { lat: 13.2500, lon: 109.3000 },
  'hon yen': { lat: 13.2500, lon: 109.3000 },
  'sông cầu': { lat: 13.4050, lon: 109.2420 },
  'song cau': { lat: 13.4050, lon: 109.2420 },
  'hồ chí minh': { lat: 10.8231, lon: 106.6297 },
  'ho chi minh': { lat: 10.8231, lon: 106.6297 },
  'hcmc': { lat: 10.8231, lon: 106.6297 },
  'hà nội': { lat: 21.0285, lon: 105.8542 },
  'ha noi': { lat: 21.0285, lon: 105.8542 },
  'đà nẵng': { lat: 16.0544, lon: 108.2022 },
  'da nang': { lat: 16.0544, lon: 108.2022 },
  'tokyo': { lat: 35.6762, lon: 139.6503 },
  'osaka': { lat: 34.6937, lon: 135.5023 },
  'kyoto': { lat: 35.0116, lon: 135.7681 },
  'nha trang': { lat: 12.2388, lon: 109.1967 },
  'vung tau': { lat: 10.3520, lon: 107.0845 },
};

/**
 * Get weather for a city
 */
export async function getWeather(city) {
  const normalized = city.toLowerCase().trim();
  const coords = CITY_COORDS[normalized];

  if (!coords) {
    // Try to geocode via OpenStreetMap Nominatim
    try {
      const geoResult = await geocodeCity(city);
      if (geoResult) {
        return await fetchOpenMeteo(geoResult.lat, geoResult.lon, city);
      }
    } catch (e) {
      console.error('Geocoding failed:', e);
    }
    return null;
  }

  return await fetchOpenMeteo(coords.lat, coords.lon, city);
}

/**
 * Get weather for coordinates
 */
export async function getWeatherByCoords(lat, lon) {
  return await fetchOpenMeteo(lat, lon, 'current location');
}

/**
 * Fetch from Open-Meteo (free, no API key)
 */
async function fetchOpenMeteo(lat, lon, placeName) {
  try {
    const url = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}` +
      `&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m,wind_direction_10m` +
      `&hourly=temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code,wind_speed_10m_max,uv_index_max` +
      `&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max,uv_index_max` +
      `&timezone=Asia%2FHo_Chi_Minh&forecast_days=5`;

    const response = await axios.get(url, { timeout: 10000 });
    const data = response.data;

    if (!data) return null;

    return {
      place: placeName,
      current: {
        temperature: data.current?.temperature_2m,
        feelsLike: data.current?.apparent_temperature,
        humidity: data.current?.relative_humidity_2m,
        precipitation: data.current?.precipitation,
        weatherCode: data.current?.weather_code,
        weatherLabel: WX_LABELS[data.current?.weather_code] || `(${data.current?.weather_code})`,
        windSpeed: data.current?.wind_speed_10m,
        windDirection: data.current?.wind_direction_10m,
      },
      hourly: formatHourly(data.hourly),
      daily: formatDaily(data.daily),
      today: {
        tmax: data.daily?.temperature_2m_max?.[0],
        tmin: data.daily?.temperature_2m_min?.[0],
        precip: data.daily?.precipitation_sum?.[0],
        uvIndex: data.daily?.uv_index_max?.[0],
        weatherLabel: WX_LABELS[data.daily?.weather_code?.[0]] || '',
      },
      assessment: assessWeather(data.current?.weather_code, data.daily?.precipitation_sum?.[0]),
    };
  } catch (e) {
    console.error('Open-Meteo error:', e.message);
    return null;
  }
}

/**
 * Geocode city name to coordinates via Nominatim
 */
async function geocodeCity(city) {
  try {
    const response = await axios.get(
      `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(city)}&format=json&limit=1`,
      {
        headers: { 'User-Agent': 'PhuYenTravelBot/1.0' },
        timeout: 5000,
      }
    );
    if (response.data?.[0]) {
      return {
        lat: parseFloat(response.data[0].lat),
        lon: parseFloat(response.data[0].lon),
      };
    }
  } catch (e) {
    // ignore
  }
  return null;
}

function formatHourly(hourly) {
  if (!hourly) return [];
  return hourly.time?.slice(0, 24).map((t, i) => ({
    time: t,
    temp: hourly.temperature_2m?.[i],
    weatherCode: hourly.weather_code?.[i],
    weatherLabel: WX_LABELS[hourly.weather_code?.[i]] || '',
  })) || [];
}

function formatDaily(daily) {
  if (!daily) return [];
  return daily.time?.map((t, i) => ({
    date: t,
    tmax: daily.temperature_2m_max?.[i],
    tmin: daily.temperature_2m_min?.[i],
    precip: daily.precipitation_sum?.[i],
    uvIndex: daily.uv_index_max?.[i],
    weatherCode: daily.weather_code?.[i],
    weatherLabel: WX_LABELS[daily.weather_code?.[i]] || '',
  })) || [];
}

/**
 * Assess if weather is good for outdoor activities
 */
function assessWeather(weatherCode, precip) {
  if (!weatherCode) return '⚠️ Không rõ';
  if (weatherCode <= 3 && precip < 5) return '✅ Đẹp — thích hợp ra ngoài';
  if (weatherCode <= 55 && precip < 15) return '⚠️ Được — cần chú ý';
  if (weatherCode >= 95) return '❌ Có giông — tránh hoạt động ngoài trời';
  return '⚠️ Có mưa — mang theo ô';
}

/**
 * Build weather summary for Telegram
 */
export function formatWeatherForTelegram(weather) {
  if (!weather) return '❌ Không lấy được thời tiết.';

  const lines = [];
  lines.push(`🌤️ <b>${weather.place}</b>`);
  lines.push(`📍 Hiện tại: ${weather.current.weatherLabel}`);
  lines.push(`🌡️ ${weather.current.temperature}°C (cảm giác ${weather.current.feelsLike}°C)`);
  lines.push(`💧 Độ ẩm: ${weather.current.humidity}%`);
  lines.push(`🌧️ Mưa: ${weather.current.precipitation}mm`);
  lines.push(`💨 Gió: ${weather.current.windSpeed}km/h`);
  lines.push(`─`.repeat(20));
  lines.push(`📅 Hôm nay: ${weather.today.weatherLabel}`);
  lines.push(`   Tmax ${weather.today.tmax}°C / Tmin ${weather.today.tmin}°C`);
  lines.push(`   Mưa: ${weather.today.precip}mm`);
  if (weather.today.uvIndex > 5) lines.push(`   ⚠️ UV cao: ${weather.today.uvIndex} — cần kem chống nắng!`);
  lines.push(`─`.repeat(20));
  lines.push(`📊 Đánh giá: <b>${weather.assessment}</b>`);

  // 3-day forecast
  if (weather.daily?.length > 1) {
    lines.push(`\n📆 <b>Dự báo 3 ngày tới:</b>`);
    weather.daily.slice(1, 4).forEach(d => {
      const dayName = new Date(d.date).toLocaleDateString('vi-VN', { weekday: 'short', day: 'numeric', month: 'numeric' });
      lines.push(`${dayName}: ${d.weatherLabel} · ${d.tmax}°C / ${d.tmin}°C · Mưa ${d.precip}mm`);
    });
  }

  return lines.join('\n');
}