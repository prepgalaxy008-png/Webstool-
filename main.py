import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# 1. Logging setup
logging.basicConfig(level=logging.INFO)

# 2. Token environment variable से लेना
API_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# 3. Plagiarism Checking Logic
def get_similarity_report(text1, text2):
    try:
        documents = [text1, text2]
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(documents)

        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
        score = similarity[0][0] * 100
        return score
    except Exception:
        return 0

# 4. Bot Commands
@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    await message.answer(
        "🔥 **Expert Plagiarism Checker Bot** 🔥\n\n"
        "दो टेक्स्ट के बीच समानता चेक करने के लिए उन्हें इस तरह भेजें:\n"
        "`Text A` VS `Text B`\n\n"
        "नोट: दोनों के बीच 'VS' लिखना ज़रूरी है।"
    )

@dp.message(F.text.contains("VS"))
async def process_check(message: types.Message):
    texts = message.text.split("VS")
    if len(texts) < 2:
        await message.reply("कृपया सही फॉर्मेट का उपयोग करें: Text1 VS Text2")
        return

    wait_msg = await message.answer("🔍 एनेलाइजिंग... कृपया प्रतीक्षा करें।")

    score = get_similarity_report(texts[0].strip(), texts[1].strip())

    status = "🚨 **Plagiarism Detected!**" if score > 25 else "✅ **Content is Unique!**"
    response = (
        f"{status}\n\n"
        f"📊 **Similarity Score:** `{score:.2f}%`\n"
        f"✍️ **Verdict:** " + ("कॉपी किया गया है।" if score > 25 else "ओरिजिनल कंटेंट है।")
    )

    await wait_msg.edit_text(response, parse_mode="Markdown")

# 5. Start Bot
async def main():
    print("Bot is Running...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
