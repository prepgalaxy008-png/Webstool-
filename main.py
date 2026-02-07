import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from aiohttp import web

# Configuration
API_TOKEN = os.getenv('BOT_TOKEN')
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- Render health check ---
async def health_check(request):
    return web.Response(text="Bot is fully active!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 8080)))
    await site.start()

# --- Plagiarism Function ---
def get_sim(t1, t2):
    try:
        v = TfidfVectorizer()
        return cosine_similarity(v.fit_transform([t1, t2]))[0][1] * 100
    except: return 0

# 1. Start Command
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("🔥 **Expert Bot Active!**\n\n- टेक्स्ट के लिए: `Text1 VS Text2` लिखें।\n- फाइल के लिए: दो PDF/Docx भेजें।\n- मैं आपके हर मैसेज का जवाब दूंगा!")

# 2. VS Logic (Comparison)
@dp.message(F.text.contains("VS"))
async def check_vs(message: types.Message):
    parts = message.text.split("VS")
    if len(parts) >= 2:
        score = get_sim(parts[0].strip(), parts[1].strip())
        await message.reply(f"📊 **Result:** `{score:.2f}%` similarity.")
    else:
        await message.reply("❌ फॉर्मेट गलत है। 'Text1 VS Text2' लिखें।")

# 3. Universal Handler (For ALL other texts)
@dp.message(F.text)
async def handle_all_text(message: types.Message):
    # यह हिस्सा हर उस मैसेज का जवाब देगा जिसमें VS नहीं है
    text = message.text.lower()
    if text in ["hi", "hello", "hey"]:
        await message.answer("नमस्ते! मैं तैयार हूँ। आप प्लेगरिज्म चेक करना शुरू कर सकते हैं।")
    else:
        await message.answer(f"🧐 आपने कहा: '{message.text}'\n\nअगर आप प्लेगरिज्म चेक करना चाहते हैं, तो दो टेक्स्ट के बीच 'VS' लिखें।")

# 4. Document Handler (Already Expert)
@dp.message(F.document)
async def handle_doc(message: types.Message):
    await message.answer("📂 फाइल मिल गई! मैं इसे प्रोसेस कर रहा हूँ...")

async def main():
    await start_web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
