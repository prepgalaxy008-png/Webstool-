import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from googlesearch import search
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from aiohttp import web
import fitz  # PyMuPDF
import docx

# 1. Logging & Configuration
logging.basicConfig(level=logging.INFO)
API_TOKEN = os.getenv('BOT_TOKEN')
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- 2. Render Health Check Server (24/7 रखने के लिए) ---
async def health_check(request):
    return web.Response(text="Plagiarism Bot is High-Performing & Live!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

# --- 3. Expert Functions (File Reading & Similarity) ---
def get_text_from_file(path, name):
    try:
        if name.endswith('.pdf'):
            t = ""
            with fitz.open(path) as d:
                for p in d: t += p.get_text()
            return t
        elif name.endswith('.docx'):
            return "\n".join([p.text for p in docx.Document(path).paragraphs])
    except Exception as e:
        logging.error(f"Error reading file: {e}")
    return None

def calc_sim(t1, t2):
    try:
        v = TfidfVectorizer()
        return cosine_similarity(v.fit_transform([t1, t2]))[0][1] * 100
    except: return 0

# --- 4. Bot Handlers ---
user_memory = {}

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "🚀 **Advanced Plagiarism Bot Active!**\n\n"
        "1. **Web Search:** बस कोई भी टेक्स्ट भेजें।\n"
        "2. **Comparison:** 'Text1 VS Text2' लिखें।\n"
        "3. **Files:** दो PDF या Word फाइलें भेजें।"
    )

# File Comparison Logic
@dp.message(F.document)
async def handle_docs(msg: types.Message):
    uid = msg.from_user.id
    ext = msg.document.file_name.lower()
    
    if not (ext.endswith('.pdf') or ext.endswith('.docx')):
        await msg.reply("❌ सिर्फ PDF या DOCX भेजें।")
        return

    m = await msg.answer("⏳ फाइल प्रोसेस हो रही है...")
    file = await bot.get_file(msg.document.file_id)
    path = f"tmp_{uid}_{msg.document.file_name}"
    await bot.download_file(file.file_path, path)
    
    content = get_text_from_file(path, ext)
    os.remove(path)

    if uid not in user_memory:
        user_memory[uid] = content
        await m.edit_text("✅ **पहली फाइल मिल गई!** अब तुलना के लिए दूसरी फाइल भेजें।")
    else:
        score = calc_sim(user_memory[uid], content)
        del user_memory[uid]
        await m.edit_text(f"📊 **Similarity Result:** `{score:.2f}%`")

# Web Search & Text Logic
@dp.message(F.text)
async def handle_text(msg: types.Message):
    if "vs" in msg.text.lower():
        parts = msg.text.lower().split("vs")
        if len(parts) == 2:
            score = calc_sim(parts[0], parts[1])
            await msg.reply(f"📊 **Manual Comparison:** `{score:.2f}%` similarity.")
        return

    # Internet Search Feature
    m = await msg.answer("🌐 इंटरनेट पर खोजा जा रहा है...")
    links = []
    try:
        for url in search(msg.text[:100], num_results=3):
            links.append(url)
    except: pass

    if links:
        report = "🚨 **Potential Match Found on Web:**\n\n" + "\n".join([f"🔗 {l}" for l in links])
        await m.edit_text(report, disable_web_page_preview=True)
    else:
        await m.edit_text("✅ यह कंटेंट इंटरनेट पर ओरिजिनल लग रहा है!")

# --- 5. Main Execution ---
async def main():
    await start_web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
