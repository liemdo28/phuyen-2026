// ════════════════════════════════════════════════════════
//  PHÚ YÊN 2026 — AI TRAVEL ASSISTANT
//  Entry point
// ════════════════════════════════════════════════════════

import 'dotenv/config';
import { launchBot } from './bot/index.js';
import config from './config/index.js';

console.log('═══════════════════════════════════════════════');
console.log('  🌴 PHÚ YÊN 2026 — AI TRAVEL ASSISTANT');
console.log('═══════════════════════════════════════════════');
console.log(`  Trip: ${config.trip.name}`);
console.log(`  Dates: ${config.trip.start} → ${config.trip.end}`);
console.log(`  Group: ${config.trip.groupSize} people + 1 child (${config.trip.childAge}y)`);
console.log(`  Vehicle: ${config.trip.car}`);
console.log(`  AI Provider: ${config.ai.provider}`);
console.log(`  Environment: ${config.server.nodeEnv}`);
console.log('═══════════════════════════════════════════════');

// Check configuration
const missingTokens = [];
if (!config.telegram.token) missingTokens.push('TELEGRAM_BOT_TOKEN');
if (!config.ai.openai.apiKey && !config.ai.gemini.apiKey) {
  missingTokens.push('OPENAI_API_KEY or GEMINI_API_KEY');
}

if (missingTokens.length > 0) {
  console.error(`❌ Missing required env vars: ${missingTokens.join(', ')}`);
  console.error('   Copy .env.example to .env and fill in your credentials');
  console.error('   Telegram Bot: create via @BotFather');
  console.error('   AI Key: get from openai.com or aistudio.google.com');
  process.exit(1);
}

// Launch the bot
launchBot();

console.log('');
console.log('🎉 Bot is running! Send a message to your Telegram bot.');
console.log('📖 Check .env for configuration');