import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import fitz  # PyMuPDF for PDF
import docx  # python-docx for Word

# Logging
logging.basicConfig(level=logging.INFO)

# Token from Environment Variable
API_TOKEN = os.getenv('BOT_TOKEN')
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- फाइल पढ़ने के फंक्शन्स ---
def read_pdf(file_path):
    text = ""
    with fitz.open(file_path) as doc:
        for page in doc:
            text += page.get_text()
    return text

def read_docx(file_path):
    doc = docx.Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])

def calculate_similarity(text1, text2):
    try:
        vectorizer = TfidfVectorizer()
        tfidf = vectorizer.fit_transform([text1, text2])
        return cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0] * 100
    except:
        return 0

# --- बॉट कमांड्स ---
# ग्लोबल वेरिएबल (जुगाड़: अभी के लिए यूजर का पहला टेक्स्ट यहाँ सेव होगा)
user_data = {}

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer(
        "📂 **Expert Document Checker**\n\n"
        "मैं PDF और Word फाइल चेक कर सकता हूँ!\n"
        "स्टेप 1: अपनी **पहली फाइल** (Original) भेजें।\n"
        "स्टेप 2: फिर **दूसरी फाइल** (To Check) भेजें।"
    )

@dp.message(F.document)
async def handle_document(message: types.Message):
    user_id = message.from_user.id
    file_id = message.document.file_id
    file_name = message.document.file_name

    # फाइल डाउनलोड करना
    file = await bot.get_file(file_id)
    file_path = f"{user_id}_{file_name}"
    await bot.download_file(file.file_path, file_path)

    # टेक्स्ट निकालना
    text = ""
    if file_name.endswith('.pdf'):
        text = read_pdf(file_path)
    elif file_name.endswith('.docx'):
        text = read_docx(file_path)
    else:
        await message.answer("❌ सिर्फ PDF या DOCX फाइल भेजें।")
        os.remove(file_path)
        return

    # फाइल डिलीट कर दें (सर्वर साफ़ रखने के लिए)
    os.remove(file_path)

    # लॉजिक: क्या यह पहली फाइल है या दूसरी?
    if user_id not in user_data:
        user_data[user_id] = text
        await message.answer("✅ **पहली फाइल सेव हो गई!**\nअब दूसरी फाइल भेजें जिससे तुलना करनी है।")
    else:
        text1 = user_data[user_id]
        text2 = text
        
        # रिजल्ट
        score = calculate_similarity(text1, text2)
        del user_data[user_id]  # डेटा साफ़ करें

        result = (
            f"🔍 **Comparison Result:**\n"
            f"📊 Similarity: `{score:.2f}%`\n"
            f"📝 Status: {'Copied 🚨' if score > 20 else 'Unique ✅'}"
        )
        await message.answer(result)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
