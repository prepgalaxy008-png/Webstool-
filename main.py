import os
import asyncio
import logging
import re
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from googlesearch import search
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from aiohttp import web
import fitz
import docx

# 1. Configuration
logging.basicConfig(level=logging.INFO)
API_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = 7020885934  # आपकी ID सेट है

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

stats = {"total_users": set(), "checks_done": 0}
user_memory = {}

# --- 2. Render Health Server ---
async def health_check(request):
    return web.Response(text="Plagiarism Bot is Live & Accurate!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

# --- 3. Expert Functions (Cleaning & Searching) ---
def clean_text(text):
    # Wikipedia के [1], [22] जैसे नंबर्स हटाता है ताकि सर्च सटीक हो
    return re.sub(r'\[\d+\]', '', text).strip()

def calc_sim(t1, t2):
    try:
        v = TfidfVectorizer()
        return cosine_similarity(v.fit_transform([t1, t2]))[0][1] * 100
    except: return 0

# --- 4. Bot Handlers ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    stats["total_users"].add(message.from_user.id)
    await message.answer("🚀 **Expert Bot Active!**\n\nटेक्स्ट भेजें (Wikipedia से भी) या फाइलें।")

@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        report = (
            "📊 **Admin Dashboard**\n\n"
            f"👤 Users: `{len(stats['total_users'])}` \n"
            f"🔍 Checks: `{stats['checks_done']}`"
        )
        await message.answer(report)
    else:
        await message.answer(f"❌ आप एडमिन नहीं हैं। ID: `{message.from_user.id}`")

@dp.message(F.text)
async def handle_text(msg: types.Message):
    stats["checks_done"] += 1
    stats["total_users"].add(msg.from_user.id)
    
    text = clean_text(msg.text) # क्लीनिंग चालू

    if "vs" in text.lower():
        parts = text.lower().split("vs")
        if len(parts) == 2:
            score = calc_sim(parts[0], parts[1])
            await msg.reply(f"📊 Similarity: `{score:.2f}%`")
        return

    m = await msg.answer("🌐 इंटरनेट पर गहराई से खोजा जा रहा है...")
    
    # सबसे सटीक लाइन ढूँढना सर्च के लिए
    lines = [l for l in text.split('.') if len(l) > 20]
    search_query = max(lines, key=len).strip() if lines else text[:80]

    links = []
    try:
        # Exact Match के लिए कोट्स का इस्तेमाल
        for url in search(f'"{search_query[:80]}"', num_results=3):
            links.append(url)
    except: pass

    if links:
        report = "🚨 **Plagiarism Detected!**\n\nयहाँ मैच मिला है:\n" + "\n".join(links)
        await m.edit_text(report, disable_web_page_preview=True)
    else:
        await m.edit_text("✅ यह कंटेंट इंटरनेट पर ओरिजिनल लग रहा है!")

# --- 5. Main ---
async def main():
    await start_web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
