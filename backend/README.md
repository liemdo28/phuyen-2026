# 🌴 Phú Yên 2026 — AI Travel Assistant

AI-powered Telegram bot for the Phú Yên family trip (May 23–27, 2026). 7 adults + 1 child (4 years old), Kia Carnival (Diesel).

## Features

- **AI-powered natural conversation** — responds like a local friend, not a chatbot
- **Multi-language** — Vietnamese, English, Japanese, Korean, Chinese
- **Intent detection** — understands food, weather, itinerary, transport, translation, emergency, budget requests
- **Memory system** — remembers user preferences and conversation context
- **Real-time weather** — Open-Meteo API (free, no key required)
- **Restaurant database** — local Phú Yên restaurants with ratings, prices, and locations
- **Smart itinerary** — 5-day trip planner with weather awareness
- **Location-aware** — find nearby places by sharing your location
- **Multi-format support** — text, voice, photos, location

## Supported Queries

```
"Có gì ăn ngon gần đây?"
"Weather hôm nay sao?"
"Tôi đang ở Tokyo, build lịch trình 3 ngày"
"Cafe nào chill gần tôi?"
"Quán nào mở khuya?"
"Budget 500$ thì nên đi đâu?"
"Tôi muốn local experience"
"Biển hôm nay có đẹp không?"
"dịch: この料理是何ですか"
"翻訳: Where is the nearest hospital?"
```

## Quick Start

### 1. Install dependencies

```bash
cd backend
npm install
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and fill in:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
OPENAI_API_KEY=your_openai_key
```

**Getting a Telegram Bot Token:**
1. Open Telegram → search for `@BotFather`
2. Send `/newbot`
3. Follow instructions, copy the token

**Getting an OpenAI API Key:**
1. Go to [platform.openai.com](https://platform.openai.com)
2. API Keys → Create new key
3. Copy to `.env`

### 3. Run the bot

```bash
npm run dev
```

### 4. Test

1. Open Telegram, search for your bot username
2. Send `/start`
3. Try: "thời tiết hôm nay", "quán ăn ngon", "build lịch trình"

## Project Structure

```
backend/
├── src/
│   ├── index.js              # Entry point
│   ├── config/
│   │   └── index.js          # All configuration
│   ├── bot/
│   │   └── index.js          # Telegram bot + handlers
│   ├── ai/
│   │   ├── model.js          # OpenAI / Gemini adapter
│   │   ├── memory.js         # User session & preferences
│   │   ├── intent.js         # Intent detection
│   │   ├── orchestrator.js   # AI routing & response
│   │   └── prompts.js        # System prompts
│   ├── services/
│   │   ├── weather.js        # Open-Meteo weather API
│   │   ├── places.js         # Restaurant & places database
│   │   └── itinerary.js      # Trip planner
│   └── utils/
│       └── distance.js       # Haversine distance calc
├── package.json
├── .env.example
└── README.md
```

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message |
| `/help` | Usage guide |
| `/lichtrinh` | Full 5-day itinerary |
| `/thoitiet` | Weather for Phú Yên |
| `/xem` | Recent expenses |
| `/tong` | Total expenses |
| `/id` | Get your Telegram user ID |
| `/reset` | Clear conversation history |

## Architecture

```
User Message → Telegram Bot
       ↓
Intent Detection (rule-based keyword scoring)
       ↓
Context Gathering (weather, location, preferences, history)
       ↓
AI Orchestrator (routes to specialized handlers)
       ↓
Specialized Handler (weather / food / itinerary / etc.)
       ↓
AI Model (GPT-4o or Gemini) generates response
       ↓
Telegram Response (HTML formatted)
```

## AI Features

### Intent Detection
Classifies messages into: food, weather, hotel, itinerary, transport, translate, emergency, budget, nearby, safety, packing, expense, local, general

### Memory System
- Stores conversation history per user (last 50 messages)
- Learns preferences: budget, travel style, favorite foods, activity preferences
- Remembers current location
- 72-hour session TTL

### Context Awareness
1. User's location (from Telegram location sharing)
2. Current weather in Phú Yên
3. Time of day
4. User preferences (learned over time)
5. Conversation history
6. Trip context (current day of trip)

## API Integrations

| Service | API | API Key Required |
|---------|-----|-----------------|
| Telegram Bot | Bot API | Yes (free) |
| OpenAI / GPT | OpenAI API | Yes |
| Google Gemini | Gemini API | Yes |
| Weather | Open-Meteo | No (free) |
| Places Search | Google Places | Optional |

## Adding New Places

Edit `src/services/places.js` and add to `LOCAL_PLACES`:

```javascript
{
  name: 'Your Restaurant Name',
  type: '🍜 Vietnamese',
  area: 'Tuy Hòa',
  price: 50000,
  lat: 13.1234,
  lon: 109.5678,
  rating: 4.5,
  onRoute: true,
  note: 'Famous for...',
  openHours: '7:00 - 22:00',
  childFriendly: true,
  cuisine: 'local',
  ambience: 'casual',
},
```

## Deployment

### Local (development)
```bash
npm run dev
```

### Production (with PM2)
```bash
npm install -g pm2
pm2 start src/index.js --name phuyen-bot
pm2 save
pm2 startup
```

### Railway / Render / Fly.io
Set environment variables in the dashboard:
- `TELEGRAM_BOT_TOKEN`
- `OPENAI_API_KEY`
- `NODE_ENV=production`

## Google Sheets Integration

The existing Google Apps Script (`Code.js`) manages:
- Expense tracking
- Packing lists
- Weather data
- Daily briefings

This Node.js bot is a complementary AI layer on top of the same trip data.

## Troubleshooting

**Bot not responding?**
- Check `.env` has valid `TELEGRAM_BOT_TOKEN`
- Verify bot token format: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`

**AI responses slow?**
- OpenAI API latency varies; add `@` mention to bot in group for faster polling
- Consider upgrading to GPT-4 for better responses

**Weather not loading?**
- Open-Meteo is free and doesn't need an API key
- Check internet connection

**Location not working?**
- Users must share live location, not a screenshot
- Telegram → Attachment → Location → Share Live Location

## License

Internal project — Phú Yên 2026 Trip