import os
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from openai import OpenAI
from dotenv import load_dotenv

# Загружаем переменные из окружения (.env)
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")

# Проверяем токен
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден. Добавь его в Render → Environment Variables.")
if not OPENAI_API_KEY:
    raise ValueError("❌ OPENAI_API_KEY не найден. Добавь его в Render → Environment Variables.")

# Логирование
logging.basicConfig(level=logging.INFO)

# Инициализация клиентов
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
client = OpenAI(api_key=OPENAI_API_KEY)


# --- Основной обработчик сообщений ---
@dp.message()
async def handle_message(message: types.Message):
    user_text = message.text
    logging.info(f"📩 Получено сообщение: {user_text}")

    try:
        # Запрос к OpenAI
        completion = client.chat.completions.create(
            model="gpt-5.2-chat-latest",
            messages=[
                {"role": "system", "content": "Ты — корпоративный ассистент компании Buildeco."},
                {"role": "user", "content": user_text},
            ],
        )

        # Безопасное получение контента
        reply = None
        if completion and completion.choices:
            message_obj = completion.choices[0].message
            if isinstance(message_obj, dict):
                reply = message_obj.get("content")
            else:
                # новый SDK возвращает объект, а не dict
                reply = getattr(message_obj, "content", None)

        # Проверяем ответ
        if reply and reply.strip():
            await message.answer(reply)
        else:
            logging.error("⚠️ OpenAI вернул пустой ответ или неизвестный формат.")
            await message.answer("🤖 Извини, я не получил содержательного ответа от модели.")

    except Exception as e:
        logging.error(f"❌ Ошибка OpenAI: {e}")
        await message.answer("⚠️ Произошла ошибка при обращении к OpenAI API.")


# --- Настройка Webhook ---
async def on_startup(app):
    webhook_url = f"{RENDER_EXTERNAL_URL}/webhook"
    await bot.set_webhook(webhook_url)
    logging.info(f"✅ Webhook установлен: {webhook_url}")


async def on_shutdown(app):
    await bot.delete_webhook()
    logging.info("🧹 Webhook удалён.")


def main():
    app = web.Application()

    # Регистрируем webhook
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path="/webhook")
    setup_application(app, dp, bot=bot)

    # Подписываемся на события
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    port = int(os.getenv("PORT", 10000))
    web.run_app(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
