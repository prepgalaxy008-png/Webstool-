import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from googlesearch import search
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from aiohttp import web
import fitz
import docx

# 1. Configuration & Security
logging.basicConfig(level=logging.INFO)
API_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = 7020885934  # <--- यहाँ अपनी असली Telegram ID डालें (बिना कोट्स के)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Memory for tracking (Database replacement for now)
stats = {"total_users": set(), "checks_done": 0}
user_memory = {}

# --- 2. Health Check Server ---
async def health_check(request):
    return web.Response(text="Admin & Plagiarism Bot is Live!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

# --- 3. Professional Admin Command ---
@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        report = (
            "📊 **Admin Dashboard**\n\n"
            f"👤 Total Unique Users: `{len(stats['total_users'])}` \n"
            f"🔍 Total Checks Done: `{stats['checks_done']}` \n"
            "📡 Server Status: `Active 🟢`"
        )
        await message.answer(report, parse_mode="Markdown")
    else:
        await message.answer("❌ आप इस बॉट के एडमिन नहीं हैं।")

# --- 4. Logic Functions ---
def calc_sim(t1, t2):
    try:
        v = TfidfVectorizer()
        return cosine_similarity(v.fit_transform([t1, t2]))[0][1] * 100
    except: return 0

# --- 5. Handlers ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    stats["total_users"].add(message.from_user.id)
    await message.answer("🚀 **Expert Plagiarism Bot Active!**\n\nटेक्स्ट भेजें या दो फाइलें!")

@dp.message(F.text)
async def handle_text(msg: types.Message):
    stats["checks_done"] += 1
    # VS Comparison Logic
    if "vs" in msg.text.lower():
        parts = msg.text.lower().split("vs")
        if len(parts) == 2:
            score = calc_sim(parts[0], parts[1])
            await msg.reply(f"📊 Similarity: `{score:.2f}%`")
        return

    # Web Search Logic
    m = await msg.answer("🌐 इंटरनेट सर्च चालू है...")
    links = []
    try:
        for url in search(msg.text[:100], num_results=3):
            links.append(url)
    except: pass

    if links:
        await m.edit_text("🚨 **Matches Found:**\n" + "\n".join(links), disable_web_page_preview=True)
    else:
        await m.edit_text("✅ ओरिजिनल कंटेंट है!")

# --- 6. Final Execution ---
async def main():
    await start_web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
