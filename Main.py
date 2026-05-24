import telebot
import google.generativeai as genai
import json
import time
from flask import Flask
from threading import Thread

# 1. Render uchun kichik Veb-server (Health Check'dan o'tish uchun)
app = Flask('')

@app.route('/')
def home():
    return "Bot tirik va ishlamoqda!"

def run_server():
    # Render avtomatik ravishda 10000-portni beradi
    app.run(host='0.0.0.0', port=10000)

# 2. Kalitlar va Bot sozlamalari
BOT_TOKEN = "8735068391:AAH8L_LSu0-9fFOWaiLSfq5kqqKyX-XHq6M"
API_KEY = "AIzaSyDTZ8Wha5VLt-kC88jWeEZnkjEZgCBLufE"

bot = telebot.TeleBot(BOT_TOKEN)
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-pro')

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "👋 Assalomu alaykum! Interaktiv Quiz Generator botga xush kelibsiz.\n\n"
        "📝 Menga test savollari bor `.txt.pdf.docx` fayl yuboring.\n"
        "Men ularni Telegramning haqiqiy, bosiladigan **Quiz (Test)** formatiga oʻtkazib beraman!"
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(content_types=['document'])
def handle_docs(message):
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        user_text = downloaded_file.decode('utf-8')
        
        bot.reply_to(message, "⏳ Fayl tahlil qilinmoqda va haqiqiy Telegram testlariga aylantirilmoqda, iltimos kuting...")
        
        prompt = (
            f"Quyidagi matn ichidagi test savollarini tahlil qil va ularni faqat va faqat "
            f"mana shu JSON formatida qaytar, boshqa hech qanday matn yozma:\n"
            f"[\n"
            f"  {{\n"
            f"    \"question\": \"Savol matni (maksimal 300 ta belgi)\",\n"
            f"    \"options\": [\"A variant\", \"B variant\", \"C variant\", \"D variant\"],\n"
            f"    \"correct_option_id\": 0,\n"
            f"    \"explanation\": \"Qisqa tushuntirish (maksimal 200 belgi)\"\n"
            f"  }}\n"
            f"]\n"
            f"Matn:\n{user_text}"
        )
        
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        quizzes = json.loads(response_text.strip())
        
        for quiz in quizzes:
            bot.send_poll(
                chat_id=message.chat.id,
                question=quiz['question'][:300],
                options=[opt[:100] for opt in quiz['options']],
                type='quiz',
                correct_option_id=int(quiz['correct_option_id']),
                explanation=quiz['explanation'][:200],
                is_anonymous=False
            )
            time.sleep(1)
            
    except Exception as e:
        bot.reply_to(message, f"❌ Xatolik yuz berdi: {str(e)}\nFayl matni test formatida ekanligini tekshiring.")

# Serverni alohida oqimda (Thread) ishga tushirish
server_thread = Thread(target=run_server)
server_thread.start()

# Botni uzluksiz yoqish
bot.infinity_polling()
