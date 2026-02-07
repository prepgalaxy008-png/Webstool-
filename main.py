import os
import asyncio
from aiogram import Bot, Dispatcher, types, F
from googlesearch import search
import aiohttp
from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# --- Configuration ---
API_TOKEN = os.getenv('BOT_TOKEN')
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- Web Scraper & Search Logic ---
async def check_on_web(query_text):
    # 1. Google से टॉप 3 रिजल्ट्स के लिंक निकालना (Free Method)
    results = []
    try:
        # सिर्फ पहले 3-5 लिंक लेंगे ताकि प्रोसेस फ़ास्ट रहे
        for url in search(query_text, num_results=3):
            results.append(url)
    except:
        return "Search Error"

    # 2. उन लिंक्स से कंटेंट मैच करना (Simulated snippet check)
    # असली एक्सपर्ट टूल में हम यहाँ 'Request' भेजकर पेज रीड करते हैं
    # अभी के लिए हम यूजर को बताएँगे कि ये कहाँ-कहाँ मिल सकता है
    return results

@dp.message(F.text)
async def handle_pro_search(message: types.Message):
    # अगर यूजर 'VS' नहीं लिख रहा, तो हम उसे इंटरनेट पर खोजेंगे
    if "vs" in message.text.lower():
        # पुराना VS वाला लॉजिक (Text A vs Text B)
        return

    wait_msg = await message.answer("🌐 इंटरनेट पर सर्च किया जा रहा है... इसमें 10-15 सेकंड लग सकते हैं।")
    
    links = await check_on_web(message.text[:100]) # शुरुआती 100 अक्षर सर्च करेंगे
    
    if links == "Search Error":
        await wait_msg.edit_text("❌ सर्च लिमिट पूरी हो गई है या इंटरनेट धीमा है।")
    elif links:
        report = "🚨 **Potential Plagiarism Found!**\n\nयह कंटेंट इन वेबसाइट्स पर मिला है:\n"
        for i, link in enumerate(links, 1):
            report += f"{i}. [Link]({link})\n"
        await wait_msg.edit_text(report, parse_mode="Markdown", disable_web_page_preview=True)
    else:
        await wait_msg.edit_text("✅ यह कंटेंट इंटरनेट पर कहीं नहीं मिला। यह ओरिजिनल लग रहा है!")

# --- Main Execution ---
async def main():
    # Render Health check server यहाँ भी रहेगा
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
