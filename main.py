import os
import openai
from aiogram import Bot, Dispatcher, types
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WEBHOOK_HOST = os.getenv("RENDER_EXTERNAL_URL", "https://gpt-agent-emii.onrender.com")  # Render добавляет эту переменную
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

openai.api_key = OPENAI_API_KEY
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Сессии пользователей (память контекста)
user_sessions = {}

@dp.message()
async def handle_message(message: types.Message):
    user_id = str(message.from_user.id)
    text = message.text.strip()

    if user_id not in user_sessions:
        user_sessions[user_id] = [
            {"role": "system", "content": (
                "Ты — корпоративный помощник компании Билдэко. "
                "Отвечай строго по внутренним регламентам, процессам и документам компании."
            )}
        ]

    user_sessions[user_id].append({"role": "user", "content": text})

    try:
        completion = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=user_sessions[user_id],
            temperature=0.2,
        )
        reply = completion.choices[0].message["content"]
        user_sessions[user_id].append({"role": "assistant", "content": reply})
    except Exception as e:
        reply = f"⚠️ Ошибка OpenAI: {e}"

    await message.answer(reply)


async def on_startup(app):
    await bot.set_webhook(WEBHOOK_URL)
    print(f"✅ Webhook установлен: {WEBHOOK_URL}")


async def on_shutdown(app):
    await bot.delete_webhook()
    print("🛑 Webhook удалён.")


def main():
    app = web.Application()
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    web.run_app(app, host="0.0.0.0", port=int(os.getenv("PORT", 10000)))


if __name__ == "__main__":
    main()
