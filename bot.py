import asyncio
import logging
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DELETE_WELCOME_AFTER_SECONDS = int(os.getenv("DELETE_WELCOME_AFTER_SECONDS", "600"))

if not BOT_TOKEN:
    raise RuntimeError("Не найден BOT_TOKEN. Создай файл .env и вставь туда токен бота.")

router = Router()

WELCOME_TEXT = """🌙 Добро пожаловать в «Личный отдел чудес», {name}!

Рады видеть тебя в нашем пространстве.

Здесь можно общаться, задавать вопросы, делиться мыслями, знакомиться и быть собой.

Перед тем как вливаться в общение, ознакомься с правилами чата 👇

И немного расскажи о себе в любой удобной форме — кто ты, чем занимаешься, что тебя привело сюда или просто то, чем хочется поделиться ✨"""

RULES_TEXT = """🌙 ПРАВИЛА ЧАТА

Материться можно. Материть друг друга — нельзя.

Никакой политики. Совсем. Нарушение — сразу бан.

Реклама и спам разрешены только во флудилке.

Хотите разместить рекламу для участников сообщества — присылайте её администратору. После согласования она будет опубликована от имени администратора в отдельной папке.

Уважаем друг друга и не превращаем обсуждения в срач.

На этом всё. Общайтесь, знакомьтесь и чувствуйте себя свободно 🌙"""

rules_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="📜 Правила чата", callback_data="show_rules")]
    ]
)


async def delete_later(bot: Bot, chat_id: int, message_id: int, delay: int) -> None:
    await asyncio.sleep(delay)
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except (TelegramBadRequest, TelegramForbiddenError):
        pass


@router.message(CommandStart())
async def start_command(message: Message) -> None:
    await message.answer(
        "Привет 🌙 Я Хранитель чудес. Добавь меня администратором в чат, чтобы я встречал новых участников и удалял системные уведомления."
    )


@router.message(F.new_chat_members)
async def welcome_new_members(message: Message, bot: Bot) -> None:
    # Удаляем системное уведомление о вступлении в чат
    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    except (TelegramBadRequest, TelegramForbiddenError):
        pass

    for member in message.new_chat_members:
        if member.is_bot:
            continue

        name = member.first_name or "новый участник"
        welcome = await bot.send_message(
            chat_id=message.chat.id,
            text=WELCOME_TEXT.format(name=name),
            reply_markup=rules_keyboard,
        )

        asyncio.create_task(
            delete_later(
                bot=bot,
                chat_id=message.chat.id,
                message_id=welcome.message_id,
                delay=DELETE_WELCOME_AFTER_SECONDS,
            )
        )


@router.callback_query(F.data == "show_rules")
async def show_rules(callback: CallbackQuery) -> None:
    await callback.answer(RULES_TEXT, show_alert=True)


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
