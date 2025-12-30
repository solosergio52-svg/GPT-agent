import os
import logging
import openai
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode
from aiogram.utils.keyboard import ReplyKeyboardBuilder

# 🔧 Настройка логов
logging.basicConfig(level=logging.INFO)

# 🔑 Переменные окружения
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WORKFLOW_ID = os.getenv("WORKFLOW_ID")
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ⚙️ Инициализация
bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

openai.api_key = OPENAI_API_KEY

# 🟢 /start
@dp.message(CommandStart())
async def start_handler(message: types.Message):
    await message.answer(
        "👋 Привет! Я корпоративный помощник Buildeco. "
        "Задай мне вопрос — и я помогу разобраться с внутренними процессами, проектами или документами."
    )

# 💬 Обработка обычных сообщений
@dp.message()
async def handle_message(message: types.Message):
    user_text = message.text
    user_id = message.from_user.id
    logging.info(f"📩 Сообщение от {user_id}: {user_text}")

    try:
        # 🔗 Отправляем запрос в Workflow
        response = openai.Chat.completions.create(
            model="gpt-5.2-chat-latest",
            messages=[
                {"role": "system", "content": "You are Buildeco corporate assistant."},
                {"role": "user", "content": user_text}
            ],
            extra_body={"workflow_id": WORKFLOW_ID}
        )

        reply = response.choices[0].message.content
        await message.answer(reply)

    except Exception as e:
        logging.error(f"Ошибка при обращении к OpenAI: {e}")
        await message.answer("⚠️ Ошибка при обращении к OpenAI API. Попробуй позже.")

# 🚀 Запуск
from aiohttp import web

async def handle(request):
    return web.Response(text="Bot is running!")

async def on_startup(app):
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_webhook(f"{os.getenv('RENDER_EXTERNAL_URL')}/webhook")

app = web.Application()
app.router.add_get("/", handle)
app.router.add_post("/webhook", dp.webhook_handler)
app.on_startup.append(on_startup)

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=int(os.getenv("PORT", 10000)))

