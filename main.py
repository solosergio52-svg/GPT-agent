import os
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from openai import OpenAI
from dotenv import load_dotenv

# Загружаем переменные из окружения
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")

# Проверяем, есть ли токен
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found. Add it in Render Environment variables.")

logging.basicConfig(level=logging.INFO)

# Настраиваем Telegram и OpenAI
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
client = OpenAI(api_key=OPENAI_API_KEY)


# Основной обработчик сообщений
@dp.message()
async def handle_message(message: types.Message):
    user_text = message.text
    logging.info(f"Received message: {user_text}")

    try:
        # Отправляем запрос в OpenAI
        completion = client.chat.completions.create(
            model="gpt-5.2-chat-latest",
            messages=[
                {"role": "system", "content": "Ты — корпоративный ассистент компании Buildeco."},
                {"role": "user", "content": user_text},
            ],
            max_completion_tokens=400,
        )

        reply = completion.choices[0].message.content
        await message.answer(reply)

    except Exception as e:
        logging.error(f"OpenAI error: {e}")
        await message.answer("⚠️ Произошла ошибка при обращении к OpenAI API.")


# --- WEBHOOK CONFIG ---
async def on_startup(app):
    webhook_url = f"{RENDER_EXTERNAL_URL}/webhook"
    await bot.set_webhook(webhook_url)
    logging.info(f"Webhook set to {webhook_url}")


async def on_shutdown(app):
    await bot.delete_webhook()
    logging.info("Webhook deleted.")


def main():
    app = web.Application()

    # Регистрируем webhook
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path="/webhook")

    # Настраиваем запуск
    setup_application(app, dp, bot=bot)

    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    port = int(os.getenv("PORT", 10000))
    web.run_app(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
