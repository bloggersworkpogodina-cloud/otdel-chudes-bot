import asyncio
import os
from html import escape

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
WELCOME_DELETE_SECONDS = int(os.getenv("WELCOME_DELETE_SECONDS", "600"))
RULES_DELETE_SECONDS = int(os.getenv("RULES_DELETE_SECONDS", "180"))

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

RULES_TEXT = """
🌙 ПРАВИЛА ЧАТА

Материться можно. Материть друг друга — нельзя.

Никакой политики. Совсем. Нарушение — сразу бан.

Реклама и спам разрешены только во флудилке.

Хотите разместить рекламу для участников сообщества — присылайте её администратору. После согласования она будет опубликована от имени администратора в отдельной папке.

Уважаем друг друга и не превращаем обсуждения в срач.

На этом всё. Общайтесь, знакомьтесь и чувствуйте себя свободно 🌙
""".strip()


def mention_user(user) -> str:
    name = escape(user.full_name or "новый участник")
    return f'<a href="tg://user?id={user.id}">{name}</a>'


def rules_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="📜 Правила чата", callback_data="show_rules")
        ]]
    )


async def delete_later(chat_id: int, message_id: int, delay: int, label: str):
    await asyncio.sleep(delay)
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
        print(f"Deleted {label}: {message_id}", flush=True)
    except Exception as e:
        print(f"Could not delete {label}: {e}", flush=True)


@dp.message(F.new_chat_members)
async def on_new_members(message: Message):
    print(f"New chat members event in chat {message.chat.id}", flush=True)

    try:
        await message.delete()
        print("Service join message deleted", flush=True)
    except Exception as e:
        print(f"Could not delete service message: {e}", flush=True)

    for user in message.new_chat_members:
        if user.is_bot:
            continue

        text = (
            f"🌙 Добро пожаловать в «Личный отдел чудес», {mention_user(user)}!\n\n"
            "Рады видеть тебя в нашем пространстве.\n\n"
            "Перед тем как вливаться в общение, ознакомься с правилами чата 👇\n\n"
            "И немного расскажи о себе в любой удобной форме — кто ты, чем занимаешься, "
            "что тебя привело сюда или просто то, чем хочется поделиться ✨"
        )

        try:
            sent = await bot.send_message(
                chat_id=message.chat.id,
                text=text,
                parse_mode="HTML",
                reply_markup=rules_keyboard(),
                disable_web_page_preview=True,
            )
            print(f"Welcome message sent: {sent.message_id}", flush=True)
            asyncio.create_task(delete_later(message.chat.id, sent.message_id, WELCOME_DELETE_SECONDS, "welcome message"))
        except Exception as e:
            print(f"Could not send welcome message: {e}", flush=True)


@dp.callback_query(F.data == "show_rules")
async def show_rules(call: CallbackQuery):
    try:
        await call.answer("Правила отправлены ниже", show_alert=False)
    except Exception:
        pass

    try:
        msg = await call.message.answer(RULES_TEXT)
        print(f"Rules message sent: {msg.message_id}", flush=True)
        asyncio.create_task(delete_later(call.message.chat.id, msg.message_id, RULES_DELETE_SECONDS, "rules message"))
    except Exception as e:
        print(f"Could not send rules message: {e}", flush=True)


@dp.message(Command("rules"))
async def rules_command(message: Message):
    msg = await message.answer(RULES_TEXT)
    asyncio.create_task(delete_later(message.chat.id, msg.message_id, RULES_DELETE_SECONDS, "rules message"))


@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "🌙 Я Хранитель чудес. Добавьте меня администратором в чат, "
        "и я буду встречать новых участников и показывать правила."
    )


async def main():
    print("Starting Хранитель чудес clean stable 3-files version", flush=True)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
