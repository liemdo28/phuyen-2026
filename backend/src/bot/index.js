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
    `👋 Xin chào ${firstName}! Mình là AI Travel Assistant cho chuyến Phú Yên 2026!\n\n` +
    `🌴 <b>Chuyến đi:</b> 23–27/05/2026 · 7 người · 1 bé 4 tuổi\n\n` +
    `Mình có thể giúp bạn:\n` +
    `🍜 <b>Tìm quán ăn</b> — gửi vị trí rồi hỏi\n` +
    `🌤️ <b>Thời tiết</b> — dự báo cho Phú Yên\n` +
    `🗺️ <b>Địa điểm gần</b> — gửi vị trí để tìm\n` +
    `📅 <b>Lịch trình</b> — xem chi tiết từng ngày\n` +
    `💰 <b>Chi phí dự kiến</b> — ước tính cho cả nhà\n` +
    `📦 <b>Đồ cần đem</b> — checklist cho chuyến đi\n\n` +
    `Nhắn tự nhiên bằng tiếng Việt, Anh, Nhật, Hàn, Trung đều được!`,
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
  
  // Save location to session
  updateTripContext(userId, {
    currentLocation: {
      lat: latitude,
      lon: longitude,
      name: 'Vị trí hiện tại',
    },
  });
  
  await ctx.reply(
    `📍 Đã lưu vị trí của bạn!\n\n` +
    `Bây giờ hỏi mình những câu như:\n` +
    `• <b>quán ăn gần nhất</b>\n` +
    `• <b>cafe chill gần đây</b>\n` +
    `• <b>quán trên đường về</b>\n` +
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
    
    // For receipt reading, use AI vision
    // For now, respond with guidance
    const responses = {
      vi: `📸 Mình nhận được ảnh!\n\nNếu là <b>hoá đơn</b> → nhắn: \"<b>đọc hoá đơn</b>\" để mình đọc số tiền.\nNếu là <b>địa điểm</b> → mình có thể nhận diện nếu bạn hỏi thêm!\nNếu là <b>thực đơn</b> → nhắn \"<b>dịch thực đơn này</b>\" để mình dịch.`,
      en: `📸 Got your photo!\n\nIf it's a <b>receipt</b> → say \"<b>read receipt</b>\"\nIf it's a <b>place</b> → I can recognize it!\nIf it's a <b>menu</b> → say \"<b>translate this menu</b>\"`,
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
      vi: `🎤 Tính năng chuyển giọng nói đang được cập nhật.\n\nBạn có thể nhắn văn bản thay thế, mình sẽ trả lời ngay!`,
      en: `🎤 Voice message support is being updated.\n\nPlease type your message as text and I'll respond right away!`,
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
    const userContext = {
      location: session?.tripContext?.currentLocation,
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