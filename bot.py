import telebot
from telebot.types import ReplyKeyboardMarkup
import yfinance as yf
import time
import threading

TOKEN = "8948879603:AAHGLkpJQ2kGPshJ8VxuHcLidZGLKEsSo2w"
bot = telebot.TeleBot(TOKEN)

def main_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add("📊 СИГНАЛ", "🤖 АВТО-ТРЕЙДИНГ")
    kb.add("💰 БАЛАНС", "📈 СТАТИСТИКА")
    kb.add("❌ ЗАКРЫТЬ ВСЕ", "⚙️ НАСТРОЙКИ")
    return kb

@bot.message_handler(commands=['start'])
def start(msg):
    bot.send_message(msg.chat.id, "🤖 Бот запущен! Нажми кнопку.", reply_markup=main_keyboard())

@bot.message_handler(func=lambda m: m.text == "📊 СИГНАЛ")
def signal(msg):
    try:
        ticker = yf.Ticker("BTC-USD")
        data = ticker.history(period="2d")
        last = data['Close'].iloc[-1]
        prev = data['Close'].iloc[-2]
        if last > prev:
            text = f"🟢 LONG (покупка)\n💰 Цена: ${last:.2f}"
        else:
            text = f"🔴 SHORT (продажа)\n💰 Цена: ${last:.2f}"
    except Exception as e:
        text = f"Ошибка: {e}"
    bot.reply_to(msg, text)

@bot.message_handler(func=lambda m: m.text == "🤖 АВТО-ТРЕЙДИНГ")
def auto(msg):
    bot.reply_to(msg, "🤖 Авто-трейдинг включён")

@bot.message_handler(func=lambda m: m.text == "💰 БАЛАНС")
def balance(msg):
    bot.reply_to(msg, "💰 Баланс: $500")

@bot.message_handler(func=lambda m: m.text == "📈 СТАТИСТИКА")
def stats(msg):
    bot.reply_to(msg, "📈 Сделок: 0 | Win Rate: 0%")

@bot.message_handler(func=lambda m: m.text == "❌ ЗАКРЫТЬ ВСЕ")
def close_all(msg):
    bot.reply_to(msg, "✅ Все сделки закрыты")

@bot.message_handler(func=lambda m: m.text == "⚙️ НАСТРОЙКИ")
def settings(msg):
    bot.reply_to(msg, "⚙️ Настройки: /set")

def run():
    print("✅ Бот запущен!")
    bot.infinity_polling()

thread = threading.Thread(target=run, daemon=True)
thread.start()

while True:
    time.sleep(1)
