import asyncio
import os
from html import escape

from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from aiogram.filters import Command

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL", "").rstrip("/")
WELCOME_DELETE_SECONDS = int(os.getenv("WELCOME_DELETE_SECONDS", "600"))
PORT = int(os.getenv("PORT", "8080"))

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
    if WEBAPP_URL:
        url = WEBAPP_URL if WEBAPP_URL.endswith("/rules") else f"{WEBAPP_URL}/rules"
        button = InlineKeyboardButton(text="📜 Правила чата", web_app=WebAppInfo(url=url))
    else:
        # запасной вариант, если WEBAPP_URL ещё не задан
        button = InlineKeyboardButton(text="📜 Правила чата", callback_data="rules:fallback")
    return InlineKeyboardMarkup(inline_keyboard=[[button]])


async def delete_later(chat_id: int, message_id: int, delay: int):
    await asyncio.sleep(delay)
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception as e:
        print(f"Could not delete welcome message: {e}", flush=True)


@dp.message(F.new_chat_members)
async def on_new_members(message: Message):
    # Удаляем системное уведомление о вступлении.
    try:
        await message.delete()
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
        sent = await bot.send_message(
            chat_id=message.chat.id,
            text=text,
            parse_mode="HTML",
            reply_markup=rules_keyboard(),
            disable_web_page_preview=True,
        )
        asyncio.create_task(delete_later(message.chat.id, sent.message_id, WELCOME_DELETE_SECONDS))


@dp.callback_query(F.data == "rules:fallback")
async def rules_fallback(call: CallbackQuery):
    await call.answer("Сейчас открою правила", show_alert=False)
    msg = await call.message.answer(RULES_TEXT)
    asyncio.create_task(delete_later(call.message.chat.id, msg.message_id, 120))


@dp.message(Command("rules"))
async def rules_command(message: Message):
    await message.answer(RULES_TEXT)


@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "🌙 Я Хранитель чудес. Добавьте меня администратором в чат, "
        "и я буду встречать новых участников и показывать правила."
    )


async def rules_page(request: web.Request):
    html_rules = "".join(f"<p>{escape(part)}</p>" for part in RULES_TEXT.split("\n\n"))
    html = f"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Правила чата</title>
  <script src="https://telegram.org/js/telegram-web-app.js"></script>
  <style>
    :root {{ color-scheme: dark; }}
    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      background: #11131a;
      color: #f6f1e8;
      line-height: 1.55;
    }}
    .wrap {{ max-width: 720px; margin: 0 auto; padding: 28px 22px 44px; }}
    .card {{
      background: linear-gradient(180deg, #1a1d27, #12141c);
      border: 1px solid rgba(255,255,255,.08);
      border-radius: 24px;
      padding: 24px;
      box-shadow: 0 18px 60px rgba(0,0,0,.35);
    }}
    h1 {{ font-size: 28px; margin: 0 0 18px; letter-spacing: -.02em; }}
    p {{ font-size: 17px; margin: 0 0 16px; }}
    .footer {{ opacity: .72; margin-top: 18px; font-size: 14px; }}
    .btn {{
      margin-top: 18px;
      width: 100%;
      border: 0;
      border-radius: 16px;
      padding: 15px 16px;
      font-size: 16px;
      font-weight: 700;
      background: #32d3c4;
      color: #071211;
      cursor: pointer;
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="card">
      <h1>🌙 Правила чата</h1>
      {html_rules}
      <div class="footer">Личный отдел чудес</div>
      <button class="btn" onclick="closeApp()">Понятно, закрыть</button>
    </div>
  </div>
  <script>
    const tg = window.Telegram && window.Telegram.WebApp;
    if (tg) {{ tg.ready(); tg.expand(); }}
    function closeApp() {{ if (tg) tg.close(); }}
  </script>
</body>
</html>"""
    return web.Response(text=html, content_type="text/html")


async def health(request: web.Request):
    return web.Response(text="ok")


async def start_web_server():
    app = web.Application()
    app.router.add_get("/", health)
    app.router.add_get("/rules", rules_page)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    print(f"Web server started on port {PORT}", flush=True)


async def main():
    print("Starting Хранитель чудес", flush=True)
    await start_web_server()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
