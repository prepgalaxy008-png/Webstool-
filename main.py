import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from aiohttp import web
import fitz  # PyMuPDF
import docx

logging.basicConfig(level=logging.INFO)

API_TOKEN = os.getenv('BOT_TOKEN')
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- Render Health Check ---
async def health_check(request):
    return web.Response(text="Plagiarism Bot is running 24/7!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

# --- Logic ---
user_memory = {}

def extract_text_from_file(file_path, file_name):
    if file_name.endswith('.pdf'):
        text = ""
        with fitz.open(file_path) as doc:
            for page in doc: text += page.get_text()
        return text
    elif file_name.endswith('.docx'):
        doc = docx.Document(file_path)
        return "\n".join([p.text for p in doc.paragraphs])
    return None

@dp.message(F.document)
async def handle_docs(message: types.Message):
    user_id = message.from_user.id
    doc = message.document
    
    # 1. Download
    file = await bot.get_file(doc.file_id)
    dest = f"file_{user_id}_{doc.file_name}"
    await bot.download_file(file.file_path, dest)
    
    # 2. Read
    text = extract_text_from_file(dest, doc.file_name.lower())
    os.remove(dest) # सफाई

    if not text:
        await message.answer("❌ सिर्फ PDF या Word फाइल भेजें।")
        return

    # 3. Compare
    if user_id not in user_memory:
        user_memory[user_id] = text
        await message.answer("✅ **पहली फाइल मिल गई!** अब तुलना के लिए दूसरी फाइल भेजें।")
    else:
        score = 0
        try:
            vectorizer = TfidfVectorizer()
            tfidf = vectorizer.fit_transform([user_memory[user_id], text])
            score = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0] * 100
        except: pass
        
        del user_memory[user_id]
        await message.answer(f"📊 **Similarity Result:** `{score:.2f}%`")

@dp.message(F.text.contains("VS"))
async def check_text(message: types.Message):
    parts = message.text.split("VS")
    if len(parts) == 2:
        v = TfidfVectorizer()
        sim = cosine_similarity(v.fit_transform([parts[0], parts[1]]))[0][1] * 100
        await message.answer(f"📊 **Text Similarity:** `{sim:.2f}%`")

async def main():
    await start_web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
