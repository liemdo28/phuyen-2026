// ════════════════════════════════════════════════════════
//  TELEGRAM BOT — Main bot setup and handlers
// ════════════════════════════════════════════════════════

import { Telegraf, Markup } from 'telegraf';
import config from '../config/index.js';
import { processMessage } from '../ai/orchestrator.js';
import { addToHistory, updateTripContext, getSession } from '../ai/memory.js';
import { detectIntent, detectLanguage } from '../ai/intent.js';
import { formatWeatherForTelegram } from '../services/weather.js';
import { formatPlacesForTelegram, getNearbyPlaces, getPlacesOnRoute } from '../services/places.js';
import { formatItineraryForTelegram, getFullItinerary, buildSmartItinerary } from '../services/itinerary.js';

const bot = new Telegraf(config.telegram.token);

// ── Welcome & Commands ────────────────────────────────────────

bot.start(async (ctx) => {
  const firstName = ctx.from.first_name || 'bạn';
  const userId = String(ctx.from.id);

  await ctx.reply(
    `Ơ ${firstName} ơi 👋 Mình là Mi — bạn đồng hành chuyến Phú Yên 23–27/5 nha!\n\n` +
    `Nhắn tự nhiên thôi, hỏi gì cũng được:\n` +
    `🍜 <b>Ăn gì</b> — quán local ngon, không tourist trap\n` +
    `📍 <b>Gần đây có gì</b> — gửi vị trí rồi hỏi\n` +
    `🌤️ <b>Trời hôm nay</b> — có mưa không, đi được không\n` +
    `📅 <b>Lịch trình</b> — /lichtrinh để xem chi tiết\n` +
    `🚨 <b>Khẩn cấp</b> — nhắn ngay, mình lo\n\n` +
    `Nhắn tiếng Việt, Anh, thậm chí không dấu đều được 😊`,
    { parse_mode: 'HTML' }
  );
});

bot.help(async (ctx) => {
  await ctx.reply(
    `📖 <b>Hướng dẫn sử dụng</b>\n\n` +
    `📍 <b>Gửi vị trí</b> → rồi hỏi \"quán gần nhất\" hoặc \"cafe chill\"\n` +
    `🌤️ <b>Thời tiết</b> → \"Tokyo hôm nay thế nào?\"\n` +
    `📅 <b>Lịch trình</b> → \"build lịch trình 3 ngày\"\n` +
    `🍜 <b>Tìm quán</b> → \"quán hải sản ngon\" hoặc \"cafe view đẹp\"\n` +
    `💰 <b>Chi phí</b> → \"budget 500$ thì đi đâu?\"\n` +
    `📦 <b>Đồ đem</b> → \"danh sách đồ cần đem\"\n` +
    `🌐 <b>Dịch</b> → \"dịch: [text]\" hoặc \"translate: [text]\"\n\n` +
    `Các lệnh:\n` +
    `/xem — xem chi tiêu gần đây\n` +
    `/tong — tổng chi tiêu\n` +
    `/lichtrinh — lịch trình 5 ngày\n` +
    `/thoitiet — thời tiết hôm nay\n` +
    `/id — lấy user ID`,
    { parse_mode: 'HTML' }
  );
});

// ── Slash Commands ────────────────────────────────────────────

bot.command('lichtrinh', async (ctx) => {
  const lang = getSession(String(ctx.from.id))?.preferences?.language || 'vi';
  const plans = await buildSmartItinerary(5);
  await ctx.reply(formatItineraryForTelegram(plans, lang), { parse_mode: 'HTML' });
});

bot.command('thoitiet', async (ctx) => {
  const { getWeather } = await import('../services/weather.js');
  const weather = await getWeather('Phú Yên');
  await ctx.reply(formatWeatherForTelegram(weather), { parse_mode: 'HTML' });
});

bot.command('xem', async (ctx) => {
  await ctx.reply('📋 Chức năng xem chi tiêu đang được cập nhật. Dùng Google Sheet để xem chi tiêu nhé!');
});

bot.command('tong', async (ctx) => {
  await ctx.reply('💰 Tổng chi tiêu: đang cập nhật kết nối với Google Sheet...');
});

bot.command('id', async (ctx) => {
  const userId = ctx.from.id;
  const username = ctx.from.username || '(chưa có)';
  await ctx.reply(
    `🪪 Thông tin của bạn:\n\nUsername: @${username}\nUser ID: <code>${userId}</code>\n\nCopy ID → paste vào Google Sheet để đăng ký.`,
    { parse_mode: 'HTML' }
  );
});

bot.command('reset', async (ctx) => {
  const { clearSession } = await import('../ai/memory.js');
  clearSession(String(ctx.from.id));
  await ctx.reply('🔄 Đã xóa lịch sử trò chuyện. Bắt đầu lại từ đầu!');
});

// ── Location Handler ──────────────────────────────────────────

bot.on('location', async (ctx) => {
  const userId = String(ctx.from.id);
  const { latitude, longitude } = ctx.message.location;

  updateTripContext(userId, {
    currentLocation: {
      lat: latitude,
      lon: longitude,
      name: 'Vị trí hiện tại',
    },
  });

  await ctx.reply(
    `📍 Mi lưu vị trí rồi nha! Giờ hỏi gì cũng được:\n` +
    `• <b>quán ăn gần nhất</b>\n` +
    `• <b>cafe chill gần đây</b>\n` +
    `• <b>hải sản ngon xung quanh</b>`,
    { parse_mode: 'HTML' }
  );
});

// ── Photo Handler (receipt / food / landmark) ──────────────────

bot.on('photo', async (ctx) => {
  const userId = String(ctx.from.id);
  const lang = getSession(userId)?.preferences?.language || 'vi';
  
  await ctx.reply('🔍 Đang phân tích ảnh...');
  
  try {
    // Get the largest photo
    const photo = ctx.message.photo[ctx.message.photo.length - 1];
    const fileLink = await bot.telegram.getFileLink(photo.file_id);
    
    const responses = {
      vi: `📸 Mi nhận ảnh rồi!\n\nHoá đơn → nhắn "<b>đọc hoá đơn</b>"\nThực đơn → nhắn "<b>dịch thực đơn này</b>"\nĐịa điểm → hỏi thêm, mình nhận ra được nha!`,
      en: `📸 Got your photo! Say "<b>read receipt</b>", "<b>translate menu</b>", or ask about the place!`,
    };

    await ctx.reply(responses[lang] || responses.vi, { parse_mode: 'HTML' });
  } catch (e) {
    console.error('Photo handler error:', e);
    await ctx.reply('❌ Lỗi khi xử lý ảnh. Thử lại nhé!');
  }
});

// ── Voice Handler ─────────────────────────────────────────────

bot.on('voice', async (ctx) => {
  const userId = String(ctx.from.id);
  const lang = getSession(userId)?.preferences?.language || 'vi';
  
  await ctx.reply('🎤 Đang chuyển giọng nói thành văn bản...');
  
  try {
    const fileLink = await bot.telegram.getFileLink(ctx.message.voice.file_id);
    
    // Download and convert audio
    const responses = {
      vi: `🎤 Voice chưa hỗ trợ nha — nhắn chữ thôi, Mi trả lời ngay!`,
      en: `🎤 Voice isn't supported yet — just type it and I'll reply!`,
    };

    await ctx.reply(responses[lang] || responses.vi);
  } catch (e) {
    console.error('Voice handler error:', e);
    await ctx.reply('❌ Lỗi xử lý voice. Nhắn văn bản thay thế nhé!');
  }
});

// ── Text Message Handler (AI-powered) ──────────────────────────

bot.on('text', async (ctx) => {
  const userId = String(ctx.from.id);
  const text = ctx.message.text.trim();
  const firstName = ctx.from.first_name || '';
  
  // Skip commands (already handled above)
  if (text.startsWith('/')) return;

  // Typing indicator
  await ctx.sendChatAction('typing');

  try {
    // Get user session for context
    const session = getSession(userId);
    const loc = session?.tripContext?.currentLocation;

    // Direct answer: "where am I?"
    const whereAmI = /\b(đang ở đâu|tôi ở đâu|mình ở đâu|bạn ở đâu|toi o dau|minh o dau|where am i)\b/i;
    if (whereAmI.test(text)) {
      if (loc) {
        await ctx.reply(
          `📍 Vị trí mình đang lưu cho bạn: <b>${loc.name}</b>\n` +
          `Toạ độ: ${loc.lat.toFixed(5)}, ${loc.lon.toFixed(5)}\n\n` +
          `Hỏi thêm "quán gần đây" hoặc "cafe chill" để mình tìm nha!`,
          { parse_mode: 'HTML' }
        );
      } else {
        await ctx.reply('Bạn chưa gửi vị trí cho Mi nha! Bấm 📎 → Location để gửi rồi Mi tìm chỗ gần liền.');
      }
      addToHistory(userId, 'user', text, { intent: 'nearby' });
      return;
    }

    const userContext = {
      location: loc,
      language: session?.preferences?.language,
    };

    // Process through AI orchestrator
    const result = await processMessage(userId, text, userContext);
    
    // Add to conversation history
    addToHistory(userId, 'user', text, { intent: result.intent });
    addToHistory(userId, 'assistant', result.response, { intent: result.intent });
    
    // Send response
    await ctx.reply(result.response, { parse_mode: 'HTML' });
    
  } catch (e) {
    console.error('Message handler error:', e);
    
    // Fallback response
    const fallbacks = {
      vi: `😅 Xin lỗi, mình đang gặp chút trục trặc. Thử lại nhé!`,
      en: `😅 Sorry, I'm having some trouble. Please try again!`,
    };
    
    const lang = getSession(userId)?.preferences?.language || 'vi';
    await ctx.reply(fallbacks[lang] || fallbacks.vi);
  }
});

// ── Inline Query (optional) ───────────────────────────────────

bot.on('inline_query', async (ctx) => {
  // For future inline bot functionality
  await ctx.answerInlineQuery([], { cache_time: 0 });
});

// ── Error Handler ─────────────────────────────────────────────

bot.catch((err, ctx) => {
  console.error('Bot error:', err);
  ctx.reply('❌ An error occurred. Please try again.').catch(() => {});
});

// ── Launch ────────────────────────────────────────────────────

export function launchBot() {
  console.log('🤖 Launching Telegram Bot...');
  bot.launch()
    .then(() => {
      console.log('✅ Telegram Bot is running!');
      console.log(`📱 Bot username: @${bot.options.username || 'PhuYen2026Bot'}`);
    })
    .catch(err => {
      console.error('❌ Failed to launch bot:', err);
    });
  
  // Graceful shutdown
  process.once('SIGINT', () => {
    console.log('Shutting down...');
    bot.stop('SIGINT');
    process.exit(0);
  });
  process.once('SIGTERM', () => {
    console.log('Shutting down...');
    bot.stop('SIGTERM');
    process.exit(0);
  });
}

export { bot };