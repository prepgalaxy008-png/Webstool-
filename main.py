import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from aiohttp import web  # Render को खुश रखने के लिए

# Logging
logging.basicConfig(level=logging.INFO)

# Token
API_TOKEN = os.getenv('BOT_TOKEN')
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- 1. Fake Web Server (Render के लिए जुगाड़) ---
async def health_check(request):
    return web.Response(text="Bot is Alive and Running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    # Render जो पोर्ट देगा उसे यूज़ करेंगे, नहीं तो 8080
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logging.info(f"Fake site started on port {port}")

# --- 2. Plagiarism Logic ---
def calculate_similarity(text1, text2):
    try:
        vectorizer = TfidfVectorizer()
        tfidf = vectorizer.fit_transform([text1, text2])
        return cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0] * 100
    except:
        return 0

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer("✅ मैं ऑनलाइन हूँ! टेक्स्ट भेजें: 'Text1' VS 'Text2'")

@dp.message(F.text.contains("VS"))
async def check_text(message: types.Message):
    try:
        parts = message.text.split("VS")
        score = calculate_similarity(parts[0], parts[1])
        result = f"Similarity: {score:.2f}%"
        await message.answer(result)
    except:
        await message.answer("Error!")

# --- 3. Main System ---
async def main():
    # पहले वेब सर्वर स्टार्ट करें
    await start_web_server()
    # फिर बॉट स्टार्ट करें
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
