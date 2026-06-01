import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from config import config

logging.basicConfig(level=logging.INFO)

bot = Bot(token=config.TELEGRAM_TOKEN)
dp = Dispatcher()

def main_keyboard():
    buttons = [
        [KeyboardButton(text="📊 Анализ")],
        [KeyboardButton(text="🚀 Демо-Торговля")],
        [KeyboardButton(text="🧠 Самообучение")],
        [KeyboardButton(text="⚙️ Настройки")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer(
        "🤖 *ИИ-Трейдинг Бот*\n\n"
        "▪️ Анализ рынка через DeepSeek-R1\n"
        "▪️ Демо-торговля с балансом $500\n"
        "▪️ Самообучение на ошибках\n\n"
        "📌 *Выберите действие в меню ниже*",
        parse_mode="Markdown",
        reply_markup=main_keyboard()
    )

@dp.message(lambda msg: msg.text == "📊 Анализ")
async def analysis(message: types.Message):
    await message.answer("📊 *Анализ рынка*\n\nЗагрузка данных...", parse_mode="Markdown")

@dp.message(lambda msg: msg.text == "🚀 Демо-Торговля")
async def demo_trading(message: types.Message):
    await message.answer("🚀 *Демо-Торговля*\n\nБаланс: $500\nСделок: 0", parse_mode="Markdown")

@dp.message(lambda msg: msg.text == "🧠 Самообучение")
async def learning(message: types.Message):
    await message.answer("🧠 *Самообучение*\n\nОшибок в базе: 0", parse_mode="Markdown")

@dp.message(lambda msg: msg.text == "⚙️ Настройки")
async def settings(message: types.Message):
    await message.answer("⚙️ *Настройки*\n\nРиск на сделку: 1%\nМакс сделок в день: 10", parse_mode="Markdown")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
