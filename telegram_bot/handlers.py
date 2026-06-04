from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from sqlalchemy import select

from telegram_bot.keyboards import (
MAIN_MENU_KEYBOARD,
DEMO_MENU_KEYBOARD,
)

from database import get_session

from models.user import User

router = Router()

@router.message(CommandStart())
async def start_handler(message: Message) -> None:

```
async with get_session() as session:

    result = await session.execute(
        select(User).where(
            User.telegram_id == message.from_user.id
        )
    )

    user = result.scalar_one_or_none()

    if user is None:

        user = User(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
        )

        session.add(user)

await message.answer(
    text=(
        "🤖 AI Trading Bot\n\n"
        "Добро пожаловать в систему анализа "
        "и демо-трейдинга."
    ),
    reply_markup=MAIN_MENU_KEYBOARD,
)
```

@router.message(lambda message: message.text == "📊 Анализ")
async def analysis_handler(message: Message) -> None:

```
await message.answer(
    "📊 Модуль анализа рынка находится в разработке."
)
```

@router.message(lambda message: message.text == "💹 Демо-Торговля")
async def demo_trading_handler(message: Message) -> None:

```
async with get_session() as session:

    result = await session.execute(
        select(User).where(
            User.telegram_id == message.from_user.id
        )
    )

    user = result.scalar_one_or_none()

    if user is None:

        await message.answer(
            "Пользователь не найден."
        )
        return

    await message.answer(
        (
            "💹 Демо-счет\n\n"
            f"💰 Баланс: {user.balance} USDT\n"
            f"👤 Пользователь: {user.first_name}\n\n"
            "Выберите действие:"
        ),
        reply_markup=DEMO_MENU_KEYBOARD,
    )
```

@router.message(lambda message: message.text == "📈 Купить BTC")
async def buy_btc_handler(message: Message) -> None:

```
await message.answer(
    "📈 Покупка BTC будет добавлена на следующем этапе."
)
```

@router.message(lambda message: message.text == "📉 Продать BTC")
async def sell_btc_handler(message: Message) -> None:

```
await message.answer(
    "📉 Продажа BTC будет добавлена на следующем этапе."
)
```

@router.message(lambda message: message.text == "📋 Мои сделки")
async def trades_handler(message: Message) -> None:

```
await message.answer(
    "📋 У вас пока нет сделок."
)
```

@router.message(lambda message: message.text == "⬅️ Главное меню")
async def back_to_main_menu(message: Message) -> None:

```
await message.answer(
    "Главное меню",
    reply_markup=MAIN_MENU_KEYBOARD,
)
```

@router.message(lambda message: message.text == "🧠 Самообучение")
async def self_learning_handler(message: Message) -> None:

```
await message.answer(
    "🧠 Модуль самообучения находится в разработке."
)
```

@router.message(lambda message: message.text == "⚙️ Настройки")
async def settings_handler(message: Message) -> None:

```
await message.answer(
    "⚙️ Модуль настроек находится в разработке."
)
```
