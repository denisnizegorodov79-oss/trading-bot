from __future__ import annotations

from aiogram.types import KeyboardButton
from aiogram.types import ReplyKeyboardMarkup

MAIN_MENU_KEYBOARD = ReplyKeyboardMarkup(
keyboard=[
[
KeyboardButton(text="📊 Анализ"),
KeyboardButton(text="💹 Демо-Торговля"),
],
[
KeyboardButton(text="🧠 Самообучение"),
KeyboardButton(text="⚙️ Настройки"),
],
],
resize_keyboard=True,
one_time_keyboard=False,
input_field_placeholder="Выберите раздел...",
)

DEMO_MENU_KEYBOARD = ReplyKeyboardMarkup(
keyboard=[
[
KeyboardButton(text="📈 Купить BTC"),
KeyboardButton(text="📉 Продать BTC"),
],
[
KeyboardButton(text="📋 Мои сделки"),
],
[
KeyboardButton(text="⬅️ Главное меню"),
],
],
resize_keyboard=True,
)
