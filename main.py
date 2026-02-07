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

# 1. Setup
logging.basicConfig(level=logging.INFO)
API_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = 7020885934 # आपकी ID सेट है

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
stats = {"total_users": set(), "checks_done": 0}

# --- 2. Advanced Cleaner (Wikipedia Fix) ---
def ultra_clean(text):
    # 1. Wikipedia के [1], [26][27] जैसे नंबर्स को हटाता है
    text = re.sub(r'\[\d+\]', '', text)
    # 2. स्पेशल कैरेक्टर्स और एक्स्ट्रा स्पेस हटाता है
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# --- 3. Render Server ---
async def start_web_server():
    app = web.Application()
    app.router.add_get('/', lambda r: web.Response(text="Bot is Live!"))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 8080)))
    await site.start()

# --- 4. Logic & Handlers ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    stats["total_users"].add(message.from_user.id)
    await message.answer("✅ **Advanced Bot Active!**\nWikipedia टेक्स्ट भेजकर टेस्ट करें।")

@dp.message(F.text)
async def handle_text(msg: types.Message):
    if msg.text.startswith('/'): return
    
    stats["checks_done"] += 1
    stats["total_users"].add(msg.from_user.id)
    
    # टेक्स्ट को पूरी तरह साफ़ करना
    cleaned_text = ultra_clean(msg.text)
    
    m = await msg.answer("🌐 इंटरनेट पर सटीक खोज जारी है...")
    
    # सबसे महत्वपूर्ण वाक्य (Sentence) चुनना
    sentences = [s for s in cleaned_text.split('.') if len(s) > 30]
    query = sentences[0] if sentences else cleaned_text[:80]

    links = []
    try:
        # Exact Match के लिए डबल कोट्स का उपयोग
        for url in search(f'"{query[:100]}"', num_results=3):
            links.append(url)
    except Exception as e:
        logging.error(f"Search Error: {e}")

    if links:
        report = "🚨 **Plagiarism Detected!**\n\nयहाँ मैच मिला है:\n" + "\n".join([f"🔗 {l}" for l in links])
        await m.edit_text(report, disable_web_page_preview=True)
    else:
        # अगर कोट्स के साथ मैच न मिले तो सामान्य सर्च
        try:
            for url in search(query[:100], num_results=2):
                links.append(url)
        except: pass
        
        if links:
            await m.edit_text("🚨 **Potential Match Found:**\n" + "\n".join(links), disable_web_page_preview=True)
        else:
            await m.edit_text("✅ यह कंटेंट इंटरनेट पर ओरिजिनल लग रहा है!")

async def main():
    await start_web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
